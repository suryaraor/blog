# Teaching AI to Review Its Own Work: Agentic Reflection in Practice

## Introduction

Think of the last time you submitted code for review. You wrote it, you thought it was solid, then a colleague found three edge cases you missed. It's humbling, but it makes the code better. Now imagine your AI could do that for itself — automatically critique its own output, identify flaws, and iterate until the result is genuinely polished. That's the core of **Agentic AI Reflection**. In this article, you'll learn exactly what this pattern is, why it matters for software engineering, and how to implement it with concrete code. We'll break down the mechanism step by step, using a real-world analogy and an annotated Python example that you can run today.

## What is Agentic AI Reflection?

Let's start with a plain-English definition. **Agentic AI Reflection** is a process where an AI system generates an initial output, then systematically evaluates and revises that output — often in multiple rounds — to improve its quality. It's like the AI running its own code review, but without the pull request.

Under the hood, the mechanism works like this: The AI produces a response (say, a function or a paragraph), then sends that response back to itself (or a separate critic model) with a prompt like "Find three problems with this output." Based on the critique, it generates a revised version. This loop can repeat until a quality threshold is met.

**Analogy**: Imagine you're writing a first draft of an email. You type quickly, then read it aloud. You catch typos, awkward phrasing, places where you sound too harsh. Then you rewrite. Reflection is that "read aloud" step, automated and scaled.

Here's a simplified Python example using a mock AI model:

```python
import json

def generate_output(prompt: str) -> str:
    # Simulates an AI model call
    return "Add two numbers: def add(a,b): return a+b"

def critique_output(output: str) -> list[str]:
    # Simulates a critic model
    critiques = []
    if "Add two numbers" in output:
        critiques.append("Docstring repeats the prompt — redundant.")
    if "type hints" not in output:
        critiques.append("Missing type hints for parameters.")
    if "edge case" not in output:
        critiques.append("No handling of non-numeric inputs.")
    return critiques

def reflect_and_revise(prompt: str, max_iterations: int = 2) -> str:
    output = generate_output(prompt)
    for i in range(max_iterations):
        critiques = critique_output(output)
        if not critiques:
            break
        # Simulate revision based on critiques
        output = output.replace(
            "Add two numbers: def add(a,b): return a+b",
            "def add(a: float, b: float) -> float:\n    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):\n        raise TypeError\n    return a + b"
        )
    return output

print(reflect_and_revise("Write a function to add two numbers"))
# Output: def add(a: float, b: float) -> float:\n    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):\n        raise TypeError\n    return a + b
```

Non-obvious insight: Reflection works best when the critic model is separate from the generator. Using the same model can lead to "confirmation bias" — it sees its own blind spots less clearly. In practice, tools like LangChain implement reflection using distinct agents.

## The Critic Role: How Self-Evaluation Works

The **critic role** is the component that examines the output and produces actionable feedback. It's not just "good" or "bad" — it points to specific issues: missing imports, logic errors, ambiguous naming.

Mechanically, the critic is often a separate language model invoked with a structured prompt. For code, you might prompt the critic with: "Review this function for correctness, style, and edge cases. List exactly three improvements." The output is a list of flaws, which the generator model then addresses.

**Analogy**: You're a musician recording a track. You play it back and think, "The guitar is slightly out of tune in the second chorus." The critic is your ear catching that specific flaw.

Example critique prompt structure:

```
You are a code reviewer. Given this function:
[function body]
List exactly three improvements related to:
1. Correctness (potential bugs)
2. Performance (inefficiencies)
3. Readability (style/naming)
```

Non-obvious gotcha: If the critic is too harsh or too lenient, the iteration can either stall (endless revisions) or skip important fixes. Many production systems use a calibrated critic — fine-tuned on real code review datasets — to get the tone right.

## The Iteration Loop: How Quality Improves Over Rounds

