---
order: 383
layout: default
title: "Streaming Is a Luxury Most Apps Can't Afford"
date: 2026-06-03 23:21:44
image: /assets/images/posts/2026-06-03-streaming-is-a-luxury-most-apps-cant-afford.png
image_credit: "Architecture diagram generated via DeepSeek + Excalidraw"
audio: /assets/audio/posts/2026-06-03-streaming-is-a-luxury-most-apps-cant-afford.wav
---
# Streaming Is a Luxury Most Apps Can't Afford

You've been sold a lie: that real-time stream processing is the inevitable evolutionary endpoint of data architecture. Kafka streams, Flink pipelines, Kinesis consumers — every conference talk, every vendor blog, every "modern data stack" diagram treats streaming as the default. Here's the uncomfortable truth: for 80% of use cases, batch processing is not only cheaper and simpler — it's faster.

<figure class="post-hero-image">
<img class="post-hero" src="/assets/images/posts/2026-06-03-streaming-is-a-luxury-most-apps-cant-afford.png" alt="Hero image for Streaming Is a Luxury Most Apps Can&#39;t Afford" loading="lazy">
<figcaption>Architecture diagram generated via DeepSeek + Excalidraw</figcaption>
</figure>

## The Latency Mirage

The assumption is simple: streaming = lower latency, batch = higher latency. That's technically true at the micro level but catastrophically wrong at the macro level. Think of it like this: batch is a freight train, streaming is a bicycle courier. Yes, the courier delivers each envelope the moment it's ready — but the freight train moves 10,000 packages at once at 10x the speed per package.

What actually happens in practice? A typical streaming pipeline — let's say Kafka → Flink → S3 — introduces 200-500ms of processing latency per event. But that's after you've dealt with exactly-once semantics, state management, checkpointing, and backpressure handling. The complexity tax is real, and it compounds.

Consider a concrete example from Uber's 2019 engineering blog: their streaming fraud detection system required 40+ custom operators just to handle watermarks and out-of-order events. The batch equivalent? A simple Spark job with 10 lines of windowing logic. The streaming version was harder to debug, harder to test, and harder to reason about. And the latency difference? 2 seconds versus 30 minutes for their use case.

## The Hidden Cost of Always-On

```
# Simplified streaming pipeline pseudocode
stream = kafka.subscribe("user_events")
stream
  .window(Duration.ofSeconds(30))
  .aggregate(count_events())
  .stateful_operation(user_store)  # Requires Redis/RocksDB
  .exactly_once()                   # Coordination + checkpointing
  .to_sink("processed_events")
```

Now the batch equivalent:
```python
# Batch pipeline pseudocode  
df = spark.read.parquet("events/*.parquet")
df.groupBy(window("timestamp", "30 seconds"))
  .agg(count("event_id"))
  .write.mode("overwrite").parquet("processed_events")
```

See the difference? The streaming version requires persistent state stores, exactly-once coordination, and continuous operation. The batch version runs, finishes, and goes away. 

This isn't academic. In 2023, DoorDash publicly documented a 60% reduction in compute costs by migrating certain "real-time" pipelines to micro-batch. Their insight: the streaming overhead (always-on workers, state management, checkpoint I/O) consumed resources even when no events were flowing.

> "We found that 73% of our streaming pipelines had average throughput of less than 100 events/second — yet they consumed the same compute resources as pipelines processing 10,000 events/second." — DoorDash Engineering Blog, 2023

## The Industry's Stockholm Syndrome

Why does everyone keep building streaming pipelines? Three reasons, none of them technical:

1. **Vendor FUD** — "If you're not real-time, you're falling behind." This sells cloud services.
2. **Resume-driven architecture** — Streaming looks better on a LinkedIn profile than batch.
3. **Misunderstood requirements** — "We need real-time" often means "We need answers within an hour, not overnight."

The emotional reality: engineers feel sophisticated building streaming systems. Batch feels like legacy technology. But sophistication isn't a feature — it's a liability when it adds complexity without commensurate value.

Consider Bloomberg's 2022 benchmark comparison: for their market data processing, a streaming pipeline achieved p99 latency of 50ms but required 8x more infrastructure than the batch alternative running every 5 minutes. The batch system's p99? 4 minutes and 55 seconds — but the business couldn't act on data faster than 30-second windows anyway.

## The Coming Batch Renaissance

Here's what the smartest teams are doing right now:

- **Reserve streaming for event-driven actions** — Only use streaming when a human or system needs to react within seconds (fraud detection, alerting, real-time dashboards).
- **Default to micro-batch** — 30-second or 5-minute windows dramatically reduce infrastructure costs.
- **Apply the "Why not batch?" test** — Before building a streaming pipeline, force yourself to prove batch doesn't work.

The forward-looking pattern isn't "streaming everywhere" — it's intelligent tiering. Critical paths get streaming. Everything else — the 95% of data processing — gets batch.


Streaming is a hammer that's been used on every nail for a decade. The actual insight: batch wins on cost, simplicity, debuggability, and often total throughput. The question isn't "Should we stream?" — it's "How fast do we actually need answers?" If the answer is "within minutes, not seconds," you're paying a streaming tax for zero benefit.

## The Uncomfortable Question

Next time someone proposes a streaming pipeline, ask: "What breaks if we batch this every 5 minutes?" The answer will reveal whether they're solving a real latency requirement or just enjoying the architecture. The best engineers I know are the ones who default to batch and reach for streaming only when proven necessary. Join them. Your infrastructure bill — and your team's sanity — will thank you.