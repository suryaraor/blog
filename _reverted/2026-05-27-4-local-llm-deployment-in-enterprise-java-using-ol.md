# Local LLMs in Enterprise Java with Ollama and Spring Boot

You've probably heard the hype: Large Language Models (LLMs) are transforming how we build software. But the cloud-based ones come with a catch — your data leaves your network. What if you could run a powerful, conversation-capable AI right inside your Java application, using your own hardware, without sending a single byte to an external API? That's exactly what you'll learn to do here. We'll break down **Ollama**, **Privacy**, **Local**, **Deployment**, and **Inference** step by step. You'll see how to set up a local LLM server with Ollama, then call it from a Spring Boot app, all while keeping your data under your control. No cloud keys. No data leaks. Just you, your code, and a local brain.

## Ollama: Your Personal LLM Butler

**Ollama** is a free, open-source tool that lets you download, run, and manage large language models on your own machine. Think of it as a pet butler who lives in your basement. You tell him which AI "chef" (model) to hire, and he prepares it for service, keeping everything inside your house. No outside delivery trucks.

Under the hood, Ollama wraps popular models like Llama 3, Mistral, and Gemma into a simple API. It handles model downloading, quantization (reducing model size for performance), and exposes a RESTful interface. You interact with it via a command-line client or a local web server.

Here's how you get it running:

```bash
# Install Ollama (macOS/Linux — visit ollama.com for Windows)
curl -fsSL https://ollama.com/install.sh | sh

# Start the Ollama server (it listens on localhost:11434)
ollama serve

# In another terminal, download and run the Mistral model
ollama run mistral
# You can now chat with it directly in the terminal.
# "Hello!" -> "Hello! How can I help you today?"
```

The `ollama run` command downloads the model (if not already cached) and starts an interactive session. But for our Spring Boot app, we'll use the REST API it exposes.

## Privacy: Your Data, Your Rules

**Privacy** in this context means your data never travels beyond your local network. No third-party servers see your prompts, responses, or any sensitive information you might pass to the model.

The mechanism is straightforward: with a local model, the inference happens entirely on your machine. The model's weights are stored in your local filesystem, and all computation happens on your CPU or GPU. No API calls to OpenAI, Anthropic, or any cloud provider.

Analogy: Sending data to a cloud LLM is like mailing your diary to a stranger to read and annotate. Using a local LLM is like keeping the diary on your nightstand and reading it yourself. Same act, radically different control.

Here's a concrete example: imagine your Spring Boot app processes financial documents containing account numbers. With a cloud LLM, those numbers leave your server. With a local model, they never leave your machine:

```java
@RestController
public class DocumentController {

    @Autowired
    private LlmService llmService;

    @PostMapping("/analyze/transaction")
    public String analyzeTransaction(@RequestBody Transaction tx) {
        // Sensitive data — account numbers, amounts, etc.
        String prompt = "Analyze this transaction for fraud: " + tx.toString();
        // Only your local machine sees this prompt
        return llmService.askLocalModel(prompt);
    }
}
```

Non-obvious insight: even model metadata (like which model you're using) stays private. With cloud APIs, the mere act of querying reveals something about your application's domain.

## Local: No Internet Required

**Local** means everything — the model, the inference engine, and the calling application — runs on hardware you physically control. Your machine, your server rack, your VM inside your corporate network.

Under the hood, the model's neural network weights are loaded into RAM. When you send a prompt, the CPU or GPU processes it through the network layers, generating a response, all within the same process space. No network round trips to a remote data center.

Analogy: Imagine two coffee shops. One ships beans to a central roaster, waits for the batch, then serves your latte. The other roasts beans in the back room while you wait. The local model is the second coffee shop — everything happens under one roof.

To prove it works without internet, try this: disconnect your Wi-Fi, then run:

```bash
ollama run mistral "What is 2+2?"
# Output: "2+2 = 4"
```

Your laptop just answered a math question with zero external connectivity. That's the power of local.

## Deployment: From Command Line to Production

**Deployment** in this context means getting your local LLM to serve requests reliably within your enterprise Java application — not just in a terminal demo.

The mechanism: you run Ollama as a background service (systemd on Linux, launchd on macOS), then configure your Spring Boot app to point at its local REST endpoint. You add basic error handling, connect to your app's authentication, and set up logging and monitoring around the LLM calls.

Analogy: You've trained a new intern (Ollama) to answer questions. Deployment is giving them a desk, a badge, and connecting their phone to your company's switchboard so they can take calls from customers.

Here's the Spring Boot setup:

```java
@Service
public class LlmService {

    private final RestTemplate restTemplate;
    private final String ollamaUrl = "http://localhost:11434/api/generate";

    public LlmService() {
        this.restTemplate = new RestTemplate();
    }

    public String askLocalModel(String prompt) {
        var request = Map.of(
            "model", "mistral",
            "prompt", prompt,
            "stream", false  // Get complete response, not chunks
        );

        var response = restTemplate.postForEntity(
            ollamaUrl,
            request,
            Map.class
        );

        return response.getBody().get("response").toString();
    }
}
```

Edge case: what if Ollama is down? Your app should handle `ConnectException` gracefully:

```java
try {
    return restTemplate.postForEntity(ollamaUrl, request, Map.class);
} catch (ResourceAccessException e) {
    // Log the failure and return a fallback message
    log.error("Ollama unavailable. Check if service is running.");
    return "I'm sorry, the local AI is currently offline.";
}
```

## Inference: The Actual Brain Work

**Inference** is the act of the model generating a response to a prompt. It's the computation that turns "What is the capital of France?" into "Paris."

Under the hood, inference involves feeding your prompt through the model's neural network layers. Each layer transforms the input, and the final layer predicts the most likely next token (word fragment). This repeats, token by token, until the model signals it's done or you set a maximum length.

Analogy: Inference is like a master pianist improvising a piece. They don't look up sheet music. They've internalized patterns (the model's training data) and produce note after note based on what came before. Each note is a prediction of what sounds best next.

You've already seen inference in action — every `ollama run` command performs inference. Here's how you'd set the temperature (creativity level) in Java:

```java
var request = Map.of(
    "model", "mistral",
    "prompt", "Craft a haiku about Java",
    "stream", false,
    "options", Map.of(
        "temperature", 0.7,  // Lower = more deterministic, higher = more creative
        "max_tokens", 50    // Limit response length
    )
);
```

Non-obvious insight: inference speed depends on model size, quantization, and your hardware. Mistral 7B can run on a decent laptop CPU at 5-10 tokens/second. Llama 70B requires a powerful GPU. Always test with your target hardware.

## Comparison: Cloud vs. Local LLMs

| Feature | Cloud LLM | Local LLM (Ollama) |
|---|---|---|
| **Privacy** | Your data leaves your network | Data stays on your machine |
| **Latency** | Variable (network delay) | Predictable (local compute) |
| **Cost** | Per-token pricing | Free (hardware cost only) |
| **Model Variety** | Provider's catalog | Any open-source model |
| **Setup Time** | Minutes (API key) | Hours (download + config) |
| **Performance** | Powerful hardware | Limited by your hardware |
| **Offline** | No | Yes |

## Key Takeaways

- **Ollama** simplifies local LLM management — download, run, and serve models via a REST API.
- **Privacy** means your data never leaves your machine, crucial for sensitive enterprise workloads.
- **Local** execution means only your hardware matters — no network round trips to clouds.
- **Deployment** with Spring Boot requires minimal code, but handle the Ollama service going down.
- **Inference** happens entirely on your CPU/GPU, token by token, with controllable parameters like temperature and max tokens.
