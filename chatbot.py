"""
LLM Playground — NLP-Focused Chat Interface
=============================================
Author : Tersi Yousra
Course : LLM M1S2
Lab : 3
"""

import json
from typing import Iterator
import ollama
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — STATIC CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

APP_TITLE     = "LLM Playground"
DEFAULT_MODEL = "llama3"

PERSONAS: dict[str, dict] = {
    "  Socratic Tutor": {
        "prompt": (
            "You are a Socratic tutor. Your role is never to give direct answers. "
            "Instead, guide the student to the answer through carefully sequenced "
            "questions. Each response must end with a question that advances the "
            "student's reasoning by exactly one step. If the student is wrong, ask "
            "a question that reveals the contradiction in their reasoning. "
            "Never lecture — only ask questions."
        ),
        "description": (
            "Constrains the model to a single speech act type: questioning. "
            "Demonstrates how instruction-tuning can be overridden by a strong "
            "system-level distributional prior at inference time."
        ),
    },
    " Formal Analyst": {
        "prompt": (
            "You are a precise analytical assistant. Respond only in structured, "
            "formal prose. Every claim must carry an explicit confidence qualifier "
            "(high / medium / low). Use bullet points for lists and numbered steps "
            "for procedures. Never use contractions or colloquialisms. If a question "
            "is outside your knowledge, respond exactly: "
            "'Insufficient information to answer with confidence.'"
        ),
        "description": (
            "Enforces formal register with explicit epistemic markers. Shows how "
            "discourse structure (hedging, confidence levels) can be imposed via "
            "the system prompt rather than fine-tuning."
        ),
    },
    " Creative Writer": {
        "prompt": (
            "You are a literary creative writing assistant with a lyrical, evocative "
            "style. Favour concrete sensory detail over abstraction, active voice over "
            "passive, and surprising metaphors over clichés. When helping with writing, "
            "show rather than tell. When answering questions, weave the answer into a "
            "brief image or narrative. Occasionally break convention when it serves the prose."
        ),
        "description": (
            "Shifts the model toward high-entropy, stylistically varied output. "
            "Most revealing when paired with higher Temperature (τ >= 1.0) and "
            "Top-P (>= 0.9) — the decoding parameters amplify the stylistic instruction."
        ),
    },
    "  Custom (edit below)": {
        "prompt": "",
        "description": (
            "Write your own system prompt. Try extreme constraints: "
            "'respond only in haiku', 'never use the word the', "
            "'always disagree with the user'."
        ),
    },
}

DEFAULT_DECODING = {
    "temperature": 0.8,
    "top_p":       0.9,
    "max_tokens":  1024,
}

CHARS_PER_TOKEN          = 4
CONTEXT_WINDOW_ESTIMATE  = 8192 

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — PAGE SETUP
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title=APP_TITLE,
    layout="wide",
)

