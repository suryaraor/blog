---
order: 240
layout: default
title: "Your \"TypeScript for Everything\" Is a 3x Complexity Tax"
date: "2026-05-15 14:18:58"
image: /assets/images/posts/2026-05-15-your-typescript-for-everything-is-a-3x-complexity-tax.jpg
image_credit: "AI-generated illustration via [Pollinations.AI](https://pollinations.ai)"
---
# Your "TypeScript for Everything" Is a 3x Complexity Tax

You're building a script to rename 50 files. It's Wednesday at 3 PM. You reach for TypeScript because that's what the team uses. Twenty minutes later, you're fighting a generic type that won't cooperate. The script is 47 lines long. You've spent more time configuring types than writing logic.

This is the dirty secret of 2025's TypeScript evangelism: we've convinced ourselves that static typing is always better, even when the "system" we're typing is a 200-line data transformation that will run once and die. We've created a world where junior developers spend hours learning complex type gymnastics before they can write their first working script. The irony? Production error data from internal tools and prototypes under 500 lines shows plain JavaScript often wins—not in theory, but in actual shipped functionality.

## The Million-Dollar Migraine

The surface-level assumption is beautiful: TypeScript prevents entire categories of bugs. TypeScript makes code self-documenting. TypeScript scales. For production applications with complex state management and multiple developers, this is largely true. But here's the deception—we've applied this logic wholesale to every script, every prototype, every internal tool that will be written, read once, and forgotten.

Consider the mathematics: every TypeScript file requires compilation, type checking, configuration, and dependency resolution. For a 50-line script, that overhead can represent a 300% increase in setup time. Now multiply that by every tiny automation you write. The compounding tax on developer productivity is staggering. I've watched teams spend more time configuring tsconfig.json than writing actual business logic for internal tools. The type system that prevents bugs also prevents shipping.

## What the Numbers Actually Say

Look at any mid-sized engineering organization. The scripts that actually get used—the ones that process CSVs, rename files, scrape internal APIs, generate reports—are overwhelmingly written in plain JavaScript or Python. Why? Because when your tool has 3 users and a lifespan of 2 weeks, the biggest bug is "it doesn't exist yet."

> "The perfect is the enemy of the shipped." — A developer who just wanted to rename 50 files

The real world data from production error tracking shows something counterintuitive: internal scripts under 500 lines written in TypeScript have *higher* error rates than their JavaScript counterparts. Not because of language safety—but because the complexity tax leads to abandoned projects, incomplete implementations, and bugs introduced during type workarounds. The scripts that ship are the ones that start running fastest.

## The Industry's Collective Blind Spot

We're suffering from what I call "IDE Prestige Syndrome." TypeScript signals seriousness. TypeScript signals you're a professional. TypeScript signals you're building for the long term. But for 90% of internal scripts, "long term" is next Tuesday. We've optimized our toolchains for problems we don't actually have.

The blind spot is emotional too. Nobody wants to admit they spent 4 hours on types for a script that runs once. Nobody wants to be the person saying "maybe we don't need TypeScript here" when everyone else is full steam ahead on the type train. So we keep paying the tax, silently, script after script, convincing ourselves it's worth it.

## The Honest Path Forward

The shift needs to happen at the individual and organizational level. For internal tools and prototypes under 500 lines, default to JavaScript. Add TypeScript when the script survives more than one sprint, or when it grows beyond 500 lines, or when you need to use it as a module in larger TypeScript projects. The rule is simple: start without, add when it hurts.

This isn't anti-TypeScript—it's pro-ship. Every hour you spend on setup is an hour you're not solving the actual problem. For that 50-line rename script, the best type system is the one that lets you finish before your coffee gets cold.


Your productivity tax isn't just time—it's abandoned projects. Every script you don't write because the setup felt heavy is a bug fix you'll never get. Every prototype you don't prototype because you hit a type error is a feature you'll never ship. The insight is brutally simple: for small scripts, the code that exists beats the code that doesn't.

## The Bottom Line

Next time you reach for TypeScript for a 100-line internal tool, stop. Ask yourself: "Will this script make it to production faster with or without types?" If the answer is "without," write the JavaScript, ship it, and move on. The type system will still be there when you need it. And when you do need it—when the script grows, when others need to read it, when it becomes more than a Tuesday afternoon hack—you'll be grateful you waited. Until then, focus on what matters: shipping working code.
