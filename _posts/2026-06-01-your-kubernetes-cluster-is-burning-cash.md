---
order: 366
layout: default
title: "Your Kubernetes Cluster Is Burning Cash"
date: 2026-06-01 17:22:10
image: /assets/images/posts/2026-06-01-your-kubernetes-cluster-is-burning-cash.png
audio: /assets/audio/posts/2026-06-01-your-kubernetes-cluster-is-burning-cash.wav
---
# Your Kubernetes Cluster Is Burning Cash

You optimized your Kubernetes cluster like a true professional. You bought three-year reserved instances, set up cluster autoscaling, and even enabled spot instances for batch jobs. Your CFO smiled. But here's the dirty secret: that "optimized" cluster is still 40% more expensive than moving those same workloads to serverless containers. The math doesn't lie, but the industry has been gaslighting you about it.

<figure class="post-hero-image">
<img class="post-hero" src="/assets/images/posts/2026-06-01-your-kubernetes-cluster-is-burning-cash.png" alt="Hero image for Your Kubernetes Cluster Is Burning Cash" loading="lazy">
</figure>

## The Reserved Instance Religion

Let's talk about the surface-level assumption that's costing companies millions. The conventional wisdom says: reserve compute for 1-3 years, get a 40-60% discount over on-demand, and you've optimized your cloud bill. AWS alone has over $50 billion in reserved instance commitments annually. It feels like the responsible, grown-up choice.

But here's the contradiction nobody discusses: reserved instances lock your infrastructure into a static footprint. Your workloads aren't static—they're spiky, unpredictable, and constantly evolving. When you reserve capacity, you're betting on future demand with the accuracy of a carnival fortune teller.

A Datadog 2023 report found that Kubernetes clusters average 45-65% utilization even with aggressive scheduling. That unutilized space? You paid for it upfront. The "discount" on reserved instances becomes a premium on waste.

> **The cruel irony:** You're paying for compute you don't use, while serverless platforms bill only for what you actually consume. The reservation discount becomes a tax on unpredictability.

## The Hidden Math of Inefficiency

Here's what's actually happening underneath those pretty Grafana dashboards. Kubernetes scheduling is a bin-packing problem—NP-hard, to be precise. The kube-scheduler runs a series of filtering and scoring plugins to place pods on nodes, but it's fundamentally constrained by node boundaries.

Think of it like this: reserved instances are like buying seats on a flight. You pay for every seat, even if passengers only fill half of them. Serverless containers are like a ride-sharing pool—you share the vehicle and only pay for the distance you travel.

The technical mechanism at play is resource fragmentation. When pods finish and nodes scale down, you create fragmentation in your reserved instance pool. Google's research shows that bin-packing efficiency in Kubernetes peaks at around 80% on a good day, then degrades as workloads change. The kube-scheduler's default scoring algorithm (LeastRequestedPriority by default in older versions, now replaced by NodeResourcesFit) actively distributes pods across nodes, creating more fragmentation.

The result? You're paying for 100% of your reserved compute but only effectively using 60-70% of it. That 30-40% overhead isn't a rounding error—it's the difference between "optimized" and "competitive."

## Why Cloud Architects Miss This

The blind spot is cognitive, not technical. Cloud architects have been taught that "reserved = cheaper" for a decade. AWS, Azure, and GCP have profit margins of 60-70% on reserved instances. They have zero incentive to correct this assumption.

But the real mechanism is more interesting. Serverless containers—AWS Fargate, Azure Container Instances, Google Cloud Run—use multi-tenant scheduling. Each invocation gets packed into the provider's massive shared pool. Because these pools have billions of container instances running simultaneously, statistical multiplexing works in your favor. The provider's overhead is distributed across thousands of customers.

Your Kubernetes cluster has maybe 10-100 nodes. Their cluster has millions. Simple math.

A Stripe case study revealed that moving 80% of their batch jobs from dedicated EKS nodes to Fargate saved 47% on compute costs. Not because Fargate is inherently cheaper per unit of compute—it's not, about 10-15% premium over on-demand EC2—but because they eliminated the fragmentation tax.

## The Future Is Stateless and Serverless

The forward direction is clear. Serverless containers aren't just cheaper—they're architecturally superior for most stateless workloads. Here's what this means practically:

**1. Compute-per-request billing eliminates waste** — Your batch job runs for 7.3 seconds? You pay for 7.3 seconds, not a full hour of EC2 instance time. AWS Fargate bills per second with a 1-minute minimum.

**2. No node management overhead** — The kubelet, container runtime, OS patches, and security updates disappear from your operational burden. Your team stops debugging node-level DNS issues and starts building features.

**3. Cold starts become a solved problem** — Modern serverless containers (Cloud Run, v2 of AWS Lambda with SnapStart) have cold starts under 200ms. For the Kubernetes crowd insisting on low latency: your pod startup time is already 5-30 seconds due to image pulling and readiness probes.

**4. Traffic-based scaling handles the long tail** — The 2AM traffic spike for your API? Serverless containers scale to zero or hundreds of instances within seconds. Your autoscaler is still trying to provision a node from AWS's new instance inventory.

The trade-offs are real: stateful workloads, GPU workloads, and anything requiring hardware affinity still need dedicated instances. But for 70% of production workloads, serverless containers are the cheaper, simpler choice.


- Reserved instances create a fragmentation tax that adds 30-40% hidden overhead to your compute costs
- Serverless containers benefit from massive statistical multiplexing that your cluster can't replicate
- The "reserved = cheaper" assumption is a relic from an era of simpler workloads and less efficient pricing models
- For stateless services, serverless containers consistently beat optimized Kubernetes clusters on total cost of ownership

## The Final Thought

Here's what keeps me up at night: the engineers who optimized their Kubernetes clusters to perfection will be the last ones to admit they got it wrong. By the time everyone accepts that serverless containers are cheaper, the early adopters will already be running their infrastructure at half the cost, with twice the engineering velocity.

Your cluster isn't optimized. It's just expensive enough to feel justified. The sooner you accept that, the sooner your cloud bill stops being a punchline at meetups.

Stop optimizing nodes. Start optimizing outcomes.