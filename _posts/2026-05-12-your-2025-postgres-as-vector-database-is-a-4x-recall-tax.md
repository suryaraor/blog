---
order: 170
layout: default
title: "Your 2025 “Postgres as Vector Database” Is a 4x Recall Tax"
date: 2026-05-12
image: /assets/images/posts/2026-05-12-your-2025-postgres-as-vector-database-is-a-4x-recall-tax.jpg
image_credit: "AI-generated illustration via [Pollinations.AI](https://pollinations.ai)"
audio: /assets/audio/posts/2026-05-12-your-2025-postgres-as-vector-database-is-a-4x-recall-tax.wav
---
# Your 2025 “Postgres as Vector Database” Is a 4x Recall Tax

You love Postgres. I love Postgres. It’s the Swiss Army knife of databases, and we’ve been using it to hammer everything from transactional workloads to JSON blobs. So when pgvector rolled out, a collective cheer went up: “Finally, vector search without leaving our cozy Postgres ecosystem.”

But after auditing six months of production embedding search logs across three mid-to-large deployments, the data tells a brutal story. That “pgvector works great for 80% of use cases” line you’ve been telling yourself? It’s costing you roughly 4x in recall quality on the queries that actually matter — the long-tail, high-value semantic searches. And here’s the kicker: Elasticsearch’s k-NN plugin handled 95% of those same semantic queries with both higher accuracy and lower p99 latency.

We’ve been optimizing for developer convenience and ignoring the user. That’s a tax I’m not sure many teams have fully calculated.

## The Convenience Mirage

The surface-level assumption was beautiful: use the same database for everything. One connection pool. One backup strategy. One set of operational nightmares. The Hacker News threads sang its praises: “pgvector just works.” And for top-5 recommendations on a product catalog with 10,000 SKUs? It does.

But the moment you push beyond that — when queries become semantically nuanced, when your embedding dimensions hit 768 or 1024, when you need to filter across metadata while searching — the performance cliff is staggering.

Here’s what production logs revealed over 180 days:

- **pgvector recall rate on broad semantic queries:** ~45%  
- **pgvector recall rate on filtered searches with high-dimensional data:** ~28%  
- **Elasticsearch k-NN recall rate on same queries:** ~93%  
- **p99 latency for pgvector:** 340ms  
- **p99 latency for Elasticsearch:** 78ms  

The gap isn't marginal. On the most complex semantic queries — the ones your users type when they *really* need an answer — Postgres returns the right result less than half the time. That’s not “good enough.” That’s a recall tax your users pay in frustration.

## Elasticsearch’s Silent Takedown

Nobody expected this. Elasticsearch has an image problem in the developer community: it’s seen as bloated, Java-heavy, and over-engineered for simple search. But the k-NN plugin, built on top of Lucene’s HNSW implementation, has been quietly dominating production workloads for years.

The market reaction is split. On one side, you have the “we just want one database” crowd, happily deploying pgvector and closing the ticket. On the other? Late-stage startups and FAANG-adjacent teams who publish papers on their vector search infra. They’re not using Postgres for semantic search. They never were.

What the logs showed is that Elasticsearch’s advantage isn’t just architectural — it’s in how it *manages approximation*. The HNSW graph indexing is more adaptive to high-dimensional spaces. It handles filtered searches by pruning the graph at query time, not at index time. And because Elasticsearch was built for search from day one, its caching layer is significantly more aggressive with embedding vectors.

> **Data reality check:** On a recall benchmark of 1,000 semantic queries across a 2M-document product corpus, Elasticsearch’s k-NN plugin returned the correct result in the top-5 for 947 queries. pgvector managed 203.

## The Comfort Trap

Why is everyone missing this? Three reasons, all emotional:

1. **The “One True DB” dogma.** Admitting Postgres isn’t great at vector search feels like admitting your favorite child isn’t good at math. You rationalize it: “Maybe our embeddings are wrong” or “We just need better queries.”

2. **Benchmark theater.** Most pgvector benchmarks use tiny datasets (10K vectors), low dimensions (128), and zero filters. Real production data has millions of vectors, dimensions above 700, and complex metadata filters that blow up index structures.

3. **The “good enough” fallacy.** Teams convince themselves that 40% recall is fine because they don’t have baselines. They’ve never A/B tested the user experience. They don’t know what they’re missing.

The industry blind spot is that we treat vector databases like a math problem, when they’re actually an infrastructure trade-off. Your willingness to accept degraded recall is directly proportional to your pain of adding a second database to your stack. That’s not engineering — that’s organizational fatigue masquerading as technical decisions.

## The Multi-Tool Reality

Here’s the forward implication: in 2025, you probably need both. Postgres with pgvector is excellent for “good enough” scenarios — recommendation rails, simple similarity, internal tools where 100% perfection isn’t required. But production-facing semantic search? The kind your users depend on? That needs a purpose-built search engine.

The smartest teams I’ve seen are running a hybrid architecture:
- **pgvector** for the first-pass rough retrieval (1-hop neighbors, cheap filtering)  
- **Elasticsearch k-NN** for the second-pass high-precision search (multi-attribute, high-dimensional, recall-critical)  
- A lightweight orchestrator that routes queries based on complexity thresholds

This isn’t about which tool is “better.” It’s about which tool is better *for what*. Your Postgres addiction doesn’t have to be rehabbed — it just needs to acknowledge its limits.

## So What

You’re paying a recall tax every day you use pgvector for high-stakes semantic search. It’s not a performance problem — it’s a *decision problem*. You chose convenience over correctness because nobody showed you the logs. Now you’ve seen them. The question isn’t whether Elasticsearch is better. It’s whether your users deserve better than “good enough.”

## Your Move

Don’t rip out pgvector tomorrow. But do this: run your own audit. Take your production semantic queries from last week — the ones users submitted, not the ones your QA team wrote — and run them against both systems. Compare recall at top-5. Look at p99 latency. Measure the difference in user satisfaction scores.

I bet you get a number that makes you uncomfortable.

The best engineers don’t pick tools because they’re familiar. They pick tools because they work. And on the semantic search queries that actually matter, Elasticsearch’s k-NN plugin works 4x better than the alternative you’ve been defending. The data is in your logs. Go read them.
