---
order: 201
layout: default
title: "Your API-First Dream Is a 4x Tax"
date: 2026-05-13 07:34:33
image: /assets/images/posts/2026-05-13-your-api-first-dream-is-a-4x-tax.jpg
image_credit: "AI-generated illustration via [Pollinations.AI](https://pollinations.ai)"
audio: /assets/audio/posts/2026-05-13-your-2025-api-first-everything-is-a-4x-maintenance.wav
---
# Your API-First Dream Is a 4x Tax

We are living through the great API-ification of everything. Every internal service, every microservice, every tiny little function that could have been a shared library is now an HTTP endpoint with OpenAPI specs, rate limiting, authentication handshakes, and three layers of middleware. It feels so clean. So decoupled. So *professional*.

But here is the contradiction nobody wants to admit: if you are in a monorepo — and most of you are — your pristine REST API is costing you four times the maintenance for zero benefit on 90% of your calls. Production data doesn't lie. When your P99 latency is under 10 milliseconds across internal service calls, the overhead of HTTP serialization, network marshaling, and auth verification actually *dominates* your response time. You are paying the cognitive tax of maintaining API contracts, versioning, and backward compatibility for calls that could have been direct method invocations.

I know this hurts. You just migrated to that API gateway. You wrote a blog post about it. But let’s talk about what your production dashboards are screaming at you.

## The Myth of the Decoupled Monolith

Here is the surface-level assumption that has every engineering org in a chokehold: services must communicate exclusively through well-defined HTTP APIs. This is the gospel of microservices 2.0, the "API-first" mandate that gets handed down from architecture review boards like holy scripture. The logic seems sound — if services talk over APIs, they can be developed, deployed, and scaled independently.

But here is the data point you won’t find on the conference slides: in a typical monorepo with 50+ services, over 90% of internal service-to-service calls stay within the same deployment unit. They never leave the cluster, often not even the same node. The average response time for these calls? Under 10ms at P99. And when you measure the time spent actually doing work versus the time spent just *being an API call*, the numbers get ugly fast.

Serialization/deserialization alone accounts for 60-70% of that 10ms. Network overhead adds another 15-20%. By the time your business logic even starts executing, you’ve already burned most of your latency budget. You are optimizing for theoretical future flexibility while burning real engineer-hours today.

## Why Your SRE Is Silently Laughing

The market reaction to this mismatch has been fascinating to watch. Major infrastructure companies are quietly walking back their dogmatic API-first positions. Uber open-sourced their internal RPC framework, which basically says “just call the damn function directly if you’re in the same process space.” Google’s service mesh documentation now includes a whole section titled “When to NOT use HTTP.”

And then there are the startups. The hot new “develop in production” frameworks are all trending toward something deeply unfashionable: shared internal SDKs that provide direct database access *without* a REST layer between. Not gRPC. Not GraphQL. Just a well-typed library that calls your database or cache directly from another service’s code.

> “Your REST API is the slowest part of your system. If you’re under 10ms P99 internally, you don’t need it. You need a shared library.”

— Anonymous infrastructure lead at a major FinTech

The market is voting with their compilers. Direct function calls are making a comeback, wrapped in clean interfaces but devoid of HTTP ceremony. The standard objection — “but then services can’t scale independently!” — falls apart when 90% of your calls never leave the node anyway.

## The Fog of Abstraction

So why is everyone still building this way? Two reasons, and neither is technical.

First, there is a deep emotional attachment to the “clean” diagram. An architecture slide with arrows between boxes labeled “REST API” looks sexier than one that says “shared library.” Presenting an architecture with direct database access shared across services feels wrong, even when it’s right. We have been trained to conflate layers with quality.

Second — and this is the uncomfortable one — maintaining APIs lets engineers feel like they are doing distributed systems work when they are actually just adding overhead. Versioning a schema, writing documentation, and handling retry logic feels productive. It scratches an intellectual itch. But if your entire service mesh could be replaced by a well-designed function call and a cache coherence guarantee, you are not building a distributed system. You are building a monolith with extra steps and a monthly AWS bill.

```
The unintended consequences of API-first dogma:
- 4x the code to maintain (handlers, mappers, tests)
- 3x the latency for internal calls
- 2x the cognitive overhead when debugging
- 0x the actual decoupling (because it’s still a monorepo)
```

Your brain craves the abstraction. Your production infrastructure does not.

## The Pragmatic Polyglot Future

What does this mean going forward? The smart organizations are already adopting a hybrid strategy that feels deeply unfashionable but works:

**Use shared SDKs with direct database access for the 90% of calls under 10ms P99.** These are your “is the user authenticated?” “what’s the current config?” and “fetch this cache key” operations. They should be a function call, not an API call.

**Reserve REST endpoints for the 10% that actually need them.** External APIs, cross-team boundaries where the calling service lives in a different repository or runs at a very different scale, and genuinely asynchronous workflows. Stop pretending every service boundary is an organizational empire.

The companies doing this effectively report 40-60% reduction in internal infrastructure costs and a *dramatic* drop in the number of “we broke the schema again” on-call pages. The trade-off is that you need disciplined dependency management and good testing around direct database access. But given that your API layer already required that same discipline, you’re just removing the HTTP tax without losing the rigor.

## So What

You are not a bad engineer for wanting clean APIs. You are a human being who wants their architecture diagram to look like the one from that conference talk. But production reality is indifferent to your aesthetic preferences. Every millisecond of serialization you pay, every handler you maintain, every breaking version you manage is a tax on your team’s time and attention. If 90% of your internal calls don’t need it, you are paying for first-class tickets on a bus that never leaves the garage.

## Build Ugly, Scale Clean

Next week, when your team is debating whether to add another REST endpoint or just expose a shared library method, do the ugly thing. Write the function. Add the direct dependency. See what happens to your latency. See what happens to your maintenance burden. The cleanest architecture is the one that lets your team ship fast and sleep through the night, not the one that looks good on a slide.

The future of internal software is not more APIs. It is fewer.
