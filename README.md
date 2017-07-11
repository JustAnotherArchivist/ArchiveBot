This branch contains my code for testing the performance of ArchiveBot's ignoracle. Specifically, it tests whether the complexity of the regex patterns, ranging from very simple (literal matching, no regex features) to precise (basic regex features like anchors or quantifiers) to complex (e.g. lookarounds, alternations) makes a difference in performance, and whether caching the regexes between changes of `primary_{url,netloc}` can speed up the ignoracle.

# Code description
`ignoracle_stress.py` is the test code. It accesses a wpull 2.x database at `wpull.db`, which must have at least 50k entries in the `url_strings` table. There are a few variables that need changes if you want to run it with your own database: `parentUrl` is the main URL of the grab, and `simplePatterns`, `precisePatterns`, and `complexPatterns` are the patterns to be tested. Note that `ignoracle_stress.py` doesn't really care what the patterns are, and whether they match the right URLs; all results from the ignoracle are ignored (heh) completely. *This is purely a performance test.*

Since the number of ignore patterns can also make a large difference in performance, the variable `withGlobalSet` controls whether the global ignore set (`db/ignore_sets/global.json` on the main branch) should be included.

The number of URLs to be tested depends on whether the global ignore set is used or not and was tuned so the test takes a reasonable amount of time.

The script first runs a warmup round as my CPU reduces its frequency very quickly when it isn't at 100% load, yielding unusable timings at the beginning of the script. Then, it tests the simple, precise, and complex patterns first with the original Ignoracle and then with the new, caching one.

Several other files are included here for easy standalone tests:
* `ignoracle.py` is the file `pipeline/archivebot/wpull/ignoracle.py` from commit 412936b9.
* `ignoracle_new.py` is the same file from commit dea91b3f in this repository.
* `item.py` is wpull's `wpull/pipeline/item.py` from commit d0a9dffd.
* `url.py` is wpull's `wpull/url.py` from commit d0a9dffd.

The imports in these files had to be changed slightly:
* The `import wpull` plus `import wpull.pipeline.item` in `ignoracle{,_new}.py` was replaced by `import item`, and the references to `wpull.pipeline.item.URLRecord` adjusted accordingly.
* The `wpull.url` import in `item.py` was changed to just `url`.
* The two `wpull.*` imports in `url.py` were commented out.

# Results
## Summary
* The complexity of patterns is irrelevant in realistic cases unless you add dozens of patterns to a job. The global ignore set of about 190 patterns will dominate anyway.
* Caching does make a difference (factor 2 to 3). I suspect that this difference doesn't come from regex compilation though since there's also an internal cache of 512 patterns (on 3.x; 100 patterns in 2.7, so it might look different there). Instead, I think it's due to regex-escaping the `{primary_url}` and `{primary_netloc}` values and replacing the placeholders in the patterns on every call to `Ignoracle.ignores`. I didn't analyse that in detail though.

## Raw results
Without global ignore set (50000 URLs):
```
Simple patterns
elapsed time: 1.101192
elapsed time: 1.086952
elapsed time: 1.059913
elapsed time: 1.053293
elapsed time: 1.071061
elapsed time: 1.056186
elapsed time: 1.071129
elapsed time: 1.111269
elapsed time: 1.069778
elapsed time: 1.105170
Precise patterns
elapsed time: 1.340239
elapsed time: 1.318230
elapsed time: 1.364211
elapsed time: 1.281372
elapsed time: 1.267838
elapsed time: 1.281031
elapsed time: 1.277554
elapsed time: 1.294723
elapsed time: 1.284649
elapsed time: 1.267734
Complex patterns
elapsed time: 1.473686
elapsed time: 1.454509
elapsed time: 1.450073
elapsed time: 1.435549
elapsed time: 1.434815
elapsed time: 1.429190
elapsed time: 1.432913
elapsed time: 1.440867
elapsed time: 1.435085
elapsed time: 1.432234
Simple patterns, new oracle
elapsed time: 0.407096
elapsed time: 0.407673
elapsed time: 0.407076
elapsed time: 0.407129
elapsed time: 0.410769
elapsed time: 0.405775
elapsed time: 0.407888
elapsed time: 0.407620
elapsed time: 0.404661
elapsed time: 0.417438
Precise patterns, new oracle
elapsed time: 0.589039
elapsed time: 0.598275
elapsed time: 0.593245
elapsed time: 0.590316
elapsed time: 0.603195
elapsed time: 0.591455
elapsed time: 0.595139
elapsed time: 0.591094
elapsed time: 0.593979
elapsed time: 0.601731
Extra complex patterns, new oracle
elapsed time: 0.683729
elapsed time: 0.687341
elapsed time: 0.689319
elapsed time: 0.682893
elapsed time: 0.685734
elapsed time: 0.687261
elapsed time: 0.684153
elapsed time: 0.685237
elapsed time: 0.687343
elapsed time: 0.689383
```

With global ignore set (5000 URLs):
```
Simple patterns
elapsed time: 2.353562
elapsed time: 2.129584
elapsed time: 2.131379
elapsed time: 2.272788
elapsed time: 2.131848
elapsed time: 2.129182
elapsed time: 2.141497
elapsed time: 2.129557
Precise patterns
elapsed time: 2.140352
elapsed time: 2.141830
elapsed time: 2.136581
elapsed time: 2.346281
elapsed time: 2.161666
elapsed time: 2.145294
elapsed time: 2.231363
elapsed time: 2.244966
elapsed time: 2.149131
elapsed time: 2.137380
Complex patterns
elapsed time: 2.156054
elapsed time: 2.153815
elapsed time: 2.185925
elapsed time: 2.614645
elapsed time: 2.169718
elapsed time: 2.169002
elapsed time: 2.925880
elapsed time: 2.552235
elapsed time: 2.155310
elapsed time: 2.195167
Simple patterns, new oracle
elapsed time: 1.003834
elapsed time: 0.976398
elapsed time: 1.005326
elapsed time: 1.013589
elapsed time: 0.977967
elapsed time: 0.997788
elapsed time: 1.042963
elapsed time: 1.021872
elapsed time: 1.061999
elapsed time: 1.013419
Precise patterns, new oracle
elapsed time: 1.022805
elapsed time: 0.984942
elapsed time: 1.107668
elapsed time: 0.986480
elapsed time: 0.984979
elapsed time: 0.985674
elapsed time: 0.985390
elapsed time: 1.006061
elapsed time: 1.078945
elapsed time: 0.981485
Extra complex patterns, new oracle
elapsed time: 0.995742
elapsed time: 0.966456
elapsed time: 1.022613
elapsed time: 1.013296
elapsed time: 0.976889
elapsed time: 0.961355
elapsed time: 0.975976
elapsed time: 1.006548
elapsed time: 0.970501
elapsed time: 0.961612
```
