# Inside the Terminal Code Loop: Primitives of File Editing, Context Windows, and Shell Execution Tracking

You've used an AI coding assistant before. You type a prompt, it spits out code, you copy it into your editor. Maybe it works. Maybe it doesn't. Maybe you lose track of what changed.

Now imagine something different. Instead of generating text that you manually apply, the AI directly edits your files, runs shell commands, and tracks every change across multiple files — all from your terminal. No copy-pasting. No context-switching.

This is the world of terminal-native coding agents like Claude Code, OpenCode, and DeepCode. These tools operate inside a fundamentally different loop than chat-based assistants. They work with primitives: file edits, shell execution, and careful tracking of what they can see and do.

In this tutorial, I'll demystify exactly how these primitives work. You'll learn what these tools are, how file editing and shell commands execute under the hood, how multi-file reasoning works, and why context window management is the hidden superpower — or achilles heel — of every coding agent.

By the end, you'll understand not just *what* these tools do, but *how* they do it, and how you can use that knowledge to get better results.

---

## Claude Code, OpenCode, and DeepCode: Three Windows into the Same Room

Let's start with the obvious question: what are these tools?

**Claude Code** is Anthropic's terminal-based coding agent. **OpenCode** is an open-source alternative. **DeepCode** is another implementation. All three share the same core idea: an AI assistant that lives in your terminal, directly edits your files, runs commands, and reasons across multiple files.

Think of them as different operating systems for the same hardware. The hardware is the "terminal code loop" — the cycle of reading context, making changes, and getting feedback. Each tool implements this loop slightly differently, but the primitives are identical.

Here's the key insight: **these tools don't generate code for you to paste. They directly modify your filesystem.** When Claude Code decides to fix a bug, it opens the file, makes the change, and saves it. No middleman.

**How it works under the hood:** The tool has access to a sandboxed environment (usually a Docker container or a restricted shell). It can call functions like `read_file()`, `write_file()`, and `execute_command()`. Each action is logged, tracked, and reversible.

**Analogy:** Imagine a skilled carpenter (the AI) standing at your workbench (the terminal). Instead of telling you what to build and handing you plans, they pick up the tools and build it themselves. You're there to supervise and give feedback.

```python
# Simplified example of how these tools work internally
class TerminalAgent:
    def __init__(self, model, workspace):
        self.model = model  # The AI model (Claude, GPT, etc.)
        self.workspace = workspace  # Your project directory
        self.context = []  # Current context window contents
        
    def execute_edit(self, file_path, old_text, new_text):
        """Directly edit a file in the workspace"""
        with open(f"{self.workspace}/{file_path}", 'r') as f:
            content = f.read()
        
        # The AI proposes: "Replace this function with this better version"
        updated_content = content.replace(old_text, new_text)
        
        with open(f"{self.workspace}/{file_path}", 'w') as f:
            f.write(updated_content)
        
        print(f"✅ Edited {file_path}")
```

**Non-obvious insight:** These tools are surprisingly bad at complex git operations. They'll happily rewrite your entire file when a two-line change would do. Always review the diff before accepting.

---

## File Edits: Surgery Without a Scalpel

**File Edits** are the core action a terminal agent performs. When the AI decides your code needs changing, it constructs an edit — a precise modification to a specific file.

**Plain-English definition:** A file edit is a targeted changeset. The AI says "in `app.py`, replace lines 42-47 with this new code." The tool does exactly that.

**How it works:** Under the hood, these tools use a structured format. Claude Code uses a special XML-like syntax. OpenCode uses JSON blocks. Both describe: which file to edit, where in the file (by line numbers or search text), and what the new content should be.

**Analogy:** Think of a surgeon performing laparoscopic surgery. They make small incisions (file edits) at precise locations, guided by cameras (the context window). The tool tracks every incision and can reverse it.

```xml
<!-- Claude Code's file edit format -->
<edit>
  <file>src/database.py</file>
  <search>def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))</search>
  <replace>def get_user(user_id):
    cursor.execute("SELECT id, name, email FROM users WHERE id = ?", (user_id,))</replace>
</edit>
```

**Non-obvious insight:** The `<search>` block must match *exactly*. A single extra space breaks the edit. This is why well-formatted code matters more with AI tools — they're literal-minded.

---

## Shell Command Execution: Letting the AI Type

**Shell Command Execution** is the ability for the AI to run terminal commands in your project. `npm install`, `git status`, `python test.py` — the AI can execute them directly.

**Plain-English definition:** The AI can type and run commands just like you would in your terminal. It sees the output and uses that to plan its next action.

**How it works:** The tool spawns a subprocess (or uses a Docker container) and executes the command. Output is captured and added to the context window. This creates a feedback loop: edit → run → see output → edit again.

**Analogy:** Imagine a chef who tastes their dish after every addition. The spoon is shell execution — it tells them if they need more salt (fix a bug) or if the dish is ready (tests pass).

