---
layout: default
title: Your Serverless SQL Dream Is a 3x Tax
date: 2025-01-15
---

# Your Serverless SQL Dream Is a 3x Tax

You've been told serverless SQL is the future. "Just query everything with BigQuery—no servers, no ops, no limits." Sounds liberating. Feels like progress. But here's the dirty secret your cloud bill is screaming at 3 AM: for 90% of analytical workloads under 1TB, traditional PostgreSQL batches aren't just competitive—they're 3x cheaper. Not slightly. Not "with reservations." Three times the cost for the same query result. The same dashboard. The same business decision. The contradiction stings because we've been sold a vision of elastic, pay-per-query nirvana. The reality? A hidden tax on every click. Your production bill data doesn't lie. Let's walk through why your "serverless everything" strategy is quietly bleeding budget, and why good old PostgreSQL batches might be the contrarian play that actually makes sense.

## The 3x Myth of Elasticity

The pitch is seductive: "Pay only for what you query." No idle servers. No capacity planning. Just pure, elastic compute that scales to zero. In theory, it's the dream. In practice, it's a tax on discipline. When you run the same SQL in BigQuery versus a well-tuned PostgreSQL batch, the cost difference is stark. For queries scanning under 1TB—which is 90% of analytical workloads—BigQuery charges per byte processed. PostgreSQL charges for compute time. The twist? Most analytical queries are repetitive. Same joins. Same aggregations. Same window functions. BigQuery charges you for re-scanning the same data every time. PostgreSQL caches it. That 3x multiplier isn't theoretical—it's the delta between a query that costs $1.50 on Postgres and $4.50 on BigQuery. Every. Single. Time.

## The Repetition Tax You Didn't See

Here's where it gets ugly. The "serverless" model penalizes your most common pattern: repeated queries. A dashboard that refreshes hourly? BigQuery charges you fresh each time. PostgreSQL? The first query pays the I/O tax. The second reads from memory. The third is instant. This isn't a nuance—it's the core economic flaw. Serverless SQL assumes infinite, stateless elasticity is the ideal state. But 90% of analytical work is stateful. It's iterative. It's humans refining the same question against the same dataset. Every time you hit "run," serverless treats you like a first-time visitor. PostgreSQL treats you like a returning customer. The bill tells the story: repetitive workloads under 1TB see a 2-4x premium on serverless platforms. Not because they're faster (often they're not), but because the pricing model was designed for ad-hoc exploration, not production habits.

## The Blind Spot Everyone Shares

Why is everyone missing this? Two reasons. First, cloud vendors optimized for their own margin, not your workload. Serverless pricing is intentionally opaque—per-byte charges obscure the fact that repetitive queries are pure profit. Second, the industry fetishizes "modern" over "efficient." Admitting that PostgreSQL batches beat BigQuery for 90% of work feels like saying your flip phone is better than an iPhone for calls. It's technically true, but it's embarrassing. So we rationalize. "But BigQuery is serverless!" "But it scales!" "But it's Google!" Meanwhile, your finance team is asking why infrastructure costs grew 40% year-over-year while query volume barely budged. The blind spot is emotional: we'd rather pay 3x for a "modern" stack than admit the old tool was better optimized.

## The Contrarian Path Forward

This doesn't mean BigQuery is useless. It's unmatched for petabyte-scale explorations nobody repeats. But for your daily dashboards? Your weekly reports? Your ad-hoc queries under a terabyte? Go back to PostgreSQL batches. Seriously. Set up pg_cron. Materialize your views. Cache aggressively. The cost savings alone—often 60-70%—fund better monitoring, stronger backups, and a backup coffee budget. The forward path isn't "serverless everything." It's "right tool for the workload." For the 90% of analytical queries under 1TB, that tool is a relational database running batches, not a data warehouse charging per scan. Embrace the boring. Your budget will thank you.

**So what?** You're likely leaking thousands per month on serverless tax without realizing it. The insight isn't that serverless is bad—it's that the premium is unjustified for your most common queries. Check your bill. Look at the top 10 repeating queries. If they're under 1TB, you're overpaying.

**Conclusion:** The next time someone pitches "serverless SQL for everything," ask them one question: "What's my cost per query for repeated workloads?" The silence will be telling. Then go set up a PostgreSQL batch job, run the same query, and compare the bills. The numbers don't lie—and right now, they're saying 3x is too much for convenience you're not even fully using. The future isn't serverless. It's making the right cost/performance trade for the work you actually do.
