import asyncio
import collections
import datetime
import io
import os
import sys
import websockets
import websockets.framing


DEBUG = 'WSDEBUG' in os.environ and os.environ['WSDEBUG'] == '1'


# Taken from qwarc.utils
PAGESIZE = os.sysconf('SC_PAGE_SIZE')
def get_rss():
	with open('/proc/self/statm', 'r') as fp:
		return int(fp.readline().split()[1]) * PAGESIZE


async def stdin(loop):
	reader = asyncio.StreamReader(limit = 2 ** 20) # 1 MiB buffer limit
	reader_protocol = asyncio.StreamReaderProtocol(reader)
	await loop.connect_read_pipe(lambda: reader_protocol, sys.stdin)
	return reader


async def stdin_to_amplifier(amplifier, loop):
	reader = await stdin(loop)
	while True:
		amplifier.send((await reader.readline()).decode('utf-8').strip())


class MessageAmplifier:
	def __init__(self):
		self.queues = {}  # websocket -> queue
		self.extensionsMap = collections.defaultdict(list)  # tuple of extensions -> websockets

	def register(self, websocket):
		q = asyncio.Queue(maxsize = 1000)
		extensions = tuple(websocket.extensions)
		self.queues[websocket] = q
		self.extensionsMap[extensions].append(q)
		return q

	def send(self, message):
		#FIXME This abuses internal API of websockets==7.0
		# Using the normal `websocket.send` reencodes and recompresses the message for every client.
		# So we construct the relevant Frame once instead and push that to the individual queues.
		frame = websockets.framing.Frame(fin = True, opcode = websockets.framing.OP_TEXT, data = message.encode('utf-8'))
		data = {}  # tuple of extensions → bytes
		for extensions in self.extensionsMap:
			output = io.BytesIO()
			frame.write(output.write, mask = False, extensions = list(extensions))
			data[extensions] = output.getvalue()

		for extensions in self.extensionsMap:
			for queue in self.extensionsMap[extensions]:
				try:
					queue.put_nowait(data[extensions])
				except asyncio.QueueFull:
					# Pop one, try again; it should be impossible for this to fail, so no try/except here.
					queue.get_nowait()
					queue.put_nowait(data[extensions])

	def unregister(self, websocket):
		q = self.queues[websocket]
		del self.queues[websocket]
		extensions = tuple(websocket.extensions)
		self.extensionsMap[extensions].remove(q)
		if not self.extensionsMap[extensions]:
			del self.extensionsMap[extensions]


async def websocket_server(amplifier, websocket, path, stats):
	queue = amplifier.register(websocket)
	try:
		while True:
			#FIXME See above; this is write_frame essentially
			data = await queue.get()
			await websocket.ensure_open()
			websocket.writer.write(data)
			stats['sent'] += len(data)
			if websocket.writer.transport is not None:
				if websocket.writer_is_closing():
					await asyncio.sleep(0)
			try:
				async with websocket._drain_lock:
					await websocket.writer.drain()
			except ConnectionError:
				websocket.fail_connection()
				await websocket.ensure_open()
	except websockets.exceptions.ConnectionClosed: # Silence connection closures
		pass
	finally:
		amplifier.unregister(websocket)


async def print_status(amplifier, stats):
	interval = 60
	previousUtime = None
	previousStats = {}
	while True:
		currentUtime = os.times().user
		cpu = (currentUtime - previousUtime) / interval * 100 if previousUtime is not None else float('nan')
		print(f'{datetime.datetime.now():%Y-%m-%d %H:%M:%S} - ' +
			', '.join([
				f'{len(amplifier.queues)} clients',
				f'{len(amplifier.extensionsMap)} extensions groups',
				f'{sum(q.qsize() for q in amplifier.queues.values())} total queue size',
				f'{cpu:.1f} % CPU',
				f'{get_rss()/1048576:.1f} MiB RSS',
				'throughput: ' + ', '.join(f'{(stats[k] - previousStats.get(k, 0))/1000:.1f} kB/s {k}' for k in stats),
			])
		)
		if DEBUG:
			for socket in amplifier.queues:
				print(f'  {socket.remote_address}: {amplifier.queues[socket].qsize()}')
			for extensions in amplifier.extensionsMap:
				print(f'  extensions: {extensions!r}')
		previousUtime = currentUtime
		previousStats.update(stats)
		await asyncio.sleep(interval)


def main():
	amplifier = MessageAmplifier()
	stats = {'sent': 0}
	# Compression is disabled because it would require a separate compression per client due to context takeover (cf. RFC 7692).
	start_server = websockets.serve(lambda websocket, path: websocket_server(amplifier, websocket, path, stats), None, 4568, compression = None)
	loop = asyncio.get_event_loop()
	loop.run_until_complete(start_server)
	loop.run_until_complete(asyncio.gather(stdin_to_amplifier(amplifier, loop), print_status(amplifier, stats)))


if __name__ == '__main__':
	main()