```python
# Shell execution in practice
output = agent.execute_shell("pytest tests/")
print(output)
# Output: "FAILED tests/test_auth.py::test_login - AssertionError: Expected 200, got 401"

# Agent sees the failure and decides to fix the login endpoint
agent.execute_edit(
    "routes/auth.py",
    "return redirect('/login')",
    "return jsonify({'token': create_token(user)}), 200"
)
```

**Non-obvious insight:** Most tools limit execution to 30-60 seconds per command. Long-running processes (like database migrations) will timeout. You must structure commands to fit within this window.

---

## Context Window Tracking: The AI's Working Memory

**Context Window Tracking** is how the AI keeps track of what it's seen and done. Every file content, every command output, every conversation turn — it all needs to fit in the AI's limited attention span.

**Plain-English definition:** The context window is the AI's short-term memory. It can only hold so much information before older details fade away.

**How it works:** The tool maintains a buffer of recent interactions. When you ask about a file, it reads the file content and pushes it into the buffer. When the buffer fills, older items get evicted. Some tools (like Claude Code) are smarter about this — they prioritize recent edits and command outputs over initial conversation.

**Analogy:** Your desk has limited space. You can only see the papers within arm's reach. When you pick up a new file, you must put something else aside. Context window tracking is the system for deciding what stays on the desk.

```python
# Context window management
class ContextWindow:
    def __init__(self, max_tokens=100000):
        self.max_tokens = max_tokens
        self.items = []  # Files, commands, conversations
        self.current_tokens = 0
        
    def add_item(self, item):
        """Add item, evicting oldest if window is full"""
        item_tokens = count_tokens(item)
        while self.current_tokens + item_tokens > self.max_tokens:
            evicted = self.items.pop(0)
            self.current_tokens -= count_tokens(evicted)
            print(f"⚠️ Evicted: {evicted.name}")
        self.items.append(item)
        self.current_tokens += item_tokens
```

**Non-obvious insight:** Once a file's content is evicted from the context window, the AI "forgets" what it says. This is why large projects hit a wall — the AI can't maintain full context.

---

## Multi-File Reasoning: Seeing the Forest

**Multi-File Reasoning** is the ability to understand how changes in one file affect another. It's not just editing multiple files — it's understanding their relationships.

**Plain-English definition:** The AI can look at your project structure, understand imports, class hierarchies, and function calls across files, and make coordinated edits.

**How it works:** The tool reads multiple files into its context. It uses code understanding (syntax trees, dependency graphs) to trace how changes propagate. When it edits `user_service.py`, it knows to check `user_controller.py` and `user_tests.py` too.

**Analogy:** You're renovating a house. Changing the kitchen plumbing affects the bathroom upstairs. Multi-file reasoning is the plumber who knows the whole system.

```python
# Multi-file edit orchestration
def fix_user_registration(agent):
    """Coordinated edit across three files"""
    
    # Step 1: Add password validation to user model
    agent.execute_edit(
        "models/user.py",
        "class User:",
        "class User:\n    def validate_password(self, pwd):\n        return len(pwd) >= 8"
    )
    
    # Step 2: Update controller to use validation
    agent.execute_edit(
        "controllers/auth.py",
        "user = User(name, email, password)",
        "user = User(name, email, password)\nif not user.validate_password(password): raise ValidationError()"
    )
    
    # Step 3: Add test for new validation
    agent.execute_edit(
        "tests/test_auth.py",
        "def test_register_success():",
        "def test_password_too_short():\n    ...\n\ndef test_register_success():"
    )
```

**Non-obvious insight:** These tools can't actually understand circular dependencies or deep inheritance chains. They treat files as flat text, not as a connected graph. Always verify cross-file consistency.

---

## Comparison Table: The Primitives at a Glance

| Primitive | What It Does | How It Works | Gotcha |
|-----------|--------------|--------------|--------|
| **File Edits** | Directly modifies files | Replace exact text or lines | Must match search text exactly |
| **Shell Execution** | Runs terminal commands | Spawns subprocess, captures output | Timeouts on long-running commands |
| **Context Window** | Tracks what AI has seen | FIFO buffer with token counting | Older context gets evicted |
| **Multi-File Reasoning** | Coordinates changes across files | Reads multiple files, traces dependencies | Poor understanding of complex code structures |

---

## Key Takeaways

- **Claude Code, OpenCode, DeepCode** are terminal-based coding agents that directly modify your filesystem
- **File edits** use exact text matching — one extra space breaks the edit
- **Shell execution** creates a feedback loop: edit → test → see output → edit again
- **Context windows** are limited memory buffers — the AI forgets old context
- **Multi-file reasoning** works best with flat, well-structured code — complex dependencies confuse it
- Review every edit before accepting, especially with large projects
- Use small, incremental changes rather than massive rewrites — the AI handles them better
