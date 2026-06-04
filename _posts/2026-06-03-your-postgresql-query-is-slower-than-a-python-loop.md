---
order: 382
layout: default
title: "Your PostgreSQL Query Is Slower Than a Python Loop"
date: 2026-06-03 19:25:31
image: /assets/images/posts/2026-06-03-your-postgresql-query-is-slower-than-a-python-loop.png
audio: /assets/audio/posts/2026-06-03-your-postgresql-query-is-slower-than-a-python-loop.wav
---
# Your PostgreSQL Query Is Slower Than a Python Loop

You've been lied to. Not maliciously—benevolently, with good intentions. The lie? That SQL abstractions will always make your data processing faster. 

I've seen teams spend three months optimizing PostgreSQL query plans, only to discover a 50-line Python loop processes their 2GB dataset in half the time. The database kernel experts will tell you this shouldn't happen. But it does. And it's not a bug—it's a feature. Or rather, a fundamental architectural limitation that most engineers don't understand.

Let's break down why your beautifully normalized database is secretly a performance tax.

<figure class="post-hero-image">
<img class="post-hero" src="/assets/images/posts/2026-06-03-your-postgresql-query-is-slower-than-a-python-loop.png" alt="Hero image for Your PostgreSQL Query Is Slower Than a Python Loop" loading="lazy">
</figure>

## The Misleading Allure of Set-Based Operations

Here's the surface-level assumption: "Database engines are written in C, so they must be faster than interpreted Python loops at everything." It sounds reasonable. C compiles to machine code. Python compiles to bytecode. How could the interpreted language possibly win?

But here's the juicy contradiction: a simple GROUP BY in PostgreSQL can be 6-10x slower than the equivalent pandas groupby operation on a 10GB dataset. Not in a microbenchmark I cooked up—in benchmarks published by the ClickHouse team showing columnar scans outperforming row-based PostgreSQL by 50x on analytics workloads.

The magic bullet? Vectorized execution engines. Instead of processing one row at a time (what databases call "tuple-at-a-time"), vectorized engines process arrays of data simultaneously. This isn't theoretical—it's the reason Snowflake and ClickHouse can process billions of rows per second while PostgreSQL chokes on millions.

## What's Actually Happening Under the Hood

Let me explain with an analogy first: processing data row-by-row is like reading a book one word at a time while looking up a dictionary definition for each word. A vectorized engine reads entire paragraphs—it can recognize patterns, skip irrelevant sections, and process complete thoughts in one go.

Technically, here's the difference:

```python
# Typical database query processing (tuple-at-a-time, like PostgreSQL's Volcano model)
SELECT SUM(price * quantity) FROM orders WHERE region = 'EMEA' AND date > '2024-01-01';

# Under the hood, PostgreSQL processes like this:
for each row in orders:
    if row.region == 'EMEA' and row.date > '2024-01-01':
        result += row.price * row.quantity
```

This is called the Volcano iterator model, and it's been the standard since the 1990s. Every row triggers a function call, a comparison, a branch—each with terrible CPU cache locality. Modern CPUs hate this. They want predictable memory access patterns and batched operations.

A vectorized engine does this instead:

```python
# Vectorized batch processing (like ClickHouse or DuckDB)
for batch in chunks(orders, batch_size=1024):
    region_mask = batch.region == 'EMEA'
    date_mask = batch.date > '2024-01-01'
    valid_rows = region_mask & date_mask
    batch_result = (batch.price[valid_rows] * batch.quantity[valid_rows]).sum()
    total += batch_result
```

Notice how we process 1024 rows with just 4 vectorized operations instead of 1024 function calls. The difference is dramatic. Google's benchmark team found that vectorized execution can achieve 10x throughput improvement on modern CPUs simply by reducing branch mispredictions and improving cache utilization.

> **Data callout:** DuckDB, a vectorized OLAP database, can filter and aggregate 256 million rows in under a second on a laptop. PostgreSQL takes over 30 seconds for the same workload. That's not optimization—that's a fundamentally different architecture.

## The Industry Blind Spot: Abstractions Are Comfortable Lies

Why does everyone keep missing this? Because SQL abstractions are incredibly comfortable. They promise portability across databases, decades of optimization research baked in, and a declarative model that should scale from a single server to a billion-row table.

But here's the hidden cost: each layer of abstraction adds interpretation overhead. PostgreSQL's query planner generates a tree of operators, each implemented via function pointers, evaluated with per-tuple dispatch overhead. The query executor spends 30-40% of CPU cycles just deciding *what to do next* rather than *doing the actual computation*.

This isn't a bug—it's an architectural trade-off. PostgreSQL prioritizes flexibility over raw throughput. It's designed for OLTP workloads where you're touching thousands of rows, not billions. The problem is we keep trying to use it for analytics workloads, and it keeps failing silently.

I've seen teams add SSDs, increase memory, and throw Redis caches at the problem, all while their Python scripts could process the data faster with a simple loop and a dict.

## What This Means Going Forward: The New Normal

The forward implications are uncomfortable. We're seeing a market bifurcation:

1. **Analytics-first databases (ClickHouse, DuckDB, Snowflake):** Vectorized execution, columnar storage, CPU-cache aware algorithms
2. **Traditional row stores (PostgreSQL, MySQL):** Row-based, tuple-at-a-time, optimized for transactional workloads

The worst thing you can do is be in the middle—using a row store for analytics, or using an analytics database for high-concurrency OLTP. Both will hurt.

Three concrete takeaways if you want to avoid this trap:

1. **Profile before you optimize.** Measure where your query time actually goes. If it's spent in executor dispatch rather than actual computation, vectorization will help.
2. **Know your access pattern.** Row-oriented databases optimize for fetching many columns from few rows. Columnar vectorized databases optimize for fetching few columns from many rows.
3. **Consider your data size.** The 100MB line: under 100MB, a Python loop is often faster. Above 100GB, vectorized engines start to shine dramatically.


Your PostgreSQL queries aren't slow because of bad indexing or missing JOIN optimizations. They're slow because the database was designed when CPUs ran at 50MHz and had a single core. Modern CPUs have multiple cores, wide SIMD units, and hierarchical caches. The Volcano model doesn't play nice with any of them.

If you're processing anything beyond transactional workloads, raw vectorized execution will almost certainly beat your SQL queries. The abstraction cost is real, it's measurable, and it's becoming the new performance tax that separates the fast from the slow.

## The Contrarian Conclusion

Stop worshiping SQL as the universal solution. It's a veneer over a decades-old execution model, and the cracks are showing. Next time your analytics query times out, don't add another index. Write a Python loop with vectorized operations. You'll be shocked at how fast it is.

But don't just take my word for it—benchmark your own workload. Take a 100MB CSV, import it into PostgreSQL, measure the query time. Then write a DuckDB or pandas script that does the same thing. The winner isn't determined by marketing hype or ecosystem popularity. The winner is determined by which model your CPU actually wants to run.

Your CPU has been screaming this at you for years. Maybe it's time to listen.