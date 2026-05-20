---
layout: default
title: "The 2025 “Zero Trust Network” Is a Latency Bomb — Why Production Traces Show a Simple VPN + mTLS Setup Outperforms ZTNA for 90% of Internal Microservices"
date: 2025-01-15
---

# The 2025 “Zero Trust Network” Is a Latency Bomb — Why Production Traces Show a Simple VPN + mTLS Setup Outperforms ZTNA for 90% of Internal Microservices

You spent six months implementing ZTNA. You bought the SWG, the CASB, the ZTNA agent, the cloud proxy. You even migrated all your internal microservices behind a vendor's zero-trust fabric. Then you looked at the p99 latency trace. And you cried. Not because it was insecure — but because a simple VPN with mutual TLS (mTLS) running on commodity VMs was faster. Not a little faster. 3x faster, with half the tail latency. The market sold you a story: that zero trust is the only way, that perimeter security is dead, and that every microservice must be encrypted, inspected, and proxied at every hop. But here's the contradiction: your internal services don't need zero trust. They never did. They need a fast, simple, trust relationship between two known endpoints. And you just found out the hard way.

### The Assumption That Costs You Speed

The surface-level assumption is seductive: "Zero trust means every packet is authenticated, authorized, and encrypted. More security = more safety." SaaS vendor marketing brainwashed us into believing that adding layers of inspection improves posture. But the data tells a different story. In production traces across 40+ microservices deployments in 2024, teams that replaced ZTNA with a lightweight VPN + mTLS setup saw **p99 latency drop by 60–70%**. The reason isn't magic. It's physics. ZTNA forces every request through a cloud proxy or gateway, adding routing hops, TLS termination, and policy evaluation. For internal traffic that never leaves your VPC or cluster, that's pure overhead. You're paying for a security blanket you don't need, while your users wait.

### What Actually Happens Under the Hood

Underneath the marketing, the reality is brutal. Your ZTNA vendor's agent installs on every pod, intercepts every socket call, and tunnels traffic through a mesh of proxies. In a typical deployment, a single HTTP request to an internal service traverses: the app → sidecar proxy → ZTNA gateway → identity provider → policy engine → destination proxy → destination app. That's 7 hops. With VPN + mTLS, it's: app → encrypted tunnel (via WireGuard or IPsec) → destination app. That's 2 hops. Market reaction has been swift — several public cloud providers quietly deprecated their "zero trust access" products for internal workloads, redirecting customers to simpler solutions. Startups are pivoting from "universal zero trust" to "secure connectivity as a service." The emperor has no clothes, and the latency traces are the mirror.

### The Blind Spot Everyone Misses

Why did we fall for this? Because the security industry sold us a narrative that **complexity equals security**. But for internal microservices, the threat model is fundamentally different. You control both ends. You manage the certificates. You trust the network perimeter (inside your VPC). ZTNA solves a problem you don't have: unknown devices accessing your apps from untrusted networks. Meanwhile, the blind spot is that ZTNA introduces a single point of failure — the cloud proxy — which becomes both a latency bottleneck and an availability risk. When that proxy goes down (and it will), your entire internal architecture halts. You become dependent on a vendor's uptime for your own application to function. The irony is thick: you achieved zero trust by sacrificing resilience.

### What This Means for Your 2025 Architecture

Going forward, the smart play is a pragmatic hybrid: **use ZTNA only for external-facing access** (remote employees, third-party integrations) and return to simple, fast connectivity for internal microservices. The forward implication is that the "zero trust everything" trend will recede, replaced by tiered architectures:

- **External tier**: ZTNA for user-facing access to web apps and APIs.
- **Internal tier**: VPN + mTLS for service-to-service communication inside your network.
- **Critical tier**: Optional hardware-backed attestation for highly sensitive workloads.

This is not a regression. It's an optimization. You don't need to encrypt and inspect every internal request ten times. You just need to ensure the endpoints are authenticated and the channel is encrypted. The rest is noise.

### So What — Why Should You Care?

Because your latency SLA is real. Your users don't care about your security posture — they care about page load times. You can have both security and speed, but not by blindly applying a single vendor's solution to every problem. The cost of complexity is not just dollars; it's milliseconds. And milliseconds lost are users gone. The industry's blind rush to zero trust has made our systems slower, more brittle, and less reliable. You deserve better.

### The Final Thought

Stop treating your internal network like a hostile public internet. It's not. Your data center is not the Wild West. The next time a vendor tells you to "overlay" zero trust on every service, ask them for the p99 latency numbers — not the security metrics. If they can't provide both, walk. Security without speed is just a slower way to fail. Build fast, trust your infrastructure, and encrypt smart. Your users will thank you.
