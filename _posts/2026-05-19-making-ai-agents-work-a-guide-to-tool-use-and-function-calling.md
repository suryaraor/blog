---
order: 294
layout: default
title: "Making AI Agents Work: A Guide to Tool Use and Function Calling"
date: "2026-05-19 16:21:49"
image: /assets/images/posts/2026-05-19-making-ai-agents-work-a-guide-to-tool-use-and-function-calling.jpg
image_credit: "AI-generated illustration via [Pollinations.AI](https://pollinations.ai)"
audio: /assets/audio/posts/2026-05-19-making-ai-agents-work-a-guide-to-tool-use-and-function-calling.wav
---
# Making AI Agents Work: A Guide to Tool Use and Function Calling

Imagine asking an AI to send an email, only to watch it write a *draft* of an email and then stop. Frustrating, right? That’s the limit of a pure language model. It can reason about tasks but can't interact with the real world.

In this guide, you'll learn how to bridge that gap. We’ll demystify **Function Calling**, **Tool Schemas**, **API Invocation Patterns**, **External Services**, **Enterprise Data Sources**, and the critical security concept of **Least-Privilege Access**. We’ll build from the ground up, with analogies and code, so you can give your AI agents the ability to actually *do* things.

## Function Calling

**Definition**: Function calling is the mechanism that lets a large language model (LLM) request a specific action, rather than just generating text. It doesn't *execute* the action itself; it asks *you* to do it.

**How it works**: The LLM receives a list of available "functions" (actions) as part of its prompt. When a user asks, "Send an email to my team," the model picks the most suitable function (e.g., `send_email`) and outputs a structured JSON object containing the function's name and its required parameters.

**Analogy** : You're at a restaurant. You don't walk into the kitchen and cook; you tell the waiter (the LLM) what you want. The waiter writes down your order (the function call) and hands it to the chef (your code). The chef cooks the meal and brings it back.

**Code Example** (Python with OpenAI):
```python
# Define the function the LLM can call
def send_email(recipient: str, subject: str, body: str):
    # Your actual email-sending logic
    print(f"Email sent to {recipient}")
    return f"Success: Sent email to {recipient}"

# The LLM's response
# It outputs: {"function": "send_email", "arguments": {"recipient": "team@co", "subject": "Meeting", "body": "Today at 3"}}
function_call = response.choices[0].message.function_call
function_name = function_call.name
arguments = json.loads(function_call.arguments)

# Your code executes the request
if function_name == "send_email":
    result = send_email(**arguments)
```
**Non-obvious insight** : The LLM decides *which* function to call, but you write the code that runs it. This separation is crucial for security and control.

## Tool Schemas

**Definition**: A tool schema is a structured definition of a function, written in JSON format. It tells the LLM everything it needs to know: the function's name, its purpose, its parameters (data types, whether they're required), and what it returns.

**How it works**: You provide these schemas as part of the LLM prompt. The model "reads" them like a manual. It understands that `send_email` needs a valid email address for `recipient`, not a full name. A well-written schema prevents the model from inventing parameters.

