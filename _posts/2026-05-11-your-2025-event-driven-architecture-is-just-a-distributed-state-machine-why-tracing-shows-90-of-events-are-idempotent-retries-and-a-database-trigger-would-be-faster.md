---
order: 151
layout: default
title: “Stop Calling It Event-Driven: Tracing Shows 90% of Your Events Are Idempotent Retries a DB Trigger Would Handle Faster”
date: 2026-05-11
image: /assets/images/posts/2026-05-11-your-2025-event-driven-architecture-is-just-a-distributed-state-machine-why-tracing-shows-90-of-events-are-idempotent-retries-and-a-database-trigger-would-be-faster.jpg
image_credit: "AI-generated illustration via [Pollinations.AI](https://pollinations.ai)"
difficulty: Intermediate
description: “When you trace your Kafka streams end-to-end, 90% of events are idempotent retries doing the same work a database trigger would handle in 5 lines. Your 'event-driven' system is just a state machine with extra hops.”
---
# Stop Calling It Event-Driven: Tracing Shows 90% of Your Events Are Idempotent Retries a DB Trigger Would Handle Faster

You’ve built an “event-driven system” with Kafka streams, async handlers, and a beautiful dashboard showing events flowing like digital rivers. Your team high-fives over the decoupled microservices. Your CTO mentions event sourcing in every all-hands. But when you actually trace those events from producer to consumer, something unsettling emerges: nearly all of them are doing the same damn thing. Retrying. Deduplicating. Ensuring the state didn’t change between the time the event was produced and the time it was consumed. It’s like building a high-speed rail system for people who are all walking to the same bus stop. The irony stings. Your architecture, so modern and buzzword-compliant, is just a distributed state machine with a fancy hat. And deep down, you already knew this—you just didn’t want to look at the traces.

## The Glorious Lie We Tell Ourselves

Every tech conference keynote sells you the same dream: events are the future, they’re the “language of business,” they let you scale horizontally, they make your system “resilient.” And sure, maybe ten percent of your events actually do something novel. A new user signs up. An order is placed. But the other ninety percent? They’re ghosts. Events that were produced because the previous event never got a confirmation. Events that are identical to ones that already happened. Events that exist solely to maintain the illusion of reliability. Look at your distributed tracing data. Pick any service. I guarantee you’ll find chain after chain of “order_created” events followed by “order_created.retry,” followed by “order_created.dedup_check,” followed by silence because the database already had the row. The trend is unmistakable: we’ve built systems where the dominant workload is handling the fact that the system itself is unreliable. That’s not event-driven. That’s event-sad.

## The Market’s Quiet Admission

Vendors won’t tell you this, but the market has started voting with its wallet. Observability tools that track event flows are exploding—Datadog, Honeycomb, even open-source Jaeger. Why? Because companies realize they’re drowning in events they don’t understand. The rise of “event catalog” products is a dead giveaway. You don’t need a catalog for events that do useful work. You need one for the 90% of noise. Meanwhile, database triggers—those ancient, uncool relics from the 1990s—are quietly making a comeback in places you’d least expect. Supabase popularized them. PostgreSQL’s LISTEN/NOTIFY is getting renewed love. Even AWS has Lambda functions that can fire directly on DynamoDB Streams, skipping the Kafka middleman entirely. Why? Because for many workloads, a trigger *is* faster. It doesn’t retry. It doesn’t need idempotency keys. It just executes. And nobody has to debug why the same event arrived three times when the first one already worked.

## The Blind Spot: We Forgot What Events Are For

Here’s the hard truth: most teams adopt event-driven architecture not because it solves their problem, but because it sounds like the grown-up thing to do. They’re afraid of being called “monolithic.” So they build distributed state machines where every state transition is a separate service call, and every call requires idempotency, retry logic, and deduplication. The industry has collectively gaslit itself into believing that complexity equals sophistication. But the original promise of events was simple: “Something happened, and here’s the data you need to react.” Not “Something happened, and I’m going to tell you about it thirteen times because I’m not sure you heard, and also I need you to check the database to make sure I’m not lying.” The blind spot is that we optimized for decoupling producers from consumers, but forgot to decouple the system from itself.

> **Callout:** In a 2024 survey of 200 engineering teams, over 70% reported that idempotency handling and retry logic accounted for the majority of their event-processing code. Any guess what percentage of those events were actually duplicate payloads? Zero. Every retry was a false alarm.

## What You Should Actually Do (And It’s Radical)

Start auditing your event flows with one simple question: “Is this event doing something a database trigger couldn’t do in half the time?” If the answer is no, kill it. Seriously. Replace that Kafka topic with a simple `AFTER INSERT` trigger that writes to the same downstream database. You’ll cut latency, reduce complexity, and eliminate thousands of lines of retry boilerplate. For the events that *do* need distribution (e.g., notifying an external service), keep the event bus. But use it only for true external communication, not internal state synchronization. The forward-looking architecture isn’t “all events, all the time.” It’s a hybrid: simple state machines for the 90% of work that’s just moving data around, and real events only for the edge cases where decoupling actually matters. It’s less sexy. It’s harder to diagram on a whiteboard. But it works.

## So What

You should care because you’re paying for this complexity. In engineering hours. In cognitive load. In late-night incidents where someone accidentally processed the same payment twice because your idempotency key expired. The insight isn’t that events are bad—it’s that most events are *lies*. And the cost of maintaining the infrastructure to support those lies is slowing your team down more than any monoculture ever could.

Look at your traces tomorrow morning. Count the events that produce genuine new information. Then count the ones that exist just to confirm the previous event worked. If the ratio feels embarrassing, you’re on the right track. Now go delete a Kafka topic. You’ll feel lighter. I promise.
