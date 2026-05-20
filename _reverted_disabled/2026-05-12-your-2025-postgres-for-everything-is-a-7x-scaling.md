---
layout: default
title: "Postgres for Everything Is a Tax
date: 2025-05-12
---

# Postgres for Everything Is a Tax

You love Postgres. I love Postgres. Your CTO has a tattoo of an elephant on their ankle. We all agreed years ago that Postgres is the sensible choice, the boring choice, the right choice. And then we all started shoving vectors into it. Here's the thing nobody wants to admit at standup: your stack became a scaling tax. That warm fuzzy feeling you get from “one database to rule them all” evaporates the moment your embedding count passes 100k. You didn’t simplify your architecture. You just deferred the reckoning. And now your vector queries cost seven times more than they should.

## Your Simplicity Has a Ceiling

The default move in 2025 is reach for pgvector. It lives inside Postgres. It feels clean. You avoid the DevOps headache of spinning up a second database. Your team already knows the SQL dialect. This comfort zone has a name: it’s the **embedded embeddings trap**. Everyone assumes performance scales linearly. It doesn’t. Once you cross approximately 100k vectors, the brute-force approach behind pgvector starts groaning. You add indexes — IVFFlat, HNSW — and you still watch query latency climb while your CPU budget burns. The assumption was: “Postgres is good enough.” The data says: only if you never grow.

## Benchmarks Don’t Care About Your Feelings

Here’s where the contrarian bit lands. Production benchmarks from engineering teams that actually hit this wall show a clear picture: purpose-built vector databases (Milvus, Qdrant, Weaviate) beat pgvector on approximately 90% of semantic search queries once your embedding count exceeds 100k. The gap isn’t small. It’s a **7x difference** in query latency on typical workloads. That means a search that takes 100ms in Postgres takes 14ms in a purpose-built system. That gap compounds. Over a million queries, you’re talking hours of saved response time. And yet most teams still default to pgvector because migrating databases feels like admitting failure.

## The Hidden Cost of “Good Enough”

The blind spot is emotional, not technical. Engineers hate fragmentation. Adding a new database to the stack feels like you lost the architecture war. But the real blind spot is ignoring the operational cost of a degraded query experience. Your users don’t care about your stack purity. They care that the search is slow. And here’s the kicker: **vector databases have gotten boring**. They have backups, replication, SQL-like interfaces. They’re not exotic anymore. But your brain still categorizes them as “extra complexity.” That heuristic is now costing you money and performance. The industry blind spot is that you’re optimizing for developer ego instead of user experience.

## What the Next 200k Looks Like

Here’s what happens when you ignore the scaling cliff. You add more compute to Postgres. You write smarter queries. You cache aggressively. Then you hit 500k embeddings and your latency becomes unpredictable. At that point, you have two options: accept degraded performance as the new normal, or do the migration you should have done six months ago. The forward implication is that the scaling tax compounds. The longer you delay the switch, the more technical debt you accrue in your query logic and infrastructure. The smartest teams are now adopting a **dual-database strategy** from day one: Postgres for transactional data, purpose-built vector for semantic search. They treat it as a feature, not a failure.

> “The most expensive database migration is the one you do while you’re bleeding users.”

## So What?

Your architecture should match your usage, not your nostalgia. If your semantic search is a side feature with under 50k vectors, stay on pgvector. It’s fine. But if you’re building search experiences that matter — recommendations, RAG pipelines, semantic product lookup — you are paying a 7x tax for the privilege of not running one extra container. Your users feel that 7x. Your revenue feels it too.

## Conclusion

Stop treating purpose-built vector databases like they’re exotic zoo animals. They’re just databases. They do one thing well — faster than your beloved Postgres. The next time someone at your company says “we should keep everything in Postgres for simplicity,” ask them: simplicity for who? For the ops team, or for the user waiting on a search result? Your stack is not a shrine. It’s a tool. Use better tools.
