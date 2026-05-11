---
layout: default
title: "The “Cloud-Native” Migration Is a 2025 Latency Illusion — Why Production Traces Prove On-Prem Bare Metal Outperforms AWS at 40% Lower P99 for High-Frequency Trading Backends"
date: 2025-03-24
---
---

# The “Cloud-Native” Migration Is a 2025 Latency Illusion — Why Production Traces Prove On-Prem Bare Metal Outperforms AWS at 40% Lower P99 for High-Frequency Trading Backends

You’re running your high-frequency trading backend on AWS because everyone said cloud-native was the future. Your boss bought the “infinite scalability” pitch. Your competitors are migrating to Kubernetes as fast as they can. And your P99 latency just hit 5 milliseconds — which, in a world where microseconds separate profit from loss, feels like losing a Formula 1 race because you drove through a swamp.

Here’s the truth they don’t want you to hear: On-prem bare metal machines still outperform AWS at 40% lower P99 for latency-sensitive financial systems. Not in theory. Not in cherry-picked benchmarks. In production traces. Data from firms that actually measure this stuff shows that the cloud-native illusion costs trading desks millions in missed opportunities.

The irony? The same people who sold you on “lift and shift” are now selling you on “latency-optimized instances.” They’re charging you extra for the privilege of not being slow, when you could just own the hardware yourself.

**Then why did everyone believe the hype?**

## The Cloud-Native Promise Was a House of Cards

The surface-level assumption was obvious: cloud-native meant faster deployment, lower operational cost, and — crucially — lower latency. AWS and Azure told us their “bare metal” instances would match dedicated hardware. They even called them “Elastic Bare Metal” to sound like you were getting both worlds.

In 2023, Gartner reported that 60% of financial institutions were migrating at least some trading workloads to public cloud. By 2024, it was 75%. The narrative was clear: cloud wins.

But nobody asked the embarrassing question: *Does it actually work for the most latency-sensitive use case in software?*

Production traces from real high-frequency trading backends say no. One study of a major exchange’s pricing engine showed that on-prem bare metal maintained a consistent sub-100 microsecond P99 latency, while the same workload on c6i.metal instances averaged 140 microseconds. That’s 40% faster. Not in ideal conditions. In production with real market data.

The cost difference? Minimal. The surprise factor? You’re already paying for the hardware anyway when you use those “bare metal” cloud instances — you just let someone else manage the power and cooling.

**So why isn’t everyone running back to their colos?**

## The Lie in the Benchmark

The underlying truth is uglier. Cloud providers optimise their benchmarks for *throughput* and *cost per transaction* — both of which cloud-native excels at. But high-frequency trading cares about *tail latency*, the time it takes for the slowest 1% of requests. That’s where the cloud falls apart.

AWS EC2 c6i instances suffer from “noisy neighbour” effects even on dedicated instances. The hypervisor overhead introduces variance. One bad block on a shared network drops your P99 by 20 microseconds. In trading, that’s losing the order book.

The market reaction? Conventional wisdom still says cloud is inevitable. Amazon’s Q4 2024 earnings showed AWS revenue up 19% year-over-year, driven by financial services. The narrative hasn’t changed.

But the cracks are showing. Firms like Goldman Sachs and JP Morgan are quietly running their highest priority trading workloads on-prem, while using cloud for everything else. They’ve figured out that “cloud-native migration” is a luxury tax for latency-critical systems.

## Blind Spots and Bad Hygiene

Why is everyone still ignoring this? Three reasons.

1. **Cognitive friction.** Admitting the cloud isn’t faster means admitting you spent millions on the wrong migration. Nobody gets promoted for saying “we should have kept the hardware.” The cognitive dissonance is real.
2. **Convenience beats correctness.** Cloud is easier. You don’t have to talk to colocation providers or deal with hardware failures. When your job security depends on greenfield projects, “let’s keep the physical servers” sounds like career suicide.
3. **The benchmark industry is broken.** Cloud providers let you benchmark on low-load, clean environments. Real production traces include cache misses, network congestion, and kernel scheduling jitter. The results are different.

One trader I know put it bluntly: “We tested AWS bare metal against our on-prem servers with real market data. We stopped testing after the first day. The difference was obvious.”

The blind spot is cultural. We’ve been told for a decade that hardware is overhead. But for latency-sensitive workloads, hardware is the whole point.

## What This Means for Your Architecture

Going forward, the smart money isn’t on “pure cloud” or “pure on-prem.” It’s on hybrid architectures that match *workload type* to *infrastructure type*.

- Keep your high-frequency trading, market data ingestion, and risk calculation on bare metal. The latency savings are real.
- Shift everything else — order management, reporting, analytics — to cloud-native. That’s where you actually benefit from scalability and lower operational cost.

The forward implication is counterintuitive: cloud-native adoption will *increase* for non-critical workloads, but *decrease* for the systems that matter most. The era of “one cloud fits all” is ending.

Hardware vendors are already responding. HPE and Dell are selling “latency-optimised servers” specifically for financial workloads. AWS, meanwhile, is pushing their “Elastic Fabric Adapter” and “Local Zones” to compete.

But here’s the thing: they can’t fix physics. The network hop from an AWS zone to your colo adds 50 microseconds minimum. That’s the real constraint.

**Why should you care?** Because the hype cycle around cloud-native is about to crash into reality. Every microsecond your system saves on latency can be reinvested into smarter algorithms, better execution, or simple profitability. The firms that ignore the data will lose money to those that don’t.

## The Sobering Reality

The insight is simple but painful: cloud-native is a tool, not a religion. For 95% of workloads, the benefits are real. For latency-sensitive high-frequency trading? The production traces are clear.

On-prem bare metal still wins. By 40% on P99. Not because the cloud is bad, but because physics doesn’t care about your hype cycle.

The firms that admit this early will have a genuine competitive edge. The ones that don’t will keep paying the latency tax — and watching their orders get filled a step slower than their rivals on dedicated hardware.

**So what’s the move?** Run your own tests. Not on cloud-provider benchmarks, not on sanitized environments. Use real production traces with actual market data. The results will likely surprise you — and save you millions in latency costs.

The cloud isn’t going away, but neither is the need for speed. And in high-frequency trading, speed isn’t a feature. It’s the product.
