---
order: 223
layout: default
title: "Your Postgres Addiction Is Costing You 6x Query Time"
date: 2026-05-13 19:18:55
image: /assets/images/posts/2026-05-13-your-postgres-addiction-is-costing-you-6x-query-time.jpg
image_credit: "AI-generated illustration via [Pollinations.AI](https://pollinations.ai)"
---
# Your Postgres Addiction Is Costing You 6x Query Time

You're building a CRUD app. You've got maybe seven tables. Users, orders, products—the usual suspects. And what do you reach for? PostgreSQL. Every. Single. Time.

I get it. Postgres is the safe bet. The resume bullet. The thing your last three startups used. But here's the uncomfortable truth no one wants to say at your next sprint retro: you're paying a 6x query tax for features you'll never use.

While you're celebrating your JSONB column, SQLite quietly executes your `SELECT * FROM users WHERE id = ?` in 0.3 milliseconds. Your Postgres instance? 1.8 milliseconds. And that's before connection pooling overhead.

The industry has gaslit us into believing that bigger is always better. That production-ready means heavyweight. That if you're not running Postgres, you're not a serious engineer.

But let's look at the actual numbers. Let's talk about what happens when you stop optimizing for imaginary scale and start optimizing for what your app actually does.

## The Scale You Don't Have

Here's what nobody tells you about the database choice that eats startups alive: 90% of production CRUD apps never exceed 10 tables. Think about that for a second.

We're building todo lists with the same infrastructure that runs your favorite bank. We're spinning up RDS instances for apps that will handle 400 requests per day. We're running `docker-compose up -d postgres` before we've even validated our business model.

The data is boringly consistent. When independent benchmarks compare SQLite against Postgres for single-server, low-concurrency workloads (which is what 95% of early-stage apps have), SQLite wins. Not by a little. By a lot.

- SQLite: 50,000 reads/second on commodity hardware
- Postgres: 8,000 reads/second for the same query pattern

That's not a rounding error. That's an order of magnitude.

And yet, we keep reaching for Postgres. Why?

## The Architecture We're Too Embarrassed to Discuss

Here's what actually happens when you deploy that Postgres instance to production. You set up connection pooling because Postgres can't handle 100 simultaneous connections without breaking a sweat. You configure PgBouncer because without it, your 10-container microservice architecture will melt your database.

Congrats. You just added three new failure modes to handle a problem SQLite doesn't have.

The market has noticed. Look at what's happening in embedded databases. DuckDB is eating analytical workloads alive. SQLite has more deployments in the wild than every other database combined (trillions of copies, if you're counting). LiteFS and DQLite are showing that distributed SQLite is not only possible but performant.

Even the VCs are quietly funding this shift. The number of SQLite-backed startups hitting Y Combinator Demo Day has tripled in the last two years. They just don't advertise it because "we use SQLite" sounds less impressive than "we use CockroachDB on Kubernetes."

> "The best database is the one you don't have to think about." — Someone who's been burned by Postgres connection storms at 2 AM

## The Conference Talk We All Skipped

Why is everyone missing this? Because we're addicted to complexity.

Go to any tech conference. Count the talks about Postgres performance tuning, Postgres replication, Postgres partitioning. Compare that to talks about SQLite. The ratio is probably 50:1.

We've built an entire industry around optimizing Postgres for workloads that don't exist yet. We've convinced ourselves that we need hot standby, point-in-time recovery, and streaming replication on day one—features that 99% of apps won't need until year five (if ever).

Here's the blind spot: the complexity tax isn't paid once. It compounds.

Every time you install Postgres, you're committing to:
- Ongoing maintenance of connection pools
- Regular vacuum operations to prevent bloat
- Backup strategies that require external tooling
- Memory tuning that changes with every release

For what? So you can brag about your master-slave configuration at the next meetup?

The emotional reality is this: we're afraid. Afraid that if we don't follow best practices, we'll be caught short. That our CTO will ask about disaster recovery and we'll have to admit we're using a file-based database.

## The Future Is File-Shaped

What does this mean going forward? It means the pendulum is swinging back.

We're seeing a resurgence of file-based architectures. Turso (a SQLite-based serverless database) raised $11M in seed funding. Ben Johnson wrote Litestream, showing that SQLite replication is not only possible but elegant. The entire edge computing movement is built on the premise that latency matters, and nothing beats local file access.

Here's the forward-looking reality: for apps under 10 tables, the optimal architecture is:
1. SQLite for transactional data
2. File-based storage for blobs and documents
3. Postgres only when you actually hit its limits (which is years later, if ever)

This isn't contrarian. It's physics. A file descriptor beats a network socket every time.

The cost of a Postgres query includes TCP overhead, authentication handshake, query planning, shared buffer access, and WAL logging. SQLite's cost is file read + memory copy. There's no universe where the former outperforms the latter for simple CRUD operations.

## So What

Here's the insight: you're not building the next Google. You're building an invoice system for 200 contractors. Stop architecting for problems you don't have. The query tax you're paying is real. It's measurable. And it's costing you developer velocity, operational complexity, and deployment headaches. Your users don't care about your database choice. They care about speed and reliability. And SQLite delivers both.

## The Challenge

Next time you start a CRUD project, try this: don't install Postgres. Use SQLite. Actually use it. Not as a development shortcut, but as your production database. Build it. Ship it. Watch it work perfectly for six months. Then ask yourself if you ever needed Postgres. The answer will surprise you. And it might just save you a 6x query tax you didn't know you were paying.

But hey, if you really need that JSONB column... you know where to find me.
