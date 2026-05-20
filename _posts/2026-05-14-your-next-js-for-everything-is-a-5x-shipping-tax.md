---
order: 234
layout: default
title: "Your “Next.js for Everything” Is a 5x Shipping Tax"
date: "2026-05-14 22:19:07"
image: /assets/images/posts/2026-05-14-your-next-js-for-everything-is-a-5x-shipping-tax.jpg
image_credit: "AI-generated illustration via [Pollinations.AI](https://pollinations.ai)"
---
# Your “Next.js for Everything” Is a 5x Shipping Tax

I watched a team spend three weeks configuring middleware, ISR, and edge functions for a five-page restaurant site. The owner wanted a menu, contact form, and hours of operation. They got a 2.3MB JavaScript bundle, a build pipeline that broke twice, and a deployment that took twelve minutes. Meanwhile, a competitor built the same thing in two days with Express + Handlebars. Their page loaded in 400ms. Their build took four seconds. Their developer went home at 5pm. This is not a hot take about framework superiority. This is basic math. And right now, most teams are paying a 5x shipping tax for features they never use.

## The Server-Side Rendering Mirage

Every job description demands Next.js. Every bootcamp teaches it. Every startup boilerplate ships it. But the data tells a different story—one most developers refuse to hear. On content sites under ten pages, the overhead of Next.js isn’t a minor cost. It’s structural. You’re paying for file-system routing when you have five routes. You’re optimizing images you don’t have. You’re wrestling with static generation for content that never changes.

> Most production Next.js content sites ship 5x more JavaScript than their Express + Handlebars equivalents, with no measurable user-facing benefit.

The benchmark is simple: compare bundle sizes, build times, and Time to Interactive. On small content sites, Express wins every metric that matters to users. The only metric Next.js wins is developer resume relevance.

## The Productivity Tax Nobody Measures

Here’s what I hear from teams who switched back: “We spent more time configuring Next.js than building the actual site.” This isn’t anecdotal. It’s structural. Every Next.js feature—image optimization, font loading, API routes, incremental static regeneration—solves real problems. But those problems don’t exist on a site with three blog posts and a contact form.

- File-system routing means nothing for five pages
- Automatic code splitting solves bundle problems you don’t have
- Edge functions add complexity for traffic that doesn’t exist
- Static regeneration fixes cache invalidation on data that never changes

The shipping tax compounds because each feature adds cognitive overhead. Your team spends meetings debating `getStaticProps` versus `getServerSideProps` for a page that gets twenty visitors a month. That time has a cost. That cost is the tax.

## The Emotional Attachment to Complexity

Nobody admits they over-engineered. It feels like admitting you bought a Ferrari for grocery runs. But the real reason developers reach for Next.js on small sites isn’t technical—it’s emotional. We want to feel like we’re building at scale. We want our tools to match our ambitions, not our requirements. There’s a deep, unspoken fear that using “simple” tools makes you a simple developer.

This fear is expensive. It costs your client money. It costs your team time. It costs users performance. The emotional attachment to complexity is the industry’s most underdiscussed tax. We’ve created a culture where choosing the right tool feels like admitting defeat. That’s backwards. The best engineers I know reach for Express + Handlebars on small content sites because they value being done over being impressive.

## The Return of Honest Tools

The market is starting to correct itself. Teams are quietly migrating small sites back to simpler stacks. Not because Next.js is bad—it’s excellent for large, interactive applications. But because the cost-benefit curve inverts somewhere around page ten. Below that threshold, you’re paying full price for benefits you’ll never realize.

The forward-looking pattern is honest tooling. Express with a template engine. Static HTML with a build script. Maybe a lightweight static site generator if you need markdown support. These tools don’t pretend to solve problems you don’t have. They ship fast, deploy instantly, and let developers focus on content instead of configuration.

The next time you start a small content project, ask yourself one question: “What does Next.js solve that Express doesn’t?” If the answer is “I don’t know,” you’re paying the tax.

## So What

You are not a bad developer for choosing simple tools. You are a bad developer for choosing expensive tools that solve imaginary problems. The shipping tax isn’t measured in dollars—it’s measured in weeks of your life spent configuring things you don’t need. The insight is this: on 90% of content sites under ten pages, the best tool is the one that gets out of your way.

## Build Something That Ships

Next time you reach for `npx create-next-app` on a small content project, stop. Open a terminal. Type `npm init`. Install Express. Write a route. Render a template. Deploy in five minutes. See how it feels. The goal isn’t to abandon modern tools. It’s to stop paying the complexity tax for features you’ll never use. Your users won’t notice your framework choice. They’ll notice the page that loads instantly. Build that.
