---
title: "Percentiles are overrated"
date: 2020-10-28T16:47:57-07:00
draft: true
---

When running some code in production, we usually want to record metrics about it:

- what kind of tasks it is being asked to perform, and how much of each
- how long it takes our code to perform each type of task
- whether our code is successfully completing tasks
- how much CPU, memory, disk, network, etc. are used by our code

I'm most familiar with web services, where the tasks take the form of HTTP requests, but this also applies to other types of code.
For web services, we'll measure several things for each individual HTTP request, but storing and making sense of the raw data can be prohibitively expensive.
As a compromise, we usually summarize the data by 
bucketing it by category (endpoint) and time,
calculating one or more [summary statistics](https://en.wikipedia.org/wiki/Summary_statistics) on each bucket,
and storing the results in a time series database like [Prometheus](https://prometheus.io).

Popular summary statistics are the mean, standard deviation, count, and various percentiles.
For example, the most metrics library most commonly used at Yelp [emits](https://github.com/Yelp/uwsgi_metrics/blob/534966fd461ff711aecd1e3d4caaafdc23ac33f0/uwsgi_metrics/snapshot.py#L91):

- max
- mean
- min
- 50th, 75th, 95th, 98th, 99th, and 99.9th percentiles
- standard deviation

(Why do we only keep percentiles of 50% and above?
Because it costs money to store metrics, and we find more bang for our buck by making the slowest responses less slow, rather than making the fastest responses even faster.)

# You can't do math on percentiles

It's nice to be able to combine statistics together and have the results be meaningful.
If your service runs on multiple servers at once, you may want to record statistics for each machine individually, but then compute aggregate statistics of your whole cluster.
You may also want to compute aggregates for larger time windows than you initially used to record your data --
many timeseries databases will roll up small time windows into larger windows after a while, to save storage space.
(As time goes on, the value of high-precision data tends to drop.
You may need high-resolution data to diagnose a problem that happened today,
but three months later you probably only want general trends, to know if your performance is improving or getting worse.)


Let's say we have these statistics of response time for a web server, recorded at 5-minute intervals:

Time window   | count | mean  | max    | min   | p50   | p75   | p95   | p99
--------------|-------|-------|--------|-------|-------|-------|-------|--------
17:30 - 17:35 | 1000  | 240ms | 846ms  | 102ms | 201ms | 270ms | 304ms | 533ms
17:35 - 17:40 | 1200  | 283ms | 1003ms | 113ms | 225ms | 292ms | 373ms | 644ms

We want to roll up these two time windows into a larger 10-minute window, to save space in our time series database.
Several of these statistics are pretty trivial to aggregate:

 - The two `count`s can be added together.
 - `min` and `max` are associative -- that is, `min(min(list1), min(list2)) == min(list1 + list2)`
 - mean can be aggregated using a weighted average, using `count` as the weight.

```
    mean(list1 + list2) == sum(list1 + list2) / len(list1 + list2)
                        == (sum(list1) + sum(list2)) / (len(list1) + len(list2))
                        == (mean(list1) * len(list1) + mean(list2) * len(list2)) / (len(list1) + len(list2))
```

But how do we calculate the 95th percentile?
The best we can do is a range:
 - at least 50 requests took >= 304ms (5% of the first window)
 - at least 60 requests took >= 373ms (5% of the second window)
 - therefore at least 110 requests took >= 304ms
 - therefore the 95th percentile of the combined 10 minutes is at least 304ms
 - at least 950 requests took < 304ms (95% of the first window)
 - at least 1140 requests took < 373ms (95% of the second window)
 - therefore at least 2090 requests took < 373ms
 - therefore the 95th percentile of the combined 10 minutes is less than 373ms
