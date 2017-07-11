import contextlib
import sqlite3
import timeit

#import wpull.pipeline.item
import item

#import archivebot.wpull.ignoracle
import ignoracle
import ignoracle_new


# tail -n+4 ArchiveBot/db/ignore_patterns/global.json | head -n-3 | sed 's/^\s*"//; s/",\?\s*$//; s/\\"/"/g; s/\\\\/\\/g' | sed "s/'/\\\\'/g; s/^/r'/; s/$/',/; s/^/\t/"
globalIgnoreSet = [
	r'%25252525',
	r'/App_Themes/.+/App_Themes/',
	r'/bxSlider/.+/bxSlider/',
	r'/bxSlider/bxSlider/',
	r'/slides/slides/.+/slides/',
	r'/slides/.+/slides/slides/',
	r'/slides/slides/slides/',
	r'/js/js/.+/js/',
	r'/js/.+/js/js/',
	r'/js/js/js/',
	r'/css/css/.+/css/',
	r'/css/.+/css/css/',
	r'/css/css/css/',
	r'/styles/styles/.+/styles/',
	r'/styles/.+/styles/styles/',
	r'/styles/styles/styles/',
	r'/scripts/scripts/.+/scripts/',
	r'/scripts/.+/scripts/scripts/',
	r'/scripts/scripts/scripts/',
	r'/images/images/.+/images/',
	r'/images/.+/images/images/',
	r'/images/images/images/',
	r'/img/img/.+/img/',
	r'/img/.+/img/img/',
	r'/img/img/img/',
	r'/clientscript/clientscript/.+/clientscript/',
	r'/clientscript/.+/clientscript/clientscript/',
	r'/clientscript/clientscript/clientscript/',
	r'/lib/exe/.*lib[-_]exe[-_]lib[-_]exe[-_]',
	r'/(%5C)+(%22|%27)',
	r'/%5C/%5C/',
	r'/%27\+[^/]+\+%27',
	r'/%22\+[^/]+\+%22',
	r'/%27%20\+[^/]+\+%20%27',
	r'/%22%20\+[^/]+\+%20%22',
	r'/\\+(%22|%27)',
	r'/\\+["\']',
	r'/\\/\\/',
	r'/\'\+[^/]+\+\'',
	r'^https?://localhost(:\d+)?/',
	r'^https?://(127|10)\.\d+\.\d+\.\d+(:\d+)?/',
	r'^https?://172\.(1[6-9]|2\d|3[01])\.\d+\.\d+(:\d+)?/',
	r'^https?://192\.168\.\d+\.\d+(:\d+)?/',
	r'^https?://www\.google\.com/recaptcha/api',
	r'^https?://geo\.yahoo\.com/b\?',
	r'^https?://((s-)?static\.ak\.fbcdn\.net|(connect\.|www\.)?facebook\.com)/connect\.php/js/.*rsrc\.php',
	r'^https?://www\.flickr\.com/change_language\.gne',
	r'^https?://((www|web|web-beta|wayback)\.)?archive\.org/',
	r'^https?://archive\.is/',
	r'^https?://www\.google\.((com|ad|ae|al|am|as|at|az|ba|be|bf|bg|bi|bj|bs|bt|by|ca|cd|cf|cg|ch|ci|cl|cm|cn|cv|cz|de|dj|dk|dm|dz|ee|es|fi|fm|fr|ga|ge|gg|gl|gm|gp|gr|gy|hn|hr|ht|hu|ie|im|iq|is|it|je|jo|ki|kg|kz|la|li|lk|lt|lu|lv|md|me|mg|mk|ml|mn|ms|mu|mv|mw|ne|nl|no|nr|nu|pl|pn|ps|pt|ro|ru|rw|sc|se|sh|si|sk|sn|so|sm|sr|st|td|tg|tk|tl|tm|tn|to|tt|vg|vu|ws|rs|cat)|(com\.(af|ag|ai|ar|au|bd|bh|bn|bo|br|bz|co|cu|cy|do|ec|eg|et|fj|gh|gi|gt|hk|jm|kh|kw|lb|ly|mm|mt|mx|my|na|nf|ng|ni|np|om|pa|pe|pg|ph|pk|pr|py|qa|sa|sb|sg|sl|sv|tj|tr|tw|ua|uy|vc|vn))|(co\.(ao|bw|ck|cr|id|il|in|jp|ke|kr|ls|ma|mz|nz|th|tz|ug|uk|uz|ve|vi|za|zm|zw)))/finance\?noIL=1&q=[^&]+&ei=',
	r'^https?://upload\.wikimedia\.org/wikipedia/[^/]+/thumb/',
	r'^http://b\.scorecardresearch\.com/',
	r'^http://i\.dev\.cdn\.turner\.com/',
	r'^https?://video-subtitle\.tedcdn\.com/',
	r'^https?://download\.ted\.com/',
	r'^http://msft\.digitalrivercontent\.net/win/.+\.iso',
	r'^https?://tmz\.vo\.llnwd\.net/',
	r'^https?://(www\.)?megaupload\.com/',
	r'^https?://(www\.)?filesonic\.com/',
	r'^https?://(www\.)?wupload\.com/',
	r'^https?://prod-preview\.wired\.com/',
	r'^http://([^\./]+\.)?stream\.publicradio\.org/',
	r'^http://icecast\.streaming\.castor\.nl/',
	r'^http://wm1\.streaming\.castor\.nl:8000/',
	r'^http://icecast\.databoss\.nl:8000/',
	r'^http://stream\.rynothebearded\.com:8000/',
	r'^http://mp3\.live\.tv-radio\.com/',
	r'^http://av\.rasset\.ie/av/live/',
	r'^http://gcnplayer\.gcnlive\.com/.+',
	r'^http://streaming\.radionomy\.com/',
	r'^http://mp3\.ffh\.de/',
	r'^http://(www\.)?theradio\.cc\:8000/',
	r'^http://(audio\d?|nfw)\.video\.ria\.ru/',
	r'^http://eu1\.fastcast4u\.com:3048/',
	r'^http://[^\./]+\.radioscoop\.(com|net):\d+/',
	r'^http://[^\./]+\.streamchan\.org:\d+/',
	r'^http://[^/]*musicproxy\.s12\.de/',
	r'^http://stream\.rfi\.fr/',
	r'^http://striiming\d?\.trio\.ee/',
	r'^http://streamer\.radiocampus\.be(:\d+)?/',
	r'^http://relay\.broadcastify\.com/',
	r'^http://audio\d?\.radioreference\.com/',
	r'^http://[^/]+\.akadostream\.ru(:\d+)?/',
	r'^http://radio\.silver\.ru(:\d+)?/',
	r'^http://icecast\.szwoelf\.com:8000/',
	r'^http://altair\.micronick\.com:8080/\?action=stream',
	r'^http://94\.25\.53\.13[1-4]/.+\.mp3$',
	r'^http://server\.lradio\.ru:\d+/',
	r'^http://188\.93\.17\.201:8080/',
	r'^http://81\.19\.85\.19[56]/.+\.mp3$',
	r'^http://81\.19\.85\.203/.+\.mp3$',
	r'^http://play(\d+)?\.radio13\.ru:8000/',
	r'^http://stream(\d+)?\.media\.rambler\.ru/',
	r'^http://pub(\d+)?\.di\.fm/',
	r'^http://vostok\.fmtuner\.ru/',
	r'^http://109\.120\.141\.181:8000/',
	r'^http://195\.88\.63\.114:8000/',
	r'^http://radiosilver\.corbina\.net:8000/',
	r'^http://89\.251\.147\.100/',
	r'^http://bcs\d?\.fontanka\.fm:8000/',
	r'^http://stream2\.cnmns\.net/',
	r'^http://[^/]+\.streamtheworld\.com/',
	r'^http://[^/]+\.gaduradio\.pl/',
	r'^http://anka\.org:8080/',
	r'^http://radio\.visionotaku\.com:8000/',
	r'^http://stream\.r-a-d\.io/',
	r'^http://r-a-d\.io/.+\.mp3$',
	r'^http://95\.81\.155\.17/',
	r'^https?://icecast\.rtl2?\.fr/',
	r'^http://mp3tslg\.tdf-cdn\.com/',
	r'^http://[^/]+/anony/mjpg\.cgi$',
	r'^https?://air\.radiorecord\.ru(:\d+)?/',
	r'^https?://[^/]+\.rastream\.com(:\d+)?/',
	r'^https?://audiots\.scdn\.arkena\.com/',
	r'^https?://(www|draft)\.blogger\.com/(navbar\.g|post-edit\.g|delete-comment\.g|comment-iframe\.g|share-post\.g|email-post\.g|blog-this\.g|delete-backlink\.g|rearrange|blog_this\.pyra)\?',
	r'^https?://[^/]*tumblr\.com/(impixu\?|share(/link/?)?\?|reblog/)',
	r'^https?://plus\.google\.com/share\?',
	r'^https?://(apis|plusone)\.google\.com/_/\+1/',
	r'^https?://(ssl\.|www\.)?reddit\.com/(login\?dest=|submit\?|static/button/button)',
	r'^https?://digg\.com/submit\?',
	r'^https?://(www\.)?facebook\.com/(plugins/like(box)?\.php|sharer/sharer\.php|sharer?\.php|dialog/(feed|share))\?',
	r'^https?://www\.facebook\.com/captcha/',
	r'^https?://(www\.)?twitter\.com/(share\?|intent/((re)?tweet|favorite)|home/?\?status=|\?status=)',
	r'^https?://platform\d?\.twitter\.com/widgets/tweet_button.html\?',
	r'^https?://www\.newsvine\.com/_wine/save\?',
	r'^https?://www\.netvibes\.com/subscribe\.php\?',
	r'^https?://add\.my\.yahoo\.com/(rss|content)\?',
	r'^http://www\.addtoany\.com/(add_to/|share_save\?)',
	r'^https?://www\.addthis\.com/bookmark\.php\?',
	r'^https?://(www\.)?pinterest\.com/pin/create/',
	r'^https?://www\.linkedin\.com/(cws/share|shareArticle)\?',
	r'^https?://(www\.)?stumbleupon\.com/(submit\?|badge/embed/)',
	r'^https?://csp\.cyworld\.com/bi/bi_recommend_pop\.php\?',
	r'^https://share\.flipboard\.com/bookmarklet/popout\?',
	r'^https?://flattr.com/submit/auto\?',
	r'^https?://(www\.)?myspace\.com/Modules/PostTo/',
	r'^https?://www\.google\.com/bookmarks/mark\?',
	r'^http://myweb2\.search\.yahoo\.com/myresults/bookmarklet\?',
	r'^http://vuible\.com/pins-settings/',
	r'^https?://news\.ycombinator\.com/submitlink\?',
	r'^http://reporter\.es\.msn\.com/\?fn=contribute',
	r'^http://www\.blinklist\.com/index\.php\?Action=Blink/addblink\.php',
	r'^http://sphinn\.com/index\.php\?c=post&m=submit&',
	r'^http://posterous\.com/share\?',
	r'^http://del\.icio\.us/post\?',
	r'^https?://delicious\.com/(save|post)\?',
	r'^https?://(www\.)?friendfeed\.com/share\?',
	r'^https?://(www\.)?xing\.com/(app/user\?op=share|social_plugins/share\?)',
	r'^http://iwiw\.hu/pages/share/share\.jsp\?',
	r'^http://memori(\.qip)?\.ru/link/\?',
	r'^http://wow\.ya\.ru/posts_(add|share)_link\.xml\?',
	r'^https?://connect\.mail\.ru/share\?',
	r'^http://zakladki\.yandex\.ru/newlink\.xml\?',
	r'^https?://vkontakte\.ru/share\.php\?',
	r'^https?://www\.odnoklassniki\.ru/dk\?st\.cmd=addShare',
	r'^https?://www\.google\.com/(reader/link\?|buzz/post\?)',
	r'^https?://service\.weibo\.com/share/share\.php\?',
	r'^https?://(www\.)?technorati\.com/faves/?\?add=',
	r'^https?://bufferapp\.com/add\?',
	r'^https?://b\.hatena\.ne\.jp/add\?',
	r'^https?://api\.addthis\.com/',
	r'^https?://bookmark\.naver\.com/post\?',
	r'^https?://mail\.google\.com/mail/',
	r'^http://pixel\.blog\.hu/',
	r'^https?://pixel\.quantserve\.com/',
	r'^http://b\.scorecardresearch\.com/',
	r'^https?://(www|ssl)\.google-analytics\.com/(r/)?(__utm\.gif|collect\?)',
	r'^https?://p\.opt\.fimserve\.com/',
	r'^https?://(\d|www|secure)\.gravatar\.com/avatar/ad516503a11cd5ca435acc9bb6523536',
	r'^https?://imageshack\.com/lost$',
	r'^https?://[^/]+\.corp\.ne1\.yahoo\.com/',
	r'^https?://.+/js-agent\.newrelic\.com/nr-\d{3,3}(\.min)?\.js$',
	r'^https?://.+/stats\.g\.doubleclick\.net/dc\.js$',
	r'^https?://stats\.g\.doubleclick\.net/r/collect',
	r'^https?://ad\.doubleclick\.net/activity',
	r'^https?://.+/js/chartbeat\.js$',
	r'^http://www\.khaleejtimes\.com/.+/kt_.+/kt_',
	r'^http://www\.khaleejtimes\.com/.+/images/.+/images/',
	r'^http://www\.khaleejtimes\.com/.+/imgactv/.+/imgactv/',
	r'^http://photobucket\.com/.+/albums/.+/albums/',
	r'^https?://([^/]+\.)?gdcvault\.com(/.*/|/)(fonts(/.*/|/)fonts/|css(/.*/|/)css/|img(/.*/|/)img/)',
	r'^https://static\.licdn\.com/sc/p/com\.linkedin\.nux(:|%3A)nux-static-content(\+|%2B)[\d\.]+/f/',
	r'^https?://www\.flickr\.com/(explore/|photos/[^/]+/(sets/\d+/(page\d+/)?)?)\d+_[a-f0-9]+(_[a-z])?\.jpg$',
	r'^https?://static\.licdn\.com/sc/p/.+/f//',
	r'^http://www\.warnerbros\.com/\d+$',
	r'^https?://tm\.uol\.com\.br/h/.+/h/',
	r'^https?://media\.opb\.org/clips/embed/.+\.js$',
	r'^https?://[^.]+\.pinterest\.[^/]+/join/',
	r'\?wordfence_logHuman=1',
	r'^https?://[^/]*tumblr\.com/widgets/share/tool',
]

