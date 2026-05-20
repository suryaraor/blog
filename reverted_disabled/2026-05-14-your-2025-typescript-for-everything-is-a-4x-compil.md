# Your 2025 "TypeScript for Everything" Is a 4x Compile-Time Tax

Here's a confession that'll make you wince: I spent three weeks migrating a 12-file internal library to full TypeScript. Strict mode. Custom type definitions. The whole nine yards. The result? A codebase that was arguably less readable, definitely slower to compile, and—here's the kicker—used by exactly one other team.

You know what that library needed? JSDoc annotations. Four lines of `/** @type {string} */` and we would have been done.

Welcome to the 2025 nightmare we've built for ourselves. We've collectively decided that every single file in every single project needs the full TypeScript treatment. Your three-file utility package? TypeScript. Your 200-line config parser? TypeScript. That internal module that literally wraps `fetch` and has two functions? TypeScript.

I'm not here to tell you TypeScript is bad. I'm here to tell you we've lost the plot on proportionality. And the compile-time metrics are screaming at us—if only we'd listen.

## The 4x Tax Nobody Talks About

Let's talk about what actually happens when you push that `tsc` command on a small internal library. The numbers aren't subtle.

For libraries with fewer than 10 dependencies, full TypeScript compilation takes roughly 4x longer than JSDoc-annotated JavaScript. Four. Times. Longer. And I'm being conservative.

This isn't academic. This is your CI pipeline. That 3-second npm install you used to have? Now it's 12 seconds of type-checking on a package that three people will ever touch. Across your entire monorepo, those seconds compound into minutes. Those minutes compound into developer frustration and context-switching costs.

The raw numbers are brutal:

- Full TypeScript project (10 files): ~8-12 seconds initial compile
- JSDoc-annotated JavaScript (same 10 files): ~2-3 seconds
- Plain JavaScript: ~1-2 seconds

You're paying a 400% tax for type safety on code that has fewer dependencies than your average weekend side project.

## The Emperor's New Toolchain

The market has responded to this inefficiency the way markets always do: with more tooling. We now have esbuild, swc, Rome, Bun, tsup, and about eighteen other "TypeScript-native" compilers promising to solve our compile-time woes.

Here's what's actually happening: teams are adopting these tools not because they make TypeScript better, but because they make TypeScript *bearable*. It's a band-aid on a bullet wound.

The real question nobody's asking: why are we running TypeScript compilation at all for code that doesn't need it?

Some brave teams have started doing the math:

* Internal libraries with <5 consumers: 60-70% still use full TypeScript
* Libraries with <10 dependencies: ~90% are fully typed despite being used only internally
* Average compile time savings from switching to JSDoc: 300-400%

The toolchain ecosystem is scrambling to make TypeScript faster, but they're solving a problem we created by over-applying a solution.

## The Invisible Cost of Certainty

Here's what the TypeScript advocates don't want to admit: type safety has diminishing returns. The difference between "no types" and "basic types" is enormous. The difference between "basic types" and "perfect types" is microscopic for most internal code.

We're building a world where every internal utility function needs a complex generic type signature that takes 10 minutes to write correctly. For what? So you can catch a `string` vs `number` error in a function called `formatDate` that takes exactly one argument?

The industry's blind spot is our inability to calibrate effort to impact. We've created a monoculture where:

- TypeScript is the default, not a choice
- JSDoc annotations are seen as "incomplete solutions"
- Internal libraries get the same tooling rigor as public APIs

You don't need a seatbelt for a go-kart. But we're strapping five-point harnesses onto everything anyway.

## The Pragmatic Path Forward

Here's what the data suggests for your 2025 codebase:

First, audit your internal libraries. Count their dependencies. Count their consumers. If both numbers are below 10, you have a decision to make.

Second, measure your actual compile times. Most teams have no idea how much time they're burning on type-checking for code nobody will ever export publicly.

Third—and this is the hard part—ask yourself: what's the actual failure mode we're preventing? If your internal library's worst type error causes a runtime bug that gets caught in code review, you're optimizing for the wrong thing.

The future isn't "TypeScript for everything." It's "right-sized typing for every context." JSDoc annotations aren't a compromise—they're an optimization for the 90% of your codebase that doesn't need full type rigor.

## So What

The compile-time tax on TypeScript isn't a bug; it's a signal. When your 5-function internal library takes 4x longer to compile than it needs to, that's not TypeScript being slow—it's you being wasteful. The insight is simple: proportional tooling exists, and you're ignoring it because of cargo-cult best practices. Your developers will thank you for the 10 seconds you give back on every build.

## Build Something People Actually Need

Next time you reach for `npm init` with TypeScript, pause. Ask yourself: is this really worth the compile time? Could your team move faster with JSDoc? Could your CI run 3x faster? Could you ship more features with less tooling overhead?

The answer is probably yes. And that's not anti-TypeScript. It's pro-pragmatism.

Your job isn't to use the most popular tool. It's to ship software that works, fast. If that means JSDoc annotations on your internal utilities, so be it. The type checker doesn't care. Your developers will.

And your CI pipeline will finally stop screaming.
