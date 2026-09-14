"""Audio-to-lyrics transcription engine with free online Hugging Face Inference and local Whisper fallback."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

# Safe Windows UTF-8 console output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


class SunoAudioTranscriber:
    """Transcribes song audio into formatted lyrics using free online inference or local Whisper."""

    def __init__(self, transcripts_dir: str | Path = "output/transcripts") -> None:
        self.transcripts_dir = Path(transcripts_dir)
        self.transcripts_dir.mkdir(parents=True, exist_ok=True)

    def transcribe(
        self,
        audio_path: str | Path,
        song_id: str = "",
        *,
        hf_token: str | None = None,
        model_size: str = "base",
        existing_prompt_lyrics: str = "",
    ) -> dict[str, Any]:
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")

        token = hf_token or os.environ.get("HF_TOKEN") or ""
        transcript_text = ""
        engine_used = ""

        # Strategy 1: Free Online Inference API (Hugging Face Whisper)
        if token:
            print("[*] Attempting free online Hugging Face Whisper inference (openai/whisper-large-v3-turbo)...")
            try:
                from huggingface_hub import InferenceClient

                client = InferenceClient(token=token)
                with open(path, "rb") as f:
                    data = f.read()
                result = client.automatic_speech_recognition(data, model="openai/whisper-large-v3-turbo")
                if isinstance(result, dict):
                    transcript_text = result.get("text", "")
                elif isinstance(result, str):
                    transcript_text = result
                else:
                    transcript_text = getattr(result, "text", str(result))
                engine_used = "hf_serverless_whisper_large_v3_turbo"
                print(f"[+] Online transcription completed successfully!")
            except Exception as e:
                print(f"[!] Online HF Inference API note: {e}. Falling back to local high-speed Whisper...")

        detected_lang = "en"
        translated_text = ""

        # Strategy 2: Local faster-whisper inference (free, fast, runs locally on CPU)
        if not transcript_text:
            print(f"[*] Running local faster-whisper ({model_size}) inference on {path.name}...")
            try:
                from faster_whisper import WhisperModel

                model = WhisperModel(model_size, device="cpu", compute_type="int8")
                segments, info = model.transcribe(str(path), beam_size=3)
                lines: list[str] = []
                for s in segments:
                    seg_text = s.text.strip()
                    if seg_text:
                        lines.append(seg_text)
                transcript_text = "\n".join(lines)
                detected_lang = getattr(info, "language", "en") or "en"
                engine_used = f"local_faster_whisper_{model_size}"
                print(f"[+] Local Whisper completed: {len(lines)} vocal segments identified (language={detected_lang}).")

                # If non-English vocals detected, run translation pass
                if detected_lang not in ("en", "english") and len(lines) > 0:
                    print(f"[*] Translating vocal audio from [{detected_lang.upper()}] to English...")
                    try:
                        trans_segments, _ = model.transcribe(str(path), beam_size=3, task="translate")
                        t_lines = [s.text.strip() for s in trans_segments if s.text.strip()]
                        translated_text = "\n".join(t_lines)
                        print(f"[+] Vocal translation complete: {len(t_lines)} lines translated.")
                    except Exception as te:
                        print(f"[!] Translation note: {te}")
            except Exception as e:
                print(f"[!] Local Whisper engine note: {e}")

        # Strategy 3: Align with existing prompt metadata if available
        final_lyrics = self._format_as_lyrics(
            transcript_text,
            existing_prompt=existing_prompt_lyrics,
            translated_text=translated_text,
            detected_lang=detected_lang,
        )

        sid = song_id or path.stem
        out_txt = self.transcripts_dir / f"{sid}_lyrics.txt"
        out_json = self.transcripts_dir / f"{sid}_transcript.json"

        out_txt.write_text(final_lyrics, encoding="utf-8")
        meta = {
            "song_id": sid,
            "audio_file": str(path),
            "engine": engine_used,
            "language": detected_lang,
            "raw_transcription": transcript_text,
            "translated_transcription": translated_text,
            "formatted_lyrics": final_lyrics,
        }
        out_json.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[+] Saved lyric transcript -> {out_txt}")

        return {
            "lyrics": final_lyrics,
            "raw_text": transcript_text,
            "translated_text": translated_text,
            "language": detected_lang,
            "engine": engine_used,
            "txt_path": out_txt,
            "json_path": out_json,
        }

    def _format_as_lyrics(
        self,
        raw_transcript: str,
        existing_prompt: str = "",
        translated_text: str = "",
        detected_lang: str = "en",
    ) -> str:
        """Format raw text into structured song sections with verse/chorus/bridge/outro tags."""
        # If creator provided structured prompt lyrics, preserve them
        if existing_prompt and len(existing_prompt.strip().splitlines()) >= 4:
            if any(tag in existing_prompt.lower() for tag in ("[verse", "[chorus", "[hook", "[bridge", "[intro", "[outro")):
                return existing_prompt.strip()

        clean = (raw_transcript or existing_prompt or "").strip()
        if not clean:
            return "[Verse]\n(Instrumental / No vocal transcription detected)"

        def _chunk_lines(text: str) -> list[str]:
            raw_lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
            if not raw_lines:
                raw_lines = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
            sections = [
                "Intro", "Verse 1", "Pre-Chorus", "Chorus",
                "Verse 2", "Chorus", "Bridge", "Hook",
                "Verse 3", "Chorus", "Outro"
            ]
            chunk_size = 4
            blocks: list[str] = []
            for i in range(0, len(raw_lines), chunk_size):
                idx = i // chunk_size
                sec_title = sections[idx] if idx < len(sections) else f"Verse {idx - 2}"
                stanza = "\n".join(raw_lines[i : i + chunk_size])
                blocks.append(f"[{sec_title}]\n{stanza}")
            return blocks

        formatted_main = "\n\n".join(_chunk_lines(clean))

        if translated_text and translated_text.strip() != clean:
            formatted_trans = "\n\n".join(_chunk_lines(translated_text.strip()))
            return (
                f"[Original Lyrics ({detected_lang.upper()})]\n"
                f"{formatted_main}\n\n"
                f"[English Translation]\n"
                f"{formatted_trans}"
            )

        return formatted_main


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python -m src.transcriber <audio_file_path> [song_id]")
        return 1
    audio_path = sys.argv[1]
    sid = sys.argv[2] if len(sys.argv) > 2 else ""
    t = SunoAudioTranscriber()
    res = t.transcribe(audio_path, song_id=sid)
    print("\n--- TRANSCRIBED LYRICS ---\n")
    print(res["lyrics"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