parentUrl = 'http://comicsalliance.com/'
simplePatterns = [r'trackback=fblike', r'/\?nav', r'/bar']
precisePatterns = [r'^https?://comicsalliance\.com/[^/]+/\?trackback=fblike$', r'^https?://comicsalliance\.com/.*/\?nav$', r'^https?://comicsalliance\.com/.*/bar$']
complexPatterns = [r'^https?://comicsalliance\.com/[^/]+/\?trackback=fblike($|.*(?!&foo=(?!baz)))', r'^https?://comicsalliance\.com/.*/\?nav$', r'^https?://comicsalliance\.com/.*/(?<!foobar)bar$', r'^https?://comicsalliance\.com/(.*/)?forumdisplay\.php\?(?!.*&daysprune=(?!-1))']

# Based on https://stackoverflow.com/q/15707056
@contextlib.contextmanager
def time_usage():
	startTime = timeit.default_timer()
	try:
		yield
	finally:
		endTime = timeit.default_timer()
		print("elapsed time: {:f}".format(endTime - startTime))


connection = sqlite3.connect('wpull.db')
cursor = connection.cursor()
cursor.execute('SELECT url FROM url_strings LIMIT 50000')
data = cursor.fetchall()

withGlobalSet = True
if withGlobalSet:
	data = data[0:5000]
else:
	data = data[0:50000]

for i in range(len(data)):
	record = item.URLRecord()
	record.parent_url = parentUrl
	record.url = data[i][0]
	data[i] = record

def test(oracle, patterns):
	if withGlobalSet:
		oracle.set_patterns(globalIgnoreSet + patterns)
	else:
		oracle.set_patterns(patterns)
	for i in range(10):
		with time_usage():
			for urlRecord in data:
				oracle.ignores(urlRecord) # We don't care about the result in this test

oracle = ignoracle.Ignoracle()

print('Warmup')
test(oracle, [])

print('Simple patterns')
test(oracle, simplePatterns)

print('Precise patterns')
test(oracle, precisePatterns)

print('Complex patterns')
test(oracle, complexPatterns)

newOracle = ignoracle_new.Ignoracle()

print('Simple patterns, new oracle')
test(newOracle, simplePatterns)

print('Precise patterns, new oracle')
test(newOracle, precisePatterns)

print('Extra complex patterns, new oracle')
test(newOracle, complexPatterns)
