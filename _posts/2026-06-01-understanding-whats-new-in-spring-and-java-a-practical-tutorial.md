---
order: 362
layout: default
title: "Understanding What's New in Spring and Java: A Practical Tutorial"
date: 2026-06-01 09:15:16
image: /assets/images/posts/2026-06-01-understanding-whats-new-in-spring-and-java-a-practical-tutorial.png
image_credit: "Architecture diagram generated via DeepSeek + Excalidraw"
audio: /assets/audio/posts/2026-06-01-understanding-whats-new-in-spring-and-java-a-practical-tutorial.wav
---
# Understanding What's New in Spring and Java: A Practical Tutorial

If you've been coding in Java for a while, you've probably heard about the latest updates to Spring and Java but felt overwhelmed by all the buzzwords. Virtual threads? Project Loom? Spring Boot 3? It's a lot. And honestly, most tutorials assume you already know half of it.

This article changes that. You'll learn exactly what's new in Spring and Java, starting from the ground up. I'll explain every concept in plain English first, show you how it works under the hood, give you a memorable analogy, and then demonstrate it with real code. By the end, you'll understand virtual threads, records, pattern matching, and the latest Spring Boot features well enough to use them tomorrow.

We'll cover: virtual threads (Project Loom), records, sealed classes, pattern matching for switch, and Spring Boot 3's key improvements.

<figure class="post-hero-image">
<img class="post-hero" src="/assets/images/posts/2026-06-01-understanding-whats-new-in-spring-and-java-a-practical-tutorial.png" alt="Hero image for Understanding What&#39;s New in Spring and Java: A Practical Tutorial" loading="lazy">
<figcaption>Architecture diagram generated via DeepSeek + Excalidraw</figcaption>
</figure>

## Virtual Threads: Threads Without the Headache

**Plain-English definition:** Virtual threads are lightweight threads that let you write concurrent code without the performance penalty of traditional threads. They're like having a thousand delivery drivers instead of ten.

**How it works:** Traditional Java threads map directly to operating system threads. Each one uses about 1MB of memory. That limits how many you can create. Virtual threads are managed by the JVM itself. They're stored on the heap and use only a few kilobytes. When a virtual thread blocks (say, waiting for a database response), the JVM parks that virtual thread and lets another one run on the underlying OS thread.

**Analogy:** Think of traditional threads as dedicated checkout lanes at a grocery store. Each lane needs a cashier (OS thread) and the lane itself (memory). If you have 100 lanes, you need 100 cashiers. Virtual threads are like a single self-checkout machine that can handle 100 customers by quickly swapping them in and out.

**Code example:**

```java
// Without virtual threads — limited to ~1000 concurrent tasks
ExecutorService executor = Executors.newFixedThreadPool(10);
for (int i = 0; i < 1000; i++) {
    executor.submit(() -> {
        // Simulate blocking I/O
        Thread.sleep(1000);
        return "done";
    });
}
executor.shutdown();

// With virtual threads — handles 100,000 concurrent tasks easily
ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor();
for (int i = 0; i < 100000; i++) {
    executor.submit(() -> {
        // Same blocking I/O, but now it's cheap
        Thread.sleep(1000);
        return "done";
    });
}
executor.shutdown();
```

*The first example creates 10 OS threads. It can handle about 10 concurrent tasks before queueing. The second example? Each task gets its own virtual thread. You can run 100,000 tasks without crashing your machine.*

**Non-obvious insight:** Virtual threads don't speed up CPU-bound work. If your task calculates pi for 10 seconds, a virtual thread still takes 10 seconds of CPU time. The magic is for I/O-heavy workloads — databases, HTTP calls, file reads — where threads spend most of their time waiting.

## Records: Data Carriers Without the Boilerplate

**Plain-English definition:** Records are a concise way to create classes that are "just data" — they come with constructors, getters, equals(), hashCode(), and toString() built in.

**How it works:** When you write `record Point(int x, int y) {}`, the compiler generates a final class with private final fields, a canonical constructor, accessor methods (not getX(), but x()), equals(), hashCode(), and toString() — all automatically.

**Analogy:** Records are like ordering a pre-configured sandwich. Instead of specifying every ingredient and assembling it yourself, you just say "turkey on rye" and everything comes ready.

**Code example:**

```java
// Old way — so much boilerplate
public class Person {
    private final String name;
    private final int age;
    
    public Person(String name, int age) {
        this.name = name;
        this.age = age;
    }
    
    public String getName() { return name; }
    public int getAge() { return age; }
    
    @Override
    public boolean equals(Object o) { /* 10 more lines */ }
    @Override
    public int hashCode() { /* 5 more lines */ }
    @Override
    public String toString() { return "Person[name=" + name + ", age=" + age + "]"; }
}

// New way — three lines, same functionality
public record Person(String name, int age) {}
```

*The record gives you: constructor, accessors (person.name()), equals, hashCode, and toString. You can still add custom methods if needed.*

**Non-obvious insight:** Records can't extend other classes, but they can implement interfaces. And their fields are implicitly private and final — they're truly immutable by default.

