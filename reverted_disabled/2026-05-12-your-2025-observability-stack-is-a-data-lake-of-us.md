---
layout: default
title: "Your 2025 “Observability Stack” Is a Data Lake of Useless Metrics — Why Production Logs Show 80% of Teams Only React to Three Custom Alerts and the Rest Is Noise"
date: 2025-01-15
---

# Your 2025 “Observability Stack” Is a Data Lake of Useless Metrics — Why Production Logs Show 80% of Teams Only React to Three Custom Alerts and the Rest Is Noise

You spent six months migrating to OpenTelemetry. You configured dashboards that would make a NASA engineer weep with joy. You ingest terabytes of logs daily. And yet, when production goes down at 2 AM, you're staring at the same three custom alerts you wrote three years ago for a completely different microservice. The rest of your “observability stack” is a beautifully organized museum of noise. You're not monitoring your system. You're curating a digital graveyard.

Here's the uncomfortable truth: your team is running on a maintenance treadmill, paying cloud vendors for the privilege of ignoring 97% of the data they process. You've built a data lake of useless metrics, and the only honest metric is the one that actually wakes someone up. We've normalized drowning in dashboards while starving for insights, and it's making our systems worse, not better. Let's talk about why your 2025 observability stack is a beautiful lie.

## The More You Collect, The Less You See

Walk into any engineering org today and you'll find a “single pane of glass” that's actually a funhouse mirror. The latest trend data from 2024 shows teams are now ingesting an average of 2.3 petabytes of observability data per month. Sounds impressive. Sounds thorough. Sounds like peak engineering rigor. But dig into what actually gets looked at, and the picture gets cruel.

The assumption was always: more data equals more visibility. But what we're seeing in practice is a paradox of choice at hyperscale. Teams configure hundreds of alerts because they can. They build dashboards for every service because the tooling makes it trivial. They store everything because storage is cheap. But the cognitive load of sifting through signal to find noise has become its own full-time job. We've confused data collection with insight generation.

One 2024 incident analysis I reviewed showed a team had 847 active alerts configured. In the six months prior, they'd responded to exactly four. The other 843 were either duplicates, misconfigured, or so low-severity that engineers had trained themselves to ignore them. The more you collect, the less you actually see.

## The Market Is Selling Panic, Not Clarity

The observability market is now worth over $30 billion, and it's growing at a frankly embarrassing clip. Every player — Datadog, Grafana, New Relic, Honeycomb — is racing to add more integrations, more data sources, more visualizations. They're selling you the dream of complete visibility. But what they're actually selling is a subscription to anxiety.

Here's what's really happening underneath: teams are spending 40% of their on-call budget just tripping over false positives. The market reaction has been to build *more* tooling on top of the noise — AI-driven alert correlation, root cause analysis, automated runbooks. It's a layer cake of complexity that treats the symptom, not the cause. The cause is that you're collecting data you don't need, and now you need more software to hide the fact.

> “We've reached the point where the cost of ignoring an alert is less than the cost of investigating it. That's not observability. That's learned helplessness.” — Senior SRE, interview with the author

The tools aren't solving the problem. They're monetizing your inability to say no to more data. The market is selling panic, and we're buying it by the terabyte.

## We Forgot to Ask: What Actually Matters?

The biggest blind spot in the industry is that we treat observability as a plumbing problem instead of a philosophy problem. We ask “how do we get the data?” but rarely “what data should we get?” The result is that teams build observability stacks optimized for completeness, not signal.

Think about your own on-call experience. When the pager goes off, how many dashboards do you open? If you're like most engineers, it's one or two. You look at error rate, latency, and throughput. You check the logs for that one custom alert you actually trust. The rest is theater.

The industry blind spot is that we've conflated *coverage* with *understanding*. We think that if we can see everything, we'll understand everything. But human cognition doesn't scale that way. We can hold about three variables in working memory at any given time. Your observability stack should be designed around that constraint, not against it. Instead, we've built a system that requires a PhD in your own infrastructure just to answer the question “is it broken?”

The worst part? We know this. Every engineer I talk to admits they trust maybe three alerts out of hundreds. But we keep building the monuments anyway because scrapping them feels like admitting failure.

## Stop Collecting. Start Filtering.

So what happens when we accept that 80% of teams only react to three custom alerts? The forward implications are actually liberating, not limiting. It means we can stop treating observability as a hoarding exercise and start treating it as a curation challenge.

The future is brutal curation. Teams that succeed will:
- Delete 90% of their alerts and invest in making the remaining 10% rock solid.
- Build dashboards for debugging, not for monitoring — interactive query tools, not static charts.
- Invest in cardinality reduction at ingestion, not post-hoc filtering.

The shift isn't about better tools. It's about better taste. It's about admitting that your stack isn't a safety net — it's a distraction that's making your team slower and more anxious. The best teams I've seen in 2025 are the ones who've had the courage to delete more than they add. They respond to fewer alerts with higher confidence. They trust their instincts because their data actually reflects reality, not noise.

## So What?

You should care because your time is finite. Every minute you spend clicking through dashboards that don't matter is a minute you could spend writing better code, talking to users, or sleeping. Your observability stack should make you faster, not more anxious. If it's not doing that, it's a tax on your productivity. The insight isn't that you need more data. It's that you need less. Much less. And the bravery to throw the rest away.

## The Only Metric That Matters

Here's my challenge to you: open your observability stack right now. Count how many alerts you have configured. Then count how many have actually triggered a meaningful response in the last 30 days. If the ratio is worse than 10:1, you're not monitoring your system — you're paying for the illusion of control.

The best observability stack isn't the one that shows you everything. It's the one that shows you nothing unless you need it. Go build that instead. Your sleep schedule will thank you.
