# Minigpt-LLMM1S2
A fully functional, multi-turn chat application powered by a locally running LLM (Llama 3, Mistral, Gemma, etc.) via [Ollama](https://ollama.com). Built with Streamlit's native chat primitives. No API keys and no data leaves your machine.
Letting users manipulate autoregressive decoding parameters (Temperature, Top-P) and inspect the raw JSON context window to understand the nature of transformer models.

---

##  Architecture

```
┌──────────────────┐      HTTP (localhost:11434)      ┌─────────────────┐
│  Streamlit UI    │  ──────────────────────────────► │  Ollama Server  │
│  (chatbot.py)    │  ◄──────────────────────────────  │  (local daemon) │
└──────────────────┘     streaming token chunks       └─────────────────┘
         │
         │  reads / writes
         ▼
┌──────────────────────────────────────┐
│         st.session_state             │
│  messages: [                         │
│    {"role": "system",  "content": …} │  ← injected at request time
│    {"role": "user",    "content": …} │  ← stored in state
│    {"role": "assistant","content": …}│  ← stored after streaming
│    …                                 │
│  ]                                   │
└──────────────────────────────────────┘
```

### The Conversation memory model

This is the most important concept in the project. Streamlit re-runs the entire Python script from top to bottom on every user interaction. Ordinary variables are reset to their initial values on each run.

`st.session_state` is a special dictionary that **persists across reruns** for the lifetime of a browser session. The conversation history is stored there as a list of message dicts — the same format used by the OpenAI API:

```python
[
    {"role": "user",      "content": "What is gradient descent?"},
    {"role": "assistant", "content": "Gradient descent is an optimisation algorithm…"},
    {"role": "user",      "content": "Give me a Python example."},
]
```

### Streaming

`ollama.chat(..., stream=True)` returns a generator that yields token chunks. Streamlit's `st.write_stream()` consumes this generator and renders each token into the chat bubble as it arrives — producing the typewriter effect.

---

##  Setup and installation

### Step 1: Install Ollama

Ollama is a standalone application that manages and serves local LLM models. It is not a Python package.

**macOS / Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
Download the installer from [ollama.com/download](https://ollama.com/download).

Verify the installation:
```bash
ollama --version
```

---

### Step 2: Pull a model

Ollama downloads and manages model weights for you. 

Example:
```bash
ollama pull llama3
```

This downloads the quantised model weights (~4–7 GB). You only need to do this once.

---

### Step 3: Start the Ollama server

Ollama runs as a background HTTP server on `localhost:11434`. On macOS it starts automatically; on Linux/Windows you may need to start it manually:

```bash
ollama serve
```

Leave this terminal open, or configure Ollama to run as a system service.

---

### Step 4: Set up the Python environment

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/mini-chatgpt.git
cd mini-chatgpt

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

### Step 5: Run the app

```bash
streamlit run chatbot.py
```

The app opens at `http://localhost:8501`. Select your installed model from the sidebar and start chatting.

---

##  Design cdecisions
When designing the architecture for this application, my primary challenge was navigating the inherently stateless nature of Large Language Models. I implemented a system that simulates persistent memory by passing the entire conversation history back into the context window for every single API request. A specific design choice I made was decoupling the system prompt from the visual session state history. Instead of saving it into the chat log, the system instructions are injected dynamically at request time. This separation of concerns keeps the UI clean while giving the user the flexibility to edit the assistant's persona on the fly between conversational turns.
To handle the text generation, I utilized Streamlit's st.write_stream method by passing it a generator. This updates the UI atomically and completely bypasses the visual flickering that usually happens when manually appending strings and re-rendering in a loop. Furthermore, because local inference relies heavily on the Ollama daemon, I wrapped the streaming calls in strict try/except blocks. Local environments are unpredictable, by doing this, common failures like an offline server, out-of-memory errors, or unpulled model are caught and translated into helpful UI warnings rather than causing silent application crashes.

## Architectural limitations

Because inference runs entirely locally via Ollama, both token generation speed and permissible model sizes are strictly bottlenecked by the host machine's available RAM and GPU compute power. To highlight the hard context limits of LLMs, I included a "Token Usage Meter." Since the application appends the entire conversation history every turn, computational cost grows linearly and once the native context window (e.g. 8192 tokens for LLaMA 3) is breached, the system must truncate older messages, resulting in a sudden "amnesia" effect to prevent crashes. And to keep the application lightweight, I opted for a character-to-token heuristic (roughly four characters per token) rather than importing heavy, model-specific libraries like tiktoken or sentencepiece. While robust for standard English estimation, I acknowledge this approach loses precision when analyzing complex code blocks or non-English languages.

---

##  References

- [Streamlit Chat Elements Docs](https://docs.streamlit.io/develop/api-reference/chat)
- [Streamlit Session State Docs](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state)
- [Ollama Python Client](https://github.com/ollama/ollama-python)
- [Meta Llama 3 Model Card](https://ai.meta.com/blog/meta-llama-3/)

---

