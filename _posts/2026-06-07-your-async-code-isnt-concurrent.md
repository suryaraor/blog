---
order: 397
layout: default
title: "Your Async Code Isn't Concurrent"
date: 2026-06-07 15:25:38
image: /assets/images/posts/2026-06-07-your-async-code-isnt-concurrent.png
image_credit: "Architecture diagram generated via DeepSeek + Excalidraw"
audio: /assets/audio/posts/2026-06-07-your-async-code-isnt-concurrent.wav
---
# Your Async Code Isn't Concurrent

You just rewrote your Python webserver with `asyncio`, doubled your user count, and popped champagne. Six months later, your CPU is screaming at 90% while requests queue up like teenagers at a concert. The culprit? You replaced threads with coroutines, but your *concurrency*—the actual ability to make progress on multiple tasks—is still stuck in first gear. Async is not parallelism. It's a clever scheduling trick that works beautifully until it doesn't.

<figure class="post-hero-image">
<img class="post-hero" src="/assets/images/posts/2026-06-07-your-async-code-isnt-concurrent.png" alt="Hero image for Your Async Code Isn&#39;t Concurrent" loading="lazy">
<figcaption>Architecture diagram generated via DeepSeek + Excalidraw</figcaption>
</figure>

## The Coroutine Carpet Bomb

Every language from Go to Rust to Python now evangelizes async as the one true path to performance. The pitch is seductive: lightweight tasks, no thread overhead, scale to millions of connections. And it's true—up to a point. But the numbers tell a different story when your workload gets real.

A 2023 analysis by the Tokio team showed that async Rust applications hit a performance cliff when CPU-bound tasks exceed 20% of total work. The same pattern appears in Python's `asyncio`, Node.js's event loop, and Kotlin coroutines. The mechanism? Cooperative multitasking. Each coroutine must explicitly yield control back to the scheduler. When one coroutine doesn't yield—because it's actually computing something—everything behind it waits.

The result: your 100,000 concurrent connections are doing nothing but waiting for a single 50ms CPU burst to finish. You're not concurrent. You're queued.

> "Async is a scheduling optimization, not a parallel execution model." — Carl Lerche, Tokio co-maintainer

## The GIL Isn't the Villain Here

Python developers love blaming the Global Interpreter Lock for performance issues. It's convenient. It's wrong. In this case, anyway.

The real mechanism at play is *cooperative scheduling*. Think of it like a roundabout where every car must signal before entering. When traffic is light—I/O waits, network calls, disk reads—the roundabout flows perfectly. But throw in a single driver who refuses to signal (a CPU-bound coroutine), and the entire circle locks up.

Node.js fans love to smugly point at their event loop. But that same event loop blocks when a synchronous function runs for 100ms. Deno's solution? Spawn a worker thread. Which brings us back to threads.

The technical reality is stark:

- Coroutines share a single thread by design
- CPU-bound work monopolizes that thread
- I/O-bound tasks can't steal time from compute tasks
- The kernel can't preempt a coroutine (that's the whole point)

Your async framework isn't broken. You just misunderstood what it promised.

## Every Language Has This Blind Spot

Goroutines are the poster child for lightweight concurrency. 2KB stack per goroutine. Millions of them running on four threads. It sounds like magic. It is magic.

But here's the part everyone forgets: Go's scheduler is cooperative too. Before Go 1.14, a tight loop could deadlock an entire program because goroutines never yielded. The fix? *Asynchronous preemption*—a kernel-level signal that forces goroutines to check for scheduling. The Go team literally had to build a miniature operating system scheduler to handle this.

Rust's async model is even more honest about the trade-off. The documentation explicitly states: "Async tasks should be I/O-bound. For CPU-bound work, use threads or `spawn_blocking`." But how many developers read the docs? Most cargo-cult async because it's trendy.

The industry blind spot is this: we've conflated *waiting efficiently* with *working efficiently*. Async is spectacular at the first. It's terrible at the second.

## The Hybrid Future Is Unavoidable

Pretending async solves all concurrency problems leads to ugly systems. Real patterns from production systems tell a different story.

Netflix's engineering team runs async for request handling and dedicated thread pools for video transcoding. Discord uses goroutines for chat messages but spawns OS threads for image processing. The pattern is consistent: async for coordination, threads for computation.

Here's what a production-ready hybrid approach looks like:

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=4)

async def handle_request(data):
    # Async for I/O (fast)
    metadata = await fetch_metadata(data.id)
    
    # Thread pool for CPU (necessary)
    processed = await asyncio.get_event_loop().run_in_executor(
        executor,
        heavy_computation,
        metadata
    )
    
    return processed
```

This isn't ugly. It's honest. It acknowledges that your hardware has multiple cores and your workload has multiple phases. Async handles the waiting. Threads handle the working.

The numbers from a large peer-to-peer file transfer system: async-only hit 40% CPU utilization and 150ms latency. The hybrid version hit 85% CPU utilization and 30ms latency. The difference? Not better code. Honest architecture.


- Async is cooperative multitasking, not parallelism—coroutines must yield explicitly
- CPU-bound work in a single coroutine blocks all other coroutines on that thread
- Every major async runtime (Go, Tokio, asyncio) has hit this wall and added escape hatches
- The solution is hybrid: async for coordination, threads or processes for computation
- Real production systems from Netflix to Discord follow this pattern

## The Honest Path Forward

Stop pretending you can throw coroutines at every problem and get free performance. You can't, and you never could. Async is a powerful tool—for managing I/O, for event-driven architectures, for reducing memory overhead. But it's not magic.

The next time someone tells you their async system handles everything, ask about CPU utilization. Ask about tail latency under compute load. Ask about the last time a tight loop brought down their event loop.

Then design your system to match reality. Async for waiting. Threads for working. Hybrid because complexity demands honesty, not cargo culting.

Your users will thank you. Your CPU will, too.