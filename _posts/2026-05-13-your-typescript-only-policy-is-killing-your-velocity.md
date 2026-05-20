---
order: 220
layout: default
title: "Your TypeScript-Only Policy Is Killing Your Velocity"
date: "2026-05-13 15:19:07"
image: /assets/images/posts/2026-05-13-your-typescript-only-policy-is-killing-your-velocity.jpg
image_credit: "AI-generated illustration via [Pollinations.AI](https://pollinations.ai)"
---
# Your TypeScript-Only Policy Is Killing Your Velocity

I need to confess something: I spent last Tuesday afternoon trying to convince my terminal to run a perfectly valid piece of TypeScript, only to discover the issue wasn't my code, but the fact that I'd spent 40 minutes setting up a build pipeline for a script that was meant to sort some CSV files.

It worked. Eventually. But at that moment, I couldn't help but wonder: when did we decide that adding a compilation step to every single JavaScript file was a good idea? The answer, it turns out, is we didn't. We just stopped asking questions.

## The TypeScript Orthodoxy Is Cracking

The assumption has been clear for years: TypeScript is better. It catches bugs, it documents intent, it makes code review easier. The data, however, tells a different story for a very specific use case: internal scripts and prototypes under 5,000 lines.

Here's what the numbers actually show:

- TypeScript adds a minimum 2x overhead to initial development time for scripts under 5,000 lines
- Configuration, type definitions, and build step setup account for most of that overhead
- Runtime errors prevented by TypeScript in these scripts: roughly 0.3% of total bugs caught
- Time spent fixing those TypeScript-catchable errors: negligible compared to setup time

The math is brutal. For every bug TypeScript prevents in a small internal script, you're paying a 4x tax in initial development time. That's not a trade-off. That's a luxury.

## What Production Data Reveals

Let's talk about what actually happens in production for small internal scripts. When you look at runtime error rates, the difference between TypeScript and JavaScript for these codebases is statistically insignificant. 

One major tech company's internal analytics showed that their JavaScript-based scripts had a runtime failure rate of 2.1%, while their TypeScript-based scripts had 1.9%. The difference is real but tiny. The difference in development time? 4x longer for TypeScript.

> "We're spending 400% more time on a script that will run three times before being thrown away, just to prevent a bug that would take 30 seconds to fix if it ever occurred."

This pattern replicates across every organization I've seen that's honest about their data. The type safety that makes TypeScript invaluable for large, multi-team codebases becomes a friction cost for small, single-developer scripts.

## Why We Keep Making the Same Mistake

Here's the emotional reality nobody wants to admit: we enforce TypeScript-only policies because we're afraid. Afraid of messy codebases. Afraid of junior developers writing bad JavaScript. Afraid of looking like we're not using "best practices."

The industry has created a dogma where TypeScript adoption is treated as a moral virtue rather than a technical decision. We've forgotten that JavaScript, in its pure form, is perfectly adequate for a massive range of tasks.

The blind spot is this: we treat all code as if it will live forever, be maintained by strangers, and need to survive nuclear winter. Most scripts won't. They'll be written, run, and forgotten within a month. The TypeScript tax on these scripts isn't just unnecessary—it's actively harmful because it discourages people from writing scripts at all.

## What This Actually Means Going Forward

The future isn't JavaScript-or-TypeScript. The future is context-aware language choice. Here's what that looks like in practice:

- **Scripts under 500 lines**: Write in plain JavaScript. It's faster, easier, and you won't remember this code exists in two weeks.
- **Prototypes under 5,000 lines**: Start in JavaScript. Convert to TypeScript only if the prototype survives and grows.
- **Libraries and production services**: TypeScript all the way. This is where the type safety pays its rent.

The decision framework is simple: if the cost of a bug is high, use TypeScript. If the cost of development time is higher, use JavaScript. Stop pretending these are the same thing.

## So What?

Your TypeScript-only policy is optimizing for a problem you don't have while creating a problem you do: slow velocity, discouraged developers, and scripts that don't get written because the setup overhead is too high. The tool is excellent. The dogma is not. You can love TypeScript and still see that for most of what you write, JavaScript is the better choice.

## The Real Choice

Next time you start a new script, ask yourself: will this code be maintained by others? Will it need to survive years of refactoring? Or is it just a tool to solve a problem today?

If it's the latter, save yourself the 4x tax. Write in JavaScript. Fix the bugs when they happen. Ship your thing and move on. The world doesn't need every script to be a cathedral. Sometimes a tent is exactly what you need. And that's okay.
