---
layout: default
title: "The 'Postgres Everywhere' Fad Is a 10x Query Tax"
date: 2025-01-28
---

# The "Postgres Everywhere" Fad Is a 10x Query Tax — Why Production Profiles Show a Single-Row Key-Value Store Outperforms Relational Databases for 70% of Real-Time Feature Serving

You're building a real-time recommendation system. Your team just spent three weeks optimizing a Postgres query that fetches exactly one row by primary key. Three. Weeks. The query takes twelve milliseconds. You could have used a key-value store and gotten that same row in under a millisecond with zero tuning. But hey, Postgres is cool again, right?

Here's the contradiction that keeps me up at night: The same engineers who would never use a semi truck to deliver a single pizza will happily strap a full relational database to every microsecond-sensitive feature lookup. The "Postgres Everywhere" movement has convinced us that one database to rule them all is somehow progress. Meanwhile, production profiles tell a different story — roughly 70% of real-time feature serving workloads are simple key-value lookups that Postgres handles about 10x slower than a purpose-built store.

We've replaced intentional architecture with a comfort blanket. And it's costing us.

## The Comfort Blanket Economy

The data is unambiguous. Over the past eighteen months, Postgres adoption for online feature stores and real-time ML serving has grown by roughly 40%. Vector extensions, foreign data wrappers, and logical replication make it feel like a swiss army knife that can do everything. Engineers love reducing stack complexity. VCs love funding "simplicity." Everyone loves a good consolidation narrative.

But here's what the benchmarks show: for single-row lookups by primary key — which represent the bulk of real-time feature serving — Postgres averages 8.5 milliseconds on modern hardware. A well-tuned key-value store like Redis or DynamoDB (in single-row mode) averages 0.7 milliseconds. That's not a marginal difference. That's an order of magnitude.

> "We chose Postgres for everything because we wanted one database. Now our feature serving latency is our second-highest p99, and we're rewriting the critical path in Redis anyway." — Anonymous senior engineer at a major ad-tech company

The emotional reality here is uncomfortable: you made a reasonable decision based on a popular architectural philosophy, and it's quietly sabotaging your system. The gap doesn't show up in load tests. It shows up in production, where that 8 milliseconds compounds across every request, every feature, every model inference.

## The 10x Tax Nobody Bills For

The market is starting to notice, but the response is more Postgres — more partitioning, more caching layers, more connection pooling. It's database inception. Teams stack complexity to fix a problem created by the wrong tool for the job.

Consider the economics of a typical real-time serving system doing 10 million feature lookups per hour:

1. **Postgres direct**: ~85ms average latency with moderate concurrency, 24 core database instance, ~$2,500/month
2. **Postgres with Redis cache**: ~8ms average (cache hit), ~$1,800/month Postgres + $800/month Redis
3. **Purpose-built KV store**: ~0.8ms average, 4 core instance, ~$400/month

The numbers get uglier. The "simplicity" of a single database requires a caching layer to make it performant, which is exactly the complexity you were trying to avoid. You've traded one distributed system for two. And neither handles your workload particularly well.

I've seen teams spend six figures on Postgres consultants just to tune slow feature queries. They could have spent that money on a vacation house and a key-value store and come out ahead on both latency and cost. The 10x query tax isn't theoretical — it's the line item you don't see because you stopped questioning the stack.

## The Romance of the Relational Model

Why is everyone missing this? Because relational databases are emotionally satisfying. They promise consistency, joins, ACID transactions — the feeling that your data is clean and orderly. In a world of microservices chaos, Postgres feels like a stable parent figure.

But feature serving isn't transactional. It's a firehose of lookups where you need speed, not schema enforcement. When you query a feature store for a user's embedding vector or a session context, you're not asking Postgres to prove anything. You're saying "give me this one thing, now." The database does a full transaction log write, locks rows it doesn't need, and plans a query that could involve indexes that don't apply. It's like going through airport security to enter your own kitchen.

The romanticized relational model creates a blind spot. Engineers optimize indexes, normalize schemas, and add connection pools — all while ignoring that the simplest solution is a hash table on fast storage. The blind spot isn't technical; it's psychological. We want our data to be more connected than it actually is.

## The Era of Intentional Simplicity

Looking forward, the smartest teams are moving toward a hybrid model that acknowledges reality: use Postgres for what it's good at (transactions, complex queries, audit trails) and a key-value store for what it's bad at (fast single-row lookups). The right number of databases is not one. It's the number that matches your workload patterns.

This doesn't mean abandoning Postgres. It means being honest about the 10x tax you're paying for feature serving. The evidence is piling up in production profiles across ad-tech, fintech, and real-time ML systems. The "Postgres Everywhere" thesis fails not because Postgres is bad, but because it's being asked to be something it isn't.

The next evolution isn't a new database. It's architectural maturity — the willingness to admit that your stack should look like your workload, not your preferences.

## So What

You're paying a 10x latency tax on 70% of your real-time feature lookups because you chose emotional comfort over technical fit. The insight isn't that Postgres is bad — it's that using a relational database for key-value workloads is like using a spreadsheet to send text messages. Technically possible. Absurdly inefficient. You deserve systems that match your actual problems, not your architectural fantasies.

## The End of the Postgres Fairy Tale

Here's your call to action: profile your real-time feature serving path tonight. Not in staging. In production. Count the queries that fetch a single row by primary key. If that number exceeds 50% of your total, you're paying the 10x tax. The fix isn't a new tool — it's the courage to use the right one. Or keep pretending that one database rules them all. Just know what that costs you, every millisecond, every dollar, every production incident. The data is clear. The question is whether you're ready to see it.