## Sealed Classes: Controlled Inheritance

**Plain-English definition:** Sealed classes let you control which other classes can extend or implement them. You explicitly list the permitted subclasses.

**How it works:** You declare a class as `sealed` and specify the `permits` clause. The permitted subclasses must be in the same module or package. This lets the compiler and developers know exactly which subclasses exist — enabling exhaustive pattern matching.

**Analogy:** Sealed classes are like a guest list for a private party. Instead of letting anyone show up, you control exactly who's invited. The bouncer (compiler) knows everyone allowed.

**Code example:**

```java
public sealed class Vehicle permits Car, Truck, Motorcycle {}
// Only these three classes can extend Vehicle

final class Car extends Vehicle {}
final class Truck extends Vehicle {}
final class Motorcycle extends Vehicle {}

// Now pattern matching can check all cases
String describeVehicle(Vehicle v) {
    return switch (v) {
        case Car c -> "Four wheels";
        case Truck t -> "Eighteen wheels";
        case Motorcycle m -> "Two wheels";
        // No default needed — compiler knows we covered all cases
    };
}
```

*If you remove any case from the switch, the compiler complains. That's the power of sealed classes combined with pattern matching.*

**Non-obvious insight:** The permitted subclasses must be either final, sealed themselves, or non-sealed. This prevents breaking the sealed hierarchy from deeper inheritance.

## Pattern Matching for Switch: Smarter Conditionals

**Plain-English definition:** Pattern matching lets you test a value against multiple patterns (types, conditions, or data structures) in a switch expression.

**How it works:** The switch statement now works with any reference type — not just primitives and enum. You can match on type (like `case String s`), check conditions (like `case Integer i && i > 0`), and destructure records.

**Analogy:** Pattern matching is like a mail sorter that can look at each envelope and decide its destination based on shape, weight, and zip code — all in one step.

**Code example:**

```java
// Before — messy instanceof checks
String oldWay(Object o) {
    if (o instanceof String) {
        String s = (String) o;
        return "String: " + s;
    } else if (o instanceof Integer && ((Integer) o) > 0) {
        Integer i = (Integer) o;
        return "Positive integer: " + i;
    }
    return "Other";
}

// After — clean, readable pattern matching
String newWay(Object o) {
    return switch (o) {
        case String s -> "String: " + s;
        case Integer i && i > 0 -> "Positive integer: " + i;
        case null -> "Null";
        default -> "Other";
    };
}
```

*The compiler checks that patterns are exhaustive and that no pattern shadows another. This catches bugs at compile time.*

## Spring Boot 3: What Changed

**Plain-English definition:** Spring Boot 3 is the latest major version that fundamentally upgrades to the latest Java features and changes some foundational infrastructure.

**How it works:** Spring Boot 3 is built on Spring Framework 6, which requires Java 17 minimum. It uses Jakarta EE 9+ instead of the old javax namespace. This means package names changed — `javax.servlet` becomes `jakarta.servlet`.

**Code example:**

```java
// Spring Boot 2 (old)
import javax.persistence.Entity;
import javax.validation.Valid;

// Spring Boot 3 (new)
import jakarta.persistence.Entity;
import jakarta.validation.Valid;
```

**Key improvements:**
1. Native compilation with GraalVM — compile your app to a native executable for instant startup
2. Virtual threads support — configure Tomcat to use virtual threads
3. Improved observability with Micrometer Tracing
4. Problem details for better error responses (RFC 7807)

**Non-obvious insight:** The javax to Jakarta migration broke many libraries. Before upgrading, check that all your dependencies support Jakarta EE. A compatibility checker like `openrewrite` can automate the migration.

## How All These Concepts Fit Together

| Concept | Core Problem It Solves | What It Replaces | Key Limitation |
|---------|----------------------|------------------|----------------|
| Virtual Threads | Expensive thread overhead | Traditional OS threads | No speedup for CPU-bound work |
| Records | Verbose data classes | Lombok, hand-written POJOs | Can't extend other classes |
| Sealed Classes | Uncontrolled inheritance | Abstract classes + manual checking | Restricted to same module |
| Pattern Matching | Messy instanceof chains | Cascading if-else | Requires Java 17+ |
| Spring Boot 3 | Outdated dependencies | Spring Boot 2.x | Migration effort for javax → jakarta |

## Key Takeaways

- **Virtual threads** let you handle thousands of concurrent I/O operations with minimal memory — use them for API calls, database queries, and service calls
- **Records** cut boilerplate for data classes — use them for DTOs, request/response objects, and configuration
- **Sealed classes** create controlled hierarchies — use them for domain models and exhaustive switch expressions
- **Pattern matching** simplifies conditional logic — use it wherever you'd use instanceof checks
- **Spring Boot 3** requires Java 17+ and Jakarta EE — plan your migration carefully

The best part? These features compose. You can define a sealed interface of record types, switch on them with pattern matching, and run the whole thing on virtual threads in Spring Boot 3. That's not just progress — that's a new way to write Java.