**Analogy**: This is like a form you fill out at the DMV. The form tells you exactly what information is needed (Name, Address, License #) and the format (Text, 5-digit zip, 9-digit). The LLM can't make up a field called "Favorite Color" because the form doesn't have a space for it.

**Code Example** (JSON Schema):
```json
{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get the current weather for a city.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The city name, e.g., London, Tokyo"
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"]
                }
            },
            "required": ["city"]
        }
    }
}
```
**Non-obvious insight** : The `description` fields are critical. LLMs use them to disambiguate between similar functions. A generic description like "for a location" is much less useful than "the city name, e.g., London, Tokyo." The more specific, the fewer errors.

## API Invocation Patterns

**Definition**: An API invocation pattern is the specific way your code receives, processes, and responds to a function call request from the LLM. It’s the pattern you follow to turn the LLM's request into real action.

**How it works**: You have three main patterns: (1) **Single-turn** – LLM asks, you execute, return result. (2) **Multi-turn** – LLM asks, you execute, return result, LLM can then ask for more info or a different function. (3) **Nested** – The result of one function call is used as input for another.

**Analogy**: Single-turn is like a vending machine (insert money, get a snack, done). Multi-turn is like a conversation with a personal assistant ("Order a pizza" → "What kind?" → "Pepperoni" → "Please confirm your address"). Nested is like a cooking recipe that says "First, prepare the sauce, *then* use that sauce to make the pasta."

**Code Example** (Multi-turn Pattern):
```python
# Turn 1: User asks, LLM responds
response = model.invoke("Book a flight to Paris")
# Response asks for more info: {"function": "get_flight_options", "arguments": {"destination": "Paris"}}

# Turn 2: Your code executes and returns results
flight_data = get_flight_options("Paris")
# Return the result back to the model to continue
model.invoke({"role": "user", "content": "I see flights for $300 on Air France."})
```
**Non-obvious insight** : A single-turn pattern is simpler, but multi-turn is essential for complex tasks like travel booking, where you need to confirm details. Getting the pattern right is often the difference between a frustrating and a delightful user experience.

## External Services

**Definition**: External services are any third-party APIs your agent calls to get data or perform actions—like sending an email, querying a weather service, or posting to Slack.

**How it works**: You wrap the service's API in your own function. The LLM never talks to the external service directly. It calls your function, and your function handles authentication, rate limiting, and error handling with the external API.

**Analogy**: Think of a translator. The LLM speaks a language of intent. External services speak a language of REST endpoints and API keys. Your code is the translator—it takes the LLM's request (the function call) and translates it into the exact HTTP request the service understands.

**Code Example** (Wrapping an HTTP API):
```python
import requests

def call_weather_service(city: str):
    # Your code, not the LLM, handles the external call
    url = f"https://api.weatherapi.com/v1/current.json?key={API_KEY}&q={city}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    return {
        "temperature": data["current"]["temp_c"],
        "condition": data["current"]["condition"]["text"]
    }
```
**Non-obvious insight** : Never pass API keys or credentials in the function definition passed to the LLM. The LLM could accidentally output them. Store them securely in environment variables or a vault.

## Enterprise Data Sources

**Definition**: Enterprise data sources are internal databases, CRMs, ERPs, or data warehouses that contain proprietary business data. For an agent to act on this data, it must query these sources via code.

**How it works**: You create functions that query your enterprise data (e.g., "get_customer_info(customer_id)") and make them available as tool schemas to the LLM. The LLM can then request data from these sources in a secure, structured way.

**Analogy**: It's like having a personal librarian. You can ask, "Find me all books by author 'Smith' published after 2020." You don't need to know where the books are stored, how the filing system works, or what SQL query to run. The librarian (your function) knows how to access the database and return the relevant results.

**Code Example** (Querying a PostgreSQL database):
```python
import psycopg2

def query_sales_data(start_date: str, end_date: str):
    conn = psycopg2.connect(dsn="db://...")
    cur = conn.cursor()
    cur.execute("""
        SELECT product, SUM(amount)
        FROM sales
        WHERE sale_date BETWEEN %s AND %s
        GROUP BY product
    """, (start_date, end_date))
    results = cur.fetchall()
    cur.close()
    conn.close()
    return [{"product": r[0], "total_sales": r[1]} for r in results]
```
**Non-obvious insight** : Always sanitize and parameterize inputs to database queries. An LLM can be tricked into constructing a malicious function call that leads to SQL injection.

## Least-Privilege Access

**Definition**: Least-privilege access means giving your agent only the minimum permissions it needs to perform a specific task, and nothing more. The agent should be able to *read* a customer record but not *delete* it, unless that's the explicit job.

**How it works**: You enforce this by defining separate tool schemas for each action. You don't create a single "manage_customer" function that can read, write, and delete. Instead, you have three separate functions: `read_customer`, `update_customer`, `delete_customer`. You decide which ones to expose to the LLM.

**Analogy**: A hotel key card. You can only access your floor, the pool, and the gym. You can't enter the manager's office or the storage room. The card is programmed with exactly the permissions you need. Your tool schemas are the same—they grant only the necessary access.

**Code Example** (Defining separate, limited functions):
```python
# Correct: One function per action
def read_employee(employee_id):  # OK: Read access
    pass

def update_employee_email(employee_id, new_email):  # OK: Limited update
    pass

# Incorrect: One function with all access
def manage_employee(action, employee_id, data):  # DANGER: Exposes too much
    if action == "delete":
        # This function should never be given to the LLM
        pass

# You only expose read_employee and update_employee_email to the model
tool_registry = [read_employee_schema, update_employee_email_schema]
```
**Non-obvious insight** : A common mistake is to build a "super function" that can do anything. This is a huge security risk. If the LLM is tricked, it has too much power. Stick to atomic functions.

## Comparison: Concept Mapping

| Concept | Role | Who Defines It? | Analogy | Risk if Missing |
| :--- | :--- | :--- | :--- | :--- |
| **Function Calling** | The agreement to act | LLM says "I want to" | Waiter taking order | Agent can only talk, never act |
| **Tool Schemas** | The instruction manual | The developer | A fill-out form | LLM guesses or invents parameters |
| **API Invocation Pattern** | The conversation rhythm | The developer's code | A vending machine vs. an assistant | Agent gets stuck or confused |
| **External Services** | The outside world | Third-party provider | A translator | Agent is isolated, useless |
| **Enterprise Data Sources** | The internal knowledge | Your company | A personal librarian | Agent lacks context, makes bad decisions |
| **Least-Privilege Access** | The security guard | The developer | A hotel key card | Agent has too much power, major security risk |

## Key Takeaways

- **Function Calling** is the bridge that turns an LLM from a talker into a doer.
- **Tool Schemas** are the precise blueprints that tell the LLM *exactly* what it can do.
- **API Invocation Patterns** define the flow: one-shot, conversational, or chained.
- **External Services** let agents act in the real world, but you code the interface.
- **Enterprise Data Sources** provide the private context for smart, internal decisions.
- **Least-Privilege Access** is your most important security practice: give the smallest possible permissions for each task.