The **iteration loop** is the mechanism that cycles between generation and critique. Each round refines the output, reducing error rates incrementally. In practice, two to three rounds are optimal — more than that yields diminishing returns (or "over-fitting" the critique).

Under the hood, the loop tracks a quality score (e.g., correctness percentage from unit tests) and stops when a threshold is met. This prevents infinite loops and wasted compute.

**Analogy**: A chef tastes the soup, adds salt, tastes again, adds pepper, tastes again — each round adjusts the flavor slightly. After two or three adjustments, it's perfect.

Numbered breakdown of a typical iteration loop:

1. **Generate initial output** based on user prompt.
2. **Critique** the output for defined dimensions (correctness, style, edge cases).
3. **Revise** by incorporating the critique (often via a new prompt that includes the original + critique).
4. **Re-critique** to verify improvements were actually made.
5. **Loop** until quality score >= threshold or max iterations reached.

Non-obvious insight: The iteration duration matters. If each round is too short (low temperature, greedy decoding), the model makes shallow fixes. If too long (high temperature, diverse sampling), it can "drift" into nonsense. Finding the sweet spot is more art than science.

## Applying This to Real Code: A Practical Example

Let's tie it together with a concrete, real-world scenario: generating an API endpoint handler with error handling.

System setup: We'll use a simple orchestrator that calls two model functions (generator and critic) in a loop. The key is that the critic's output is fed back into the generator's context.

```python
def generate_api_handler(endpoint: str) -> str:
    # Simulated generation
    return f"""def {endpoint}():
    data = request.json
    return process(data)"""

def critic_for_api(code: str) -> str:
    critiques = []
    if "try" not in code:
        critiques.append("Missing try/except block for handling exceptions.")
    if "status_code" not in code:
        critiques.append("No HTTP status code in response.")
    if "validate" not in code:
        critiques.append("No input validation — potential security risk.")
    return "\n".join(critiques) or "No issues found."

def reflect_on_api(endpoint: str, rounds: int = 2) -> str:
    code = generate_api_handler(endpoint)
    for i in range(rounds):
        print(f"Round {i+1}: Current code:\n{code}")
        critique = critic_for_api(code)
        if critique == "No issues found.":
            break
        # Simulate revision: add try/except, validation, and status code
        code = f"""def {endpoint}():
    try:
        data = request.json
        if not data.get('user_id'):
            return {{'error': 'missing user_id'}}, 400
        result = process(data)
        return {{'success': result}}, 200
    except Exception as e:
        return {{'error': str(e)}}, 500"""
    return code

final_endpoint = reflect_on_api("create_user")
print(final_endpoint)
```

Non-obvious insight: Reflection can be computationally expensive (double or triple the tokens). For latency-sensitive apps, consider running only the first critique round offline, or caching common critiques.

## Comparison Table: Reflection Patterns

| Pattern | Approach | Best For | Risk |
|---|---|---|---|
| **Single-round reflection** | Generate, critique once, revise | Quick quality check (typos, minor bugs) | Misses deep issues |
| **Multi-round reflection** | Loop until quality threshold | Complex code (APIs, algorithms) | Over-iteration = wasted compute |
| **Self-critique** | Same model as critic and generator | Low-cost setups | Confirmation bias |
| **Separate critic** | Different model for critic (specialized) | High-stakes output (security, finance) | Latency and cost doubled |

## Key Takeaways

- **Agentic Reflection** is the AI equivalent of self-code-review — generate, critique, revise.
- The **critic role** must be specific and structured (list flaws, not general praise).
- The **iteration loop** improves quality incrementally, but stop after 2–3 rounds.
- Use a **separate critic model** if possible, to avoid confirmation bias.
- Always **unit test** the final output; critique is a supplement, not a substitute for QA.
- The real world implication? You ship faster because you trust your AI's output more. But never skip human review for production code — reflection catches style and simple bugs, not architectural flaws. Use it as a tool, not a crutch.
