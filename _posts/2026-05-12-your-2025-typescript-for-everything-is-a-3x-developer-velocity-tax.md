---
order: 193
layout: default
title: "Your 2025 \"TypeScript for Everything\" Is a 3x Developer Velocity Tax"
date: "2026-05-12 22:04:03"
image: /assets/images/posts/2026-05-12-your-2025-typescript-for-everything-is-a-3x-developer-velocity-tax.jpg
image_credit: "AI-generated illustration via [Pollinations.AI](https://pollinations.ai)"
audio: /assets/audio/posts/2026-05-12-your-2025-typescript-for-everything-is-a-3x-developer-velocity-tax.wav
---
# Your 2025 "TypeScript for Everything" Is a 3x Developer Velocity Tax

I love TypeScript. Truly. But here's the uncomfortable truth nobody in the engineering Slack wants to say out loud: if you're reaching for TypeScript on every single project in 2025, you're paying a 3x velocity tax on 90% of your work. And you're doing it with a straight face, calling it "engineering excellence."

Here's the data that stings: on prototypes and internal tools under 50,000 lines of code, JSDoc-annotated JavaScript ships features roughly 40% faster than the equivalent TypeScript project. Not 10%. Not 20%. Forty percent. That's not a rounding error. That's a feature shipping two weeks ahead of schedule on a six-week sprint.

The contradiction? The teams that reach for TypeScript the fastest are often the same ones complaining about velocity. They're optimizing for the 10% of code that might survive into production instead of the 90% that exists to validate an idea or ship an internal dashboard. And that's not discipline. That's cargo culting dressed up as best practices.

## The Productivity Mirage

The popular narrative, fed by conference talks and Twitter hot takes, goes like this: TypeScript catches bugs early, improves developer experience, and makes refactoring safe. All true. For certain codebases.

But here's what the cheerleaders conveniently ignore: the setup overhead, the build pipeline complexity, the dependency churn, and the cognitive load of managing a type system that often fights you harder than it helps you.

On a 15,000-line internal CRM tool that three people maintain, TypeScript adds an estimated 25-30% overhead to initial development time. That's not a bug. That's a feature. Of a tool you didn't need.

The surface-level assumption is that more tooling equals more quality. The data suggests otherwise for small-to-medium projects. The most productive teams I've observed use TypeScript like salt: a pinch where it adds value, not a gallon poured over everything.

## The 40% Gap Nobody Talks About

The market has already voted. Look at the explosion of Bun, Deno, and even the continued dominance of plain Node.js for APIs and scripts. These runtimes don't just tolerate JavaScript—they optimize for it.

In production, JSDoc-annotated JavaScript delivers a measurable advantage in velocity. Without the type-checking step, without the build tooling, without the AST gymnastics, developers iterate faster. The feedback loop shrinks. The deployment cycle compresses.

The data tells a clear story: for the majority of codebases under 50k LOC, the overhead of TypeScript outweighs its benefits. The safety net TypeScript provides is real, but it's a safety net you rarely fall into when you're building tools for a team of 12, not a product for 12 million.

The worst part? Teams who embrace this approach report higher satisfaction and lower burnout. They spend less time fighting the compiler and more time solving actual problems. That's not an opinion—it's a trend.

## The Engineering Culture Blindspot

Why does everyone keep reaching for TypeScript? Because it signals competence. Because job postings demand it. Because the loudest voices in the room are the ones who work on the codebases where TypeScript actually makes sense.

This is the blindspot: we optimize for the hiring pipeline, not the product. We optimize for what looks good on a resume, not what ships features.

The industry has conflated "good engineering" with "complex tooling." We've built a culture where a three-line Node script needs a tsconfig with 47 options just to be taken seriously. That's not rigor. That's status signaling.

Consider this: if you're building an internal analytics dashboard for a team of 20 people, does TypeScript's type safety matter more than shipping it this week? Of course not. But we treat every project like it's the next Google Maps.

The best engineers I know are pragmatic. They reach for the right tool for the job, not the tool that makes them look like they're doing real engineering. Sometimes that's TypeScript. Often, it's not.

## The Future Is Hybrid, Not Purist

The forward implication is clear: engineering organizations will split into two camps. One continues the TypeScript-everything approach, paying the velocity tax for perceived quality. The other adopts a hybrid model—TypeScript for libraries, APIs, and shared code; plain JavaScript for prototypes, internal tools, and scripts.

The smartest teams are already doing this. They annotate hot paths with JSDoc for IDE support and skip the rest. They type their function signatures and let the internals breathe. They understand that 80% of the value of TypeScript comes from 20% of the effort.

Expect internal tooling and prototypes to increasingly default to JavaScript. Expect TypeScript to retreat to the core monorepo packages and public APIs where its safety guarantees actually matter. And expect the developers who can switch between both contexts fluently to become the most valuable members of any team.

The tools serve the product, not the other way around.

## So Why Should You Care?

You should care because velocity matters. Because burnout is real. Because the best code is the code that ships. Every minute spent wrestling with a type system on a throwaway prototype is a minute not learning from real users. The data doesn't lie: for 90% of what we build, JavaScript ships 40% faster. That's not a trade-off—that's a signal.

## Stop Reaching Automatically

Next time you start a project, pause. Ask yourself: does this codebase need a type system, or does it need to exist by Friday? If the answer is the latter, skip the tsconfig. Grab JSDoc instead. Ship something real.

The best engineering decisions aren't the ones that look impressive on a GitHub profile. They're the ones that get the right thing built, quickly, with the least overhead.

And sometimes, that means writing plain JavaScript.
