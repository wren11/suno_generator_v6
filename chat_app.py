"""SunoGPT Chat Interface: Standalone ChatGPT-style web application for Suno AI and Scansion-LM."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure paths
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_ROOT.parent) not in sys.path:
    sys.path.insert(0, str(_ROOT.parent))

# Shims for Gradio 4.x/6.x compatibility
try:
    import huggingface_hub
    if not hasattr(huggingface_hub, "HfFolder"):
        class _HfFolderShim:
            @staticmethod
            def get_token():
                try:
                    return getattr(huggingface_hub, "get_token", lambda: None)()
                except Exception:
                    return None
            @staticmethod
            def save_token(token):
                pass
            @staticmethod
            def delete_token():
                pass
        huggingface_hub.HfFolder = _HfFolderShim
except Exception:
    pass

import gradio as gr
from src.chat_engine import SunoChatEngine

# Initialize engine
engine = SunoChatEngine()
stats = engine.get_stats_summary()

# Styling
try:
    font_family = [gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"]
    mono_family = [gr.themes.GoogleFont("JetBrains Mono"), "ui-monospace", "monospace"]
except Exception:
    font_family = ["ui-sans-serif", "system-ui", "sans-serif"]
    mono_family = ["ui-monospace", "monospace"]

chat_theme = gr.themes.Base(
    primary_hue=gr.themes.colors.amber,
    secondary_hue=gr.themes.colors.slate,
    neutral_hue=gr.themes.colors.slate,
    font=font_family,
    font_mono=mono_family,
).set(
    body_background_fill="*neutral_950",
    body_background_fill_dark="*neutral_950",
    button_primary_background_fill="linear-gradient(135deg, #FFD21E 0%, #FF9D00 100%)",
    button_primary_background_fill_hover="linear-gradient(135deg, #FFE066 0%, #FFB020 100%)",
    button_primary_text_color="#000000",
    button_primary_text_color_dark="#000000",
    button_primary_border_color="#F59E0B",
    block_title_text_weight="600",
    block_border_width="1px",
    block_shadow="none",
)

custom_css = """
.gradio-container {
    max-width: 1180px !important;
    margin: auto !important;
}
.chat-hero {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 22px;
    background: rgba(255, 210, 30, 0.08);
    border: 1px solid rgba(255, 210, 30, 0.25);
    border-radius: 12px;
    margin-bottom: 14px;
}
.chat-badge {
    background: #FFD21E;
    color: #000;
    font-weight: 700;
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 12px;
    letter-spacing: 0.5px;
}
"""

def chat_stream(message, history, engine_mode, persona, temperature):
    for chunk in engine.generate_response(
        message=message,
        history=history,
        engine_mode=engine_mode,
        temperature=temperature,
        system_persona=persona,
    ):
        yield chunk

demo = gr.Blocks(title="SunoGPT Studio — AI Music Producer & Scansion Chat")

with demo:
    gr.Markdown(
        f"""
        <div class="chat-hero">
            <div>
                <h1 style="margin: 0; font-size: 24px; font-weight: 800; display: flex; align-items: center; gap: 10px;">
                    <span>🤖 🎵</span> SunoGPT Studio
                </h1>
                <p style="margin: 4px 0 0 0; color: #9CA3AF; font-size: 13px;">
                    Conversational AI Songwriting Assistant powered by Scansion-LM and <b>{stats['songs_used']:,}</b> Suno Songs
                </p>
            </div>
            <div>
                <span class="chat-badge">🧠 100% LOCAL NEURAL &amp; REFERENCE</span>
            </div>
        </div>
        """
    )

    additional_inputs = [
        gr.Dropdown(
            label="🧠 Model Engine",
            choices=[
                "Hybrid AI Producer (Recommended)",
                "Scansion-LM (Neural Local LM)",
                "Reference Model (Statistical Data)",
            ],
            value="Hybrid AI Producer (Recommended)",
            info="Powered 100% locally by Scansion-LM and 21k-song Reference Model (Zero external AI).",
        ),
        gr.Dropdown(
            label="🎭 Producer Persona",
            choices=[
                "SunoGPT Hit Producer",
                "Gen-Z Rapper / Artist",
                "Technical Suno V6 Architect",
                "Scansion and Lyric Poet",
            ],
            value="SunoGPT Hit Producer",
            info="Tailors the tone, vocabulary, and lyric delivery style.",
        ),
        gr.Slider(
            label="🔥 Creativity (Temperature)",
            minimum=0.1,
            maximum=1.4,
            value=0.75,
            step=0.05,
            info="Higher values produce more creative & diverse lyric rhymes.",
        ),
    ]

    example_list = [
        ["🔥 Write a viral cyberpunk synthwave song with full 3K Suno V6 specs", "Hybrid AI Producer (Recommended)", "SunoGPT Hit Producer", 0.75],
        ["📊 What are the highest traction tags and openings in the 21k song catalog?", "Reference Model (Statistical Data)", "SunoGPT Hit Producer", 0.75],
        ["🎤 Continue these lyrics: [Verse 1] Rain on the glass, neon reflections pass...", "Scansion-LM (Neural Local LM)", "Scansion and Lyric Poet", 0.85],
        ["✨ Give me 5 novel tag fusions that will stand out on Suno explore", "Reference Model (Statistical Data)", "SunoGPT Hit Producer", 0.75],
        ["💔 Help me write a heartbreaking acoustic bedroom pop confession", "Hybrid AI Producer (Recommended)", "SunoGPT Hit Producer", 0.75],
    ]

    chat_interface = gr.ChatInterface(
        fn=chat_stream,
        additional_inputs=additional_inputs,
        additional_inputs_accordion=gr.Accordion("⚙️ Producer Controls & Engine Settings", open=False),
        examples=example_list,
        chatbot=gr.Chatbot(height=620, layout="bubble"),
        autofocus=True,
    )

    gr.Markdown(
        f"""
        <div style="text-align: center; color: #6B7280; font-size: 12px; margin-top: 14px;">
            SunoGPT Studio | Catalog: {stats['songs_used']:,} songs | Scored Tags: {stats['tag_count']:,} | Scansion Model: {Path(stats['scansion_model']).name}
        </div>
        """
    )

def launch(server_port=7861):
    launch_kw = {"server_name": "0.0.0.0", "server_port": server_port}
    try:
        demo.queue().launch(theme=chat_theme, css=custom_css, **launch_kw)
    except TypeError:
        demo.queue().launch(**launch_kw)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 7861))
    print(f"[*] Launching SunoGPT Chat Studio on http://localhost:{port} ...")
    launch(server_port=port)
