---
order: 371
layout: default
title: "Why AI Workloads Are Fleeing Serverless for Bare Metal"
date: 2026-06-02 09:36:20
image: /assets/images/posts/2026-06-02-why-ai-workloads-are-fleeing-serverless-for-bare-metal.png
quality_score: 8.0
audio: /assets/audio/posts/2026-06-02-why-ai-workloads-are-fleeing-serverless-for-bare-metal.wav
---
# Why AI Workloads Are Fleeing Serverless for Bare Metal

**Published**: 2024-01-15  
**Category**: Software Engineering  
**Theme**: Industry Watch  

---

When CoreWeave raised $2.3 billion in debt financing last year to build more GPU clusters, the message wasn't subtle. The cloud GPU provider—built on bare metal Kubernetes—is now valued at over $7 billion. Meanwhile, AWS Lambda cooled from 40% growth rates to the mid-teens. The contradiction is real: serverless was supposed to eat the world, but latency-sensitive workloads are pulling a U-turn toward dedicated infrastructure. Cold starts aren't the only culprit—there's a deeper architectural mismatch that vendors don't want to admit.

<figure class="post-hero-image">
<img class="post-hero" src="/assets/images/posts/2026-06-02-why-ai-workloads-are-fleeing-serverless-for-bare-metal.png" alt="Hero image for Why AI Workloads Are Fleeing Serverless for Bare Metal" loading="lazy">
</figure>

## The Serverless Plateau Hits Hard

Serverless adoption has hit a wall. Industry estimates suggest 60-65% of enterprises now use some form of serverless, but that number has stayed flat since 2022. The spending tells a different story: hyperscaler serverless revenue grew only 12% YoY in Q3 2024, while dedicated compute spending jumped 28% per Synergy Research.

Why? Three reasons:

- **Cost unpredictability** — Hacker News threads show teams getting $10k+ monthly bills from runaway functions
- **Resource limits** — Lambda's 10GB memory cap kills batch inference workloads
- **Cold starts** — Not just for Python anymore; new container runtimes introduced their own overhead

| Factor | Serverless (AWS Lambda) | Bare Metal (CoreWeave) |
|--------|------------------------|------------------------|
| Cold start latency | 200ms-1s (10th-95th percentile) | <5ms (always warm) |
| GPU memory limit | 10GB | Up to 80GB (A100) |
| Cost for 24/7 inference | 3-5x premium | 1.2-1.5x premium over cloud VMs |
| Vendor lock-in | High (event bridge, step functions) | Moderate (Kubernetes native) |

The dirty secret: serverless economics break once you have sustained traffic above 20-30% utilization.

## Cold Starts Mask a Deeper Problem

Everyone blames cold starts. They're wrong.

The real issue is **interconnect locality**. Serverless functions spawn on random hosts—you can't guarantee your function runs near Redis, Postgres, or your model weights. When your inference request needs to grab 10MB of shared state from an ElastiCache node on the other side of an AZ, that's 50ms+ of cross-AZ latency, plus the function's own startup time.

OpenAI learned this the hard way. Their ChatGPT infrastructure runs on dedicated A100 clusters, not Lambda functions. The delta between local cache access (5μs) and cross-AZ cache access (500μs) is two orders of magnitude—devastating for real-time inference.

Hybrid architectures are emerging: use serverless for the control plane, bare metal for the data plane. Replicate's vector database operators manage their own Kubernetes pods with dedicated GPU resources, while the API gateway is serverless. This split acknowledges that serving models and sharding data need deterministic latency budgets.

## Winners, Losers, and the Middle

**Winners**: CoreWeave, Lambda Labs, and specialized bare metal providers. Their growth validates the thesis that GPU workloads need dedicated infrastructure. Vultr's bare metal cloud grew 40% in 2024 by targeting inference workloads.

**Losers**: Supabase (lost its edge as serverless Postgres hit VPC latency limits), and teams that bet their entire stack on Lambda for cost savings. Datadog data shows serverless functions with >30s execution time cost 2.7x more than equivalent containers.

**Caught in the middle**: Google Cloud Run. It's serverless, but with 4 vCPU limits and no GPU support. Fine for web apps, useless for ML inference. GCP teams using Cloud Run for ML are hitting 500ms max per-request latency before throttling.

## When to Stay, When to Jump

**Stay with serverless when:**
- Traffic is spiky (<10% sustained utilization)
- Functions are stateless and trivial (<1s runtime)
- Cold start tolerance is 500ms+
- You value autoscaling over absolute performance

**Jump to bare metal when:**
- GPU/TPU model serving (any latency-sensitive ML workload)
- High-throughput data pipelines (ETL, real-time joins)
- Low-latency financial trading (<50μs jitter)
- Stateful applications with local caching requirements

**Wait when:**
- You're in the middle—20-60% utilization, don't have dedicated DevOps team. Consider hybrid: serverless API + managed Kubernetes pools.

**Avoid entirely when:**
- You need PCI DSS Level 4 compliance and SOC2 Type II—bare metal offers better audit trails than shared infrastructure.

## The Trend Bent Not Broken

Three things to take away:

1. **Serverless is entering a maturity trough.** Not dead, but not the future of compute. Gartner's hype cycle got it right for once.
2. **Latency-sensitive ML workloads are the canary.** If your model serving needs deterministic latency, serverless is structurally incapable of providing it. The networking overhead in serverless architectures makes this a physics problem, not a software one.
3. **The real innovation is in hybrid patterns, not "anything serverless."** Expect Knative on bare metal, WASM on dedicated GPUs, and smart routing layers that cold-start only for tail requests.

## The Next 12-18 Months

By late 2025, expect hyperscalers to pivot. AWS will likely launch "Reserved Lambda" — provisioned concurrency with slot-level placement guarantees, matching current EC2 dedicated host pricing. Google will do the same with Cloud Run. This trend isn't about raw performance; it's about operational reality. The teams bragging about 99.9% serverless uptime are the ones who don't run inference on it. When your model needs to think in milliseconds, not seconds, bare metal becomes the only game in town. And that's worth more than any convenience hack.