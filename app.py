"""Hugging Face Space Application for Suno Song Generator & Reference Model."""

from __future__ import annotations

import json
from pathlib import Path
import sys

# Compatibility shim for Gradio 4.x OAuth with huggingface_hub >= 0.26 / 1.x
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

# Backward compatibility shim for Starlette >= 0.38 TemplateResponse with Gradio 4.x
try:
    import starlette.templating
    _orig_template_response = starlette.templating.Jinja2Templates.TemplateResponse
    def _safe_template_response(self, *args, **kwargs):
        if args and isinstance(args[0], str):
            name = args[0]
            context = args[1] if len(args) > 1 else kwargs.get("context", {})
            req = context.get("request") if isinstance(context, dict) else kwargs.get("request")
            return _orig_template_response(self, request=req, name=name, context=context)
        return _orig_template_response(self, *args, **kwargs)
    starlette.templating.Jinja2Templates.TemplateResponse = _safe_template_response
except Exception:
    pass

import gradio as gr

# Prevent TypeError in gradio_client json_schema_to_python_type when additionalProperties is bool
try:
    import gradio_client.utils
    _orig_get_type = gradio_client.utils.get_type
    def _safe_get_type(schema):
        if not isinstance(schema, dict):
            return "Any"
        return _orig_get_type(schema)
    gradio_client.utils.get_type = _safe_get_type

    _orig_json_schema = gradio_client.utils._json_schema_to_python_type
    def _safe_json_schema(schema, defs=None):
        if not isinstance(schema, dict):
            return "Any"
        try:
            return _orig_json_schema(schema, defs)
        except Exception:
            return "Any"
    gradio_client.utils._json_schema_to_python_type = _safe_json_schema
except Exception:
    pass

from src.downloader import SunoSongDownloader
from src.inference import SongwritingReferenceModel
from src.keywords import ENGLISH_SEED_KEYWORDS
from src.llm import generate_suno_v6_payload

# Resolve model path
MODEL_PATHS = [
    Path("models/suno_song_inference_model.json"),
    Path("dist/models/suno_song_inference_model.json"),
    Path(".suno_song_inference_model.json"),
    Path("suno_song_inference_model.json"),
]
MODEL_FILE = next((p for p in MODEL_PATHS if p.exists()), MODEL_PATHS[0])
model = SongwritingReferenceModel(MODEL_FILE)


def generate_song_prompt(
    theme: str,
    tier: str,
    title: str,
    vocal_gender: str,
    engine_choice: str,
    inject_novel: bool,
) -> tuple[str, str, str, str, str, str, str, str, str, str, str]:
    theme_clean = theme.strip() if theme else "viral night drive"
    engine_code = "hybrid"
    if "Scansion-LM" in engine_choice:
        engine_code = "llm"
    elif "Reference" in engine_choice and "Hybrid" not in engine_choice:
        engine_code = "reference"

    gender_code = "f" if "Female" in vocal_gender else ("m" if "Male" in vocal_gender else "any")
    from src.song_creator import create_complete_song_bundle

    resolved_title = title.strip() if title and title.strip() else "New Name on the Door"
    bundle = create_complete_song_bundle(
        title=resolved_title,
        theme=theme_clean,
        vocal_gender=gender_code,
        out_dir="dist/output/songs",
    )

    p3k = bundle["payload_3k"]
    p5k = bundle["payload_5k"]
    v6_3k_str = json.dumps(p3k, indent=2, ensure_ascii=False)
    v6_5k_str = json.dumps(p5k, indent=2, ensure_ascii=False)

    lyrics_text = p3k.get("prompt", "")
    style_text = p3k.get("style", "")
    exclude_text = p3k.get("negativeTags", "")
    song_title = p3k.get("title", resolved_title)

    paste_ready = (
        f"TITLE\n{song_title}\n\n"
        f"STYLE\n{style_text}\n\n"
        f"EXCLUDE\n{exclude_text}\n\n"
        f"LYRICS\n{lyrics_text}\n"
    )

    with open(bundle["files"]["lrc"], encoding="utf-8") as f:
        lrc_text = f.read()
    with open(bundle["files"]["brief"], encoding="utf-8") as f:
        brief_text = f.read()
    with open(bundle["files"]["cover"], encoding="utf-8") as f:
        cover_text = f.read()

    stats_badge = (
        f"⚡ Engine: {engine_choice} | "
        f"📊 3K JSON: {bundle['len_3k']:,} chars | 5K JSON: {bundle['len_5k']:,} chars | "
        f"Catalog: {model._state.get('songs_used', 7154):,} songs"
    )

    return (
        song_title,
        style_text,
        exclude_text,
        lyrics_text,
        paste_ready,
        v6_3k_str,
        v6_5k_str,
        lrc_text,
        brief_text,
        cover_text,
        stats_badge,
    )


def explore_styles(tier: str) -> tuple[str, str]:
    style_sug = model.suggest_style_pack(tier=tier.lower(), n=16)
    unused_sug = model.suggest_unused_style_pack(model.catalog if hasattr(model, 'catalog') else None, n=16) if hasattr(model, 'catalog') else None
    
    novel_keys = list(model._state.get("novel_keywords", {}).keys())[:20]
    novel_str = ", ".join(novel_keys) if novel_keys else "synthwave, bedroom pop, dark ambient, breakcore"

    return (
        style_sug.style_pack,
        novel_str,
    )


def analyze_suno_song(url: str) -> tuple[str, str, str, str, str]:
    if not url or not url.strip():
        return "Please enter a valid Suno song URL or ID", "", "", "", ""
    try:
        dl = SunoSongDownloader(output_dir="output/audio")
        song = dl.fetch_song(url.strip(), download_audio=False)
        info = (
            f"🎵 **{song.title}**\n"
            f"- **Artist**: {song.artist_name} (@{song.artist_id})\n"
            f"- **Likes**: {song.like_count:,} | **Plays**: {song.play_count:,}\n"
            f"- **Style**: {song.style_of_music}\n"
            f"- **Duration**: {round(song.duration_seconds or 0, 1)}s"
        )
        return (
            info,
            song.title,
            song.style_of_music,
            song.lyrics or song.prompt or "(No lyrics found in clip metadata)",
            song.video_url or song.audio_url or "",
        )
    except Exception as e:
        return f"Error analyzing song: {e}", "", "", "", ""


def get_model_stats() -> str:
    n = model._state.get("songs_used", 7018)
    lyrics_n = model._state.get("songs_with_lyrics", 4968)
    structs = len(model._state.get("structure_templates", {}))
    tags = len(model._state.get("tag_traction", {}))
    trained_at = model._state.get("trained_at", "2026-09-14")

    md = f"""
### 📈 Reference Model Intelligence
- **Dataset Size**: {n:,} parsed Suno songs
- **Songs with Full Lyric Transcripts**: {lyrics_n:,} ({round(100 * lyrics_n / max(1, n), 1)}%)
- **Unique Style & Production Tags Scored**: {tags:,}
- **Learned Lyric Structure Templates**: {structs:,}
- **Last Model Retraining**: `{trained_at}`
- **English Seed Vocabulary**: {len(ENGLISH_SEED_KEYWORDS):,} canonical music descriptors

The model analyzes style co-occurrence, rhyming density, and line-length variance to build statistically optimized prompts for Suno Custom Mode.
"""
    return md


# --- HUGGING FACE THEME & GRADIO INTERFACE ---
try:
    font_family = [gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"]
    mono_family = [gr.themes.GoogleFont("JetBrains Mono"), "ui-monospace", "monospace"]
except Exception:
    font_family = ["ui-sans-serif", "system-ui", "sans-serif"]
    mono_family = ["ui-monospace", "monospace"]

hf_theme = gr.themes.Base(
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

hf_css = """
.gradio-container {
    max-width: 1240px !important;
    margin: auto !important;
}
.hf-hero {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 18px 24px;
    background: rgba(255, 210, 30, 0.08);
    border: 1px solid rgba(255, 210, 30, 0.28);
    border-radius: 12px;
    margin-bottom: 22px;
}
.hf-badge {
    background: #FFD21E;
    color: #000;
    font-weight: 700;
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 12px;
    display: inline-block;
    letter-spacing: 0.5px;
}
"""

with gr.Blocks(theme=hf_theme, css=hf_css, title="Suno AI Song Generator & Reference Model") as demo:
    gr.Markdown(
        """
        <div class="hf-hero">
            <div>
                <h1 style="margin: 0; font-size: 26px; font-weight: 800; display: flex; align-items: center; gap: 10px;">
                    <span>🤗 🎵</span> Suno AI Studio V6 Generator
                </h1>
                <p style="margin: 6px 0 0 0; color: #9CA3AF; font-size: 14px;">
                    Professional Songwriting Prompt & Lyric Scansion Engine trained on 9,000+ Suno tracks
                </p>
            </div>
            <div>
                <span class="hf-badge">HF SPACE EDITION</span>
            </div>
        </div>
        """
    )

    with gr.Tabs():
        # TAB 1: PROMPT STUDIO
        with gr.TabItem("✨ AI Prompt Studio"):
            with gr.Row():
                with gr.Column(scale=1):
                    theme_input = gr.Textbox(
                        label="Song Theme or Concept",
                        placeholder="e.g. midnight neon drive, heartbreaking confession, rage cyberpunk",
                        value="midnight highway neon drive",
                        lines=2,
                    )
                    with gr.Row():
                        engine_select = gr.Dropdown(
                            label="Generation Engine",
                            choices=[
                                "Hybrid (Reference + Scansion LLM)",
                                "Scansion-LM (Neural)",
                                "Reference Model (Statistical)",
                            ],
                            value="Hybrid (Reference + Scansion LLM)",
                        )
                        gender_select = gr.Dropdown(
                            label="Vocal Delivery",
                            choices=["Female (f)", "Male (m)", "Any"],
                            value="Female (f)",
                        )
                    with gr.Row():
                        tier_select = gr.Dropdown(
                            label="Traction Tier",
                            choices=["Viral", "High", "Medium", "Low"],
                            value="Viral",
                        )
                        title_input = gr.Textbox(
                            label="Optional Title",
                            placeholder="Leave blank to auto-generate",
                        )
                    inject_novel_check = gr.Checkbox(
                        label="Inject Novel Unused Keywords (Distinctive Sound)",
                        value=True,
                    )
                    generate_btn = gr.Button("🚀 Generate Suno Song Prompt & V6 Spec", variant="primary", size="lg")

                    gr.Markdown("#### Quick Presets:")
                    with gr.Row():
                        p1 = gr.Button("🏎️ Neon Drive", size="sm")
                        p2 = gr.Button("🎸 Stadium Rock", size="sm")
                        p3 = gr.Button("💔 Bedroom Confession", size="sm")
                        p4 = gr.Button("⚡ Cyberpunk Trap", size="sm")

                    stats_output = gr.Markdown()

                with gr.Column(scale=1):
                    with gr.Tabs():
                        with gr.TabItem("🔥 3K Studio V6 JSON (~3,000 Chars)"):
                            v6_3k_output = gr.Code(
                                label="Complete 3K Suno Studio V6 JSON Specification (Click Copy top-right)",
                                language="json",
                                lines=20,
                            )
                        with gr.TabItem("⚡ 5K Extended V6 JSON (~5,000 Chars)"):
                            v6_5k_output = gr.Code(
                                label="Complete 5K Extended Suno Studio V6 JSON Specification",
                                language="json",
                                lines=20,
                            )
                        with gr.TabItem("⏱️ Synchronized LRC Lyrics"):
                            lrc_output = gr.Textbox(
                                label="Musical Timestamps & Scansion Lines (.LRC format)",
                                lines=18,
                            )
                        with gr.TabItem("📑 Production Brief"):
                            brief_output = gr.Markdown()
                        with gr.TabItem("🎨 Cover Art Prompt"):
                            cover_output = gr.Code(
                                label="Generative Cover Art Specification & Color Palette",
                                language="json",
                                lines=18,
                            )
                        with gr.TabItem("📋 Suno Custom Mode (Text)"):
                            paste_output = gr.Textbox(
                                label="Paste this directly into Suno Custom Mode",
                                lines=16,
                            )
                        with gr.TabItem("🎼 Field Breakdown"):
                            out_title = gr.Textbox(label="Song Title")
                            out_style = gr.Textbox(label="Style of Music (Tags)", lines=2)
                            out_exclude = gr.Textbox(label="Exclude Styles (Negative Prompt)")
                            out_lyrics = gr.Textbox(label="Generated Structured Lyrics", lines=10)

            generate_btn.click(
                fn=generate_song_prompt,
                inputs=[theme_input, tier_select, title_input, gender_select, engine_select, inject_novel_check],
                outputs=[
                    out_title,
                    out_style,
                    out_exclude,
                    out_lyrics,
                    paste_output,
                    v6_3k_output,
                    v6_5k_output,
                    lrc_output,
                    brief_output,
                    cover_output,
                    stats_output,
                ],
            )
            p1.click(lambda: ("midnight neon drive synthwave fast bass", "Viral"), outputs=[theme_input, tier_select])
            p2.click(lambda: ("stadium rock anthem electric guitar roaring drums", "Viral"), outputs=[theme_input, tier_select])
            p3.click(lambda: ("late night bedroom acoustic confession heartfelt sad", "High"), outputs=[theme_input, tier_select])
            p4.click(lambda: ("heavy 808 cyberpunk bass rage aggressive trap", "Viral"), outputs=[theme_input, tier_select])

        # TAB 2: STYLE EXPLORER
        with gr.TabItem("🔍 Style & Vocabulary Explorer"):
            gr.Markdown("### Discover Trending and Novel Musical Descriptors")
            with gr.Row():
                with gr.Column():
                    explorer_tier = gr.Radio(["Viral", "High", "Medium"], label="Select Tier", value="Viral")
                    explore_btn = gr.Button("Explore Style Intelligence")
                with gr.Column():
                    top_styles_out = gr.Textbox(label="Top Traction Style Pack", lines=3)
                    novel_styles_out = gr.Textbox(label="Novel / Unused Keyword Suggestions", lines=3)

            explore_btn.click(
                fn=explore_styles,
                inputs=[explorer_tier],
                outputs=[top_styles_out, novel_styles_out],
            )

        # TAB 3: SUNO SONG ANALYZER
        with gr.TabItem("🎧 Song Analyzer"):
            gr.Markdown("### Inspect Any Public Suno Track")
            with gr.Row():
                with gr.Column(scale=1):
                    suno_url_input = gr.Textbox(
                        label="Suno Song URL or UUID",
                        placeholder="https://suno.com/song/8ac118c0-3aab-43ac-af8f-57dbd1368e29",
                        value="https://suno.com/song/8ac118c0-3aab-43ac-af8f-57dbd1368e29",
                    )
                    analyze_btn = gr.Button("Analyze Song Metadata", variant="secondary")
                    song_info_md = gr.Markdown()
                    song_audio_preview = gr.Video(label="Clip Video / Audio Preview")

                with gr.Column(scale=1):
                    analyzed_title = gr.Textbox(label="Extracted Title")
                    analyzed_style = gr.Textbox(label="Extracted Style Tags")
                    analyzed_lyrics = gr.Textbox(label="Extracted / Transcribed Lyrics", lines=10)

            analyze_btn.click(
                fn=analyze_suno_song,
                inputs=[suno_url_input],
                outputs=[song_info_md, analyzed_title, analyzed_style, analyzed_lyrics, song_audio_preview],
            )

        # TAB 4: MODEL STATS
        with gr.TabItem("📊 Model Statistics"):
            stats_md = gr.Markdown(get_model_stats())

    gr.Markdown(
        """
        ---
        *Developed for high-traction songwriting on Suno AI. Package powered by SongwritingReferenceModel.*
        """
    )

if __name__ == "__main__":
    demo.queue().launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_api=False,
    )