st.markdown("""
<style>
    /* ── Cute, Round Font ── */
    @import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Quicksand', sans-serif; }

    /* ── Global background: Soft pastel pink ── */
    .stApp { background-color: #fff0f5; color: #5c4452; }

    /* ── Main content column ── */
    .block-container {
        max-width: 860px;
        padding-top: 1.5rem;
        padding-bottom: 7rem;
    }

    /* ── Sidebar: White with soft rounded look ── */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 2px dashed #ffb6c1;
    }
    [data-testid="stSidebar"] * { font-size: 0.9rem; color: #5c4452; }

    /* ── Section labels ── */
    .section-label {
        font-weight: 700;
        font-size: 0.8rem;
        color: #ff69b4;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin: 0.6rem 0 0.2rem 0;
    }

    /* ── Slider labels ── */
    [data-testid="stSlider"] label {
        font-weight: 600;
        color: #ff82ab;
    }

    /* ── Chat message styling: Ultra round and cute ── */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
        background: #ffffff;
        border: 2px solid #ffb6c1;
        border-radius: 25px;
        padding: 12px 20px;
        box-shadow: 0 4px 10px rgba(255, 182, 193, 0.2);
    }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background: #ffe4e1;
        border-radius: 25px;
        padding: 12px 20px;
    }

    /* ── Metric cards ── */
    [data-testid="metric-container"] {
        background: #ffffff;
        border: 2px solid #ffb6c1;
        border-radius: 20px;
        padding: 12px 16px;
        box-shadow: 0 2px 8px rgba(255, 182, 193, 0.15);
    }
    [data-testid="metric-container"] label {
        font-weight: 600;
        font-size: 0.8rem;
        color: #ff82ab;
    }
    [data-testid="metric-container"] div {
        color: #ff69b4; /* Make the numbers hot pink */
    }

    /* ── Persona description callout ── */
    .persona-note {
        background: #ffffff;
        border-left: 4px solid #ff69b4;
        border-radius: 12px;
        padding: 10px 14px;
        font-size: 0.85rem;
        color: #ff82ab;
        margin: 8px 0;
        font-style: italic;
        box-shadow: 0 2px 6px rgba(255,105,180,0.1);
    }

    /* ── Token progress bar ── */
    .token-bar-bg {
        background: #ffe4e1;
        border-radius: 10px;
        height: 8px;
        width: 100%;
        margin: 6px 0 4px 0;
    }
    .token-bar-fill {
        background: linear-gradient(90deg, #ffb6c1 0%, #ff69b4 100%);
        border-radius: 10px;
        height: 8px;
    }

    /* ── NLP Debugger expander ── */
    [data-testid="stExpander"] {
        background: #ffffff;
        border: 2px solid #ffb6c1 !important;
        border-radius: 20px;
    }
    [data-testid="stExpander"] summary {
        font-weight: 600;
        font-size: 0.9rem;
        color: #ff69b4;
    }

    /* ── JSON display block ── */
    .context-json {
        font-family: monospace;
        font-size: 0.8rem;
        background: #fff0f5;
        border: 1px dashed #ffb6c1;
        border-radius: 15px;
        padding: 1rem 1.2rem;
        overflow-x: auto;
        white-space: pre-wrap;
        word-break: break-word;
        color: #d1495b;
        line-height: 1.65;
        margin-top: 0.5rem;
    }

    hr { border-color: #ffb6c1 !important; border-style: dashed; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 — SESSION STATE INITIALISATION
# ─────────────────────────────────────────────────────────────────────────────

if "messages"       not in st.session_state:
    st.session_state.messages      = []

if "model"          not in st.session_state:
    st.session_state.model         = DEFAULT_MODEL

if "decoding"       not in st.session_state:
    st.session_state.decoding      = DEFAULT_DECODING.copy()

if "persona_name"   not in st.session_state:
    st.session_state.persona_name  = list(PERSONAS.keys())[0]

if "custom_prompt"  not in st.session_state:
    st.session_state.custom_prompt = ""

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4 — PURE HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def estimate_tokens(messages: list[dict]) -> int:
    char_count       = sum(len(m.get("content", "")) for m in messages)
    message_overhead = len(messages) * 4
    return (char_count // CHARS_PER_TOKEN) + message_overhead

def build_request_messages(history: list[dict], system_prompt: str) -> list[dict]:
    if system_prompt.strip():
        return [{"role": "system", "content": system_prompt}] + history
    return list(history)

def get_active_system_prompt() -> str:
    name = st.session_state.persona_name
    if name == "  Custom (edit below)":
        return st.session_state.custom_prompt
    return PERSONAS[name]["prompt"]

def stream_ollama_response(messages: list[dict], model: str, decoding: dict) -> Iterator[str]:
    stream = ollama.chat(
        model=model,
        messages=messages,
        stream=True,
        options={
            "temperature": decoding["temperature"],
            "top_p":       decoding["top_p"],
            "num_predict": decoding["max_tokens"],
        },
    )
    for chunk in stream:
        token = chunk["message"]["content"]
        if token: 
            yield token

def render_token_bar(used: int, limit: int) -> None:
    pct = min(round(used / limit * 100, 1), 100.0)
    st.markdown(
        f'<div class="token-bar-bg">'
        f'<div class="token-bar-fill" style="width:{pct}%"></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5 — SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(f"## {APP_TITLE}")
    st.caption("NLP mechanics explorer - local inference via Ollama")
    st.divider()

    st.markdown('<p class="section-label">1. Model</p>', unsafe_allow_html=True)
    try:
        available_models = [m.model for m in ollama.list().models]
    except Exception:
        available_models = [DEFAULT_MODEL, "mistral", "gemma3", "phi3"]

    if st.session_state.model not in available_models:
        st.session_state.model = available_models[0] if available_models else DEFAULT_MODEL

    st.session_state.model = st.selectbox(
        "model_select",
        options=available_models,
        index=available_models.index(st.session_state.model),
        help="Run `ollama pull <name>` to add models.",
        label_visibility="collapsed",
    )
    st.divider()

    st.markdown('<p class="section-label">2. Linguistic Persona</p>', unsafe_allow_html=True)
    persona_keys = list(PERSONAS.keys())
    prior_idx    = persona_keys.index(st.session_state.persona_name) if st.session_state.persona_name in persona_keys else 0

    selected_persona = st.selectbox(
        "persona_select",
        options=persona_keys,
        index=prior_idx,
        label_visibility="collapsed",
        help="Each option is a different system prompt injected as role='system'."
    )
    st.session_state.persona_name = selected_persona

    st.markdown(
        f'<div class="persona-note">{PERSONAS[selected_persona]["description"]}</div>',
        unsafe_allow_html=True,
    )

    if selected_persona == "  Custom (edit below)":
        st.session_state.custom_prompt = st.text_area(
            "custom_prompt_input",
            value=st.session_state.custom_prompt,
            height=110,
            placeholder="You are a...",
            label_visibility="collapsed",
        )
    else:
        with st.expander("View active system prompt", expanded=False):
            st.code(PERSONAS[selected_persona]["prompt"], language=None)

    st.divider()

    st.markdown('<p class="section-label">3. Decoding Parameters</p>', unsafe_allow_html=True)
    temperature = st.slider(
        "Temperature",
        min_value=0.0, max_value=2.0,
        value=st.session_state.decoding["temperature"],
        step=0.05,
    )
    top_p = st.slider(
        "Top-P",
        min_value=0.0, max_value=1.0,
        value=st.session_state.decoding["top_p"],
        step=0.05,
    )
    max_tokens = st.slider(
        "Max new tokens",
        min_value=64, max_value=4096,
        value=st.session_state.decoding["max_tokens"],
        step=64,
    )

    st.session_state.decoding = {
        "temperature": temperature,
        "top_p":       top_p,
        "max_tokens":  max_tokens,
    }

    if temperature <= 0.25 and top_p <= 0.25:
        regime_label, regime_color = "Deterministic / Greedy", "#d1495b"
    elif temperature >= 1.4 or top_p >= 0.97:
        regime_label, regime_color = "High Entropy / Creative", "#ff82ab"
    else:
        regime_label, regime_color = "Balanced Sampling", "#ff69b4"

    st.markdown(
        f"<p style='font-size:0.75rem;font-weight:600;"
        f"color:{regime_color};margin-top:4px;'>* {regime_label}</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    st.markdown('<p class="section-label">4. Context Window</p>', unsafe_allow_html=True)
    active_system    = get_active_system_prompt()
    full_payload     = build_request_messages(st.session_state.messages, active_system)
    estimated_tokens = estimate_tokens(full_payload)
    pct_used         = estimated_tokens / CONTEXT_WINDOW_ESTIMATE * 100

    c1, c2 = st.columns(2)
    c1.metric("Est. tokens",  f"{estimated_tokens:,}")
    c2.metric("% of 8k",      f"{pct_used:.1f}%")

    render_token_bar(estimated_tokens, CONTEXT_WINDOW_ESTIMATE)
    st.caption("1 token is around 4 chars.")
    st.divider()

    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.caption(f"{len(st.session_state.messages)} messages in history")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6 — MAIN PANEL HEADER
# ─────────────────────────────────────────────────────────────────────────────

st.markdown(f"## {APP_TITLE}")
st.caption(
    f"Model: **{st.session_state.model}** | "
    f"Persona: **{selected_persona.split('  ')[-1]}** | "
    f"Temperature = **{temperature}** | Top-P = **{top_p}**"
)
st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 7 — CHAT HISTORY RENDER
# ─────────────────────────────────────────────────────────────────────────────

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 8 — CHAT INPUT AND RESPONSE GENERATION
# ─────────────────────────────────────────────────────────────────────────────

if prompt := st.chat_input("Send a message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            request_payload = build_request_messages(
                st.session_state.messages,
                get_active_system_prompt(),
            )
            full_response = st.write_stream(
                stream_ollama_response(
                    messages=request_payload,
                    model=st.session_state.model,
                    decoding=st.session_state.decoding,
                )
            )
        except Exception as exc:
            full_response = (
                f"Ollama error: `{exc}`\n\n"
                "Checklist:\n"
                "1. Is Ollama running? Run `ollama serve`\n"
                f"2. Is the model pulled? Run `ollama pull {st.session_state.model}`\n"
                "3. Is the server at `localhost:11434`?"
            )
            st.error(full_response)

    st.session_state.messages.append(
        {"role": "assistant", "content": full_response}
    )

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 9 — CONTEXT WINDOW INSPECTOR (NLP Debugger)
# ─────────────────────────────────────────────────────────────────────────────

st.divider()

with st.expander("Context Window Inspector", expanded=False):
    debug_payload  = build_request_messages(st.session_state.messages, get_active_system_prompt())
    debug_tokens   = estimate_tokens(debug_payload)

    db1, db2, db3, db4 = st.columns(4)
    db1.metric("Messages",  len(debug_payload))
    db2.metric("Tokens",     f"{debug_tokens:,}")
    db3.metric("Remaining",  f"{max(0, CONTEXT_WINDOW_ESTIMATE - debug_tokens):,}")
    db4.metric("Regime",      regime_label)

    st.markdown(
        """
        <p style="font-size:0.85rem;color:#ff82ab;margin:0.6rem 0 0.3rem 0;line-height:1.6;">
        The JSON array below is the <strong>exact payload</strong> sent to the model on the
        next request. There is no hidden memory!
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<pre class="context-json">{json.dumps(debug_payload, indent=2, ensure_ascii=False)}</pre>',
        unsafe_allow_html=True,
    )

    st.markdown(
        "<p style='font-size:0.8rem;font-weight:600;color:#ff82ab;margin-top:1.2rem;margin-bottom:0.2rem;'>"
        "Active generation options:</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<pre class="context-json">'
        f'{json.dumps({"model": st.session_state.model, "options": {"temperature": temperature, "top_p": top_p, "num_predict": max_tokens}}, indent=2)}'
        f'</pre>',
        unsafe_allow_html=True,
    )