"""Loopback HTTP sidecar for Scansion-LM. Bind 127.0.0.1 only — Node proxies it."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import threading
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from .corpus import build_all, write_jsonl
from .eval_guide import eval_model, gold_sheet_score, score_sheet
from .export_bundle import export_ready
from .extract import extract_song
from .infer import infer_composer, ready
from .paths import FOUNDRY_HOST, FOUNDRY_PORT, METRICS, ROOT, STATUS, TRAIN_LOG, TRENDING_JSON, USER_EXTRACTS
from .tokenize import train_tokenizer
from .train import write_status

def _oom_adj(pid: int, value: int) -> None:
    try:
        path = f"/proc/{pid}/oom_score_adj"
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(str(value))
    except (OSError, FileNotFoundError):
        return


TRAIN_PROC: subprocess.Popen | None = None
INFER_LOCK = threading.Lock()
_TRAIN_STOPPED = False


def _read_status() -> dict:
    if not STATUS.exists():
        return {"phase": "idle", "training": False, "trained": ready()}
    try:
        data = json.loads(STATUS.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        data = {}
    data.setdefault("trained", ready())
    data.setdefault("training", False)
    data.setdefault("phase", "idle")
    return data


def _metrics(limit: int = 80) -> list[dict]:
    if not METRICS.exists():
        return []
    rows = []
    for line in METRICS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows[-limit:]


def _training_alive() -> bool:
    global TRAIN_PROC
    if TRAIN_PROC is not None and TRAIN_PROC.poll() is None:
        return True
    st = _read_status()
    pid = st.get("pid")
    if isinstance(pid, int) and pid > 1:
        try:
            os.kill(pid, 0)
            return bool(st.get("training"))
        except OSError:
            return False
    return bool(st.get("training")) and st.get("phase") not in ("ready", "error", "idle")


def _train_pgid() -> int | None:
    global TRAIN_PROC
    if TRAIN_PROC is not None and TRAIN_PROC.poll() is None:
        return TRAIN_PROC.pid
    st = _read_status()
    pid = st.get("pid")
    if isinstance(pid, int) and pid > 1:
        try:
            os.kill(pid, 0)
            return pid
        except OSError:
            return None
    return None


def _pause_train() -> bool:
    """Freeze the trainer so inference gets the CPU. Training resumes after."""
    global _TRAIN_STOPPED
    pgid = _train_pgid()
    if not pgid or not hasattr(signal, "SIGSTOP"):
        return False
    try:
        if hasattr(os, "killpg"):
            os.killpg(pgid, signal.SIGSTOP)
        else:
            os.kill(pgid, signal.SIGSTOP)
        _TRAIN_STOPPED = True
        return True
    except (ProcessLookupError, PermissionError, OSError):
        return False


def _resume_train() -> None:
    global _TRAIN_STOPPED
    if not _TRAIN_STOPPED:
        return
    pgid = _train_pgid()
    _TRAIN_STOPPED = False
    if not pgid or not hasattr(signal, "SIGCONT"):
        return
    try:
        if hasattr(os, "killpg"):
            os.killpg(pgid, signal.SIGCONT)
        else:
            os.kill(pgid, signal.SIGCONT)
    except (ProcessLookupError, PermissionError, OSError):
        pass


def _start_train(steps: int, corpus_n: int) -> dict:
    global TRAIN_PROC
    if _training_alive():
        return {"ok": True, "already": True, "status": _read_status()}
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    log_path = TRAIN_LOG if hasattr(TRAIN_LOG, "parent") else (ROOT / "runs" / "train.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log = open(log_path, "ab")
    popen_kwargs: dict[str, Any] = {
        "cwd": str(ROOT),
        "env": env,
        "stdout": log,
        "stderr": subprocess.STDOUT,
    }
    if sys.platform == "win32":
        popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        popen_kwargs["start_new_session"] = True

    TRAIN_PROC = subprocess.Popen(
        [sys.executable, "-m", "scansion_lm", "train", str(steps), str(corpus_n)],
        **popen_kwargs,
    )
    _oom_adj(TRAIN_PROC.pid, 400)
    write_status(phase="extract", training=True, error=None, pid=TRAIN_PROC.pid)
    return {"ok": True, "started": True, "pid": TRAIN_PROC.pid, "status": _read_status()}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args) -> None:  # noqa: A003
        return

    def _send(self, code: int, payload: dict | list) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        try:
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(raw)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            return

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        if not raw:
            return {}
        try:
            data = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in ("/health", "/"):
            st = _read_status()
            self._send(
                200,
                {
                    "ok": True,
                    "ready": ready(),
                    "phase": st.get("phase"),
                    "training": bool(st.get("training")),
                    "trained": bool(st.get("trained") or ready()),
                },
            )
            return
        if path == "/status":
            self._send(200, {"ok": True, **_read_status(), "ready": ready(), "infer_paused_train": _TRAIN_STOPPED})
            return
        if path == "/metrics":
            self._send(200, {"ok": True, "points": _metrics()})
            return
        if path == "/export":
            self._send(200, export_ready())
            return
        if path == "/trending":
            if TRENDING_JSON.exists():
                try:
                    learn = json.loads(TRENDING_JSON.read_text(encoding="utf-8"))
                    self._send(200, {"ok": True, "learn": learn})
                    return
                except json.JSONDecodeError:
                    pass
            self._send(200, {"ok": True, "learn": None})
            return
        self._send(404, {"ok": False, "error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        body = self._body()
        try:
            if path == "/extract":
                text = str(body.get("text") or "")
                if len(text.strip()) < 12:
                    self._send(400, {"ok": False, "error": "Paste original lyrics to extract."})
                    return
                ext = extract_song(text, title=str(body.get("title") or ""), source="user")
                scored = score_sheet(str(body.get("style") or ""), text)
                self._send(200, {"ok": True, "extract": ext, "guide": scored})
                return
            if path == "/trending":
                TRENDING_JSON.parent.mkdir(parents=True, exist_ok=True)
                TRENDING_JSON.write_text(json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8")
                songs = body.get("topSongs") or body.get("learn", {}).get("topSongs") if isinstance(body.get("learn"), dict) else body.get("topSongs")
                n = len(songs) if isinstance(songs, list) else 0
                self._send(200, {"ok": True, "saved": n})
                return
            if path == "/ingest-batch":
                songs = body.get("songs") or []
                ingested = 0
                skipped = 0
                existing: list = []
                if USER_EXTRACTS.exists():
                    for line in USER_EXTRACTS.read_text(encoding="utf-8").splitlines():
                        if line.strip():
                            existing.append(json.loads(line))
                seen = {(e.get("title") or "").lower() for e in existing}
                for song in songs:
                    if not isinstance(song, dict):
                        skipped += 1
                        continue
                    text = str(song.get("text") or song.get("prompt") or "").strip()
                    title = str(song.get("title") or "Suno extract")
                    if len(text) < 40:
                        skipped += 1
                        continue
                    if title.lower() in seen:
                        skipped += 1
                        continue
                    ext = extract_song(text, title=title, source="suno-trending")
                    ext["idea"] = f"Trending Suno · {song.get('plays') or 0} plays"
                    ext["style"] = str(song.get("style") or "")
                    existing.append(ext)
                    seen.add(title.lower())
                    ingested += 1
                write_jsonl(USER_EXTRACTS, existing)
                self._send(200, {"ok": True, "ingested": ingested, "skipped": skipped, "count": len(existing)})
                return
            if path == "/ingest":
                text = str(body.get("text") or "")
                if len(text.strip()) < 12:
                    self._send(400, {"ok": False, "error": "Nothing to ingest."})
                    return
                ext = extract_song(text, title=str(body.get("title") or "User extract"), source="user")
                ext["idea"] = str(body.get("idea") or "")
                ext["style"] = str(body.get("style") or "")
                existing = []
                if USER_EXTRACTS.exists():
                    for line in USER_EXTRACTS.read_text(encoding="utf-8").splitlines():
                        if line.strip():
                            existing.append(json.loads(line))
                existing.append(ext)
                write_jsonl(USER_EXTRACTS, existing)
                self._send(200, {"ok": True, "extract": ext, "count": len(existing)})
                return
            if path == "/build":
                info = build_all(int(body.get("n") or 640))
                tok = None
                try:
                    tok = str(train_tokenizer())
                except Exception as exc:
                    tok = f"skipped: {exc}"
                write_status(phase="corpus", training=False, **info, tokenizer=tok)
                self._send(200, {"ok": True, **info, "tokenizer": tok})
                return
            if path == "/train":
                steps = max(40, min(int(body.get("steps") or 300), 800))
                corpus_n = max(80, min(int(body.get("corpus_n") or 640), 1200))
                self._send(200, _start_train(steps, corpus_n))
                return
            if path == "/infer":
                composer = body.get("composer") or {}
                if not isinstance(composer, dict):
                    self._send(400, {"ok": False, "error": "composer required"})
                    return
                with INFER_LOCK:
                    paused = _pause_train()
                    try:
                        last_err = ""
                        gen = None
                        for attempt in range(4):
                            try:
                                gen = infer_composer(
                                    composer,
                                    live_style=str(body.get("liveStyle") or ""),
                                    dna=str(body.get("dna") or ""),
                                    iterate_hint=str(body.get("iterateHint") or ""),
                                    previous_lyrics=str(body.get("previousLyrics") or ""),
                                )
                                if gen and gen.get("lyrics"):
                                    break
                            except Exception as exc:
                                last_err = str(exc)
                                gen = None
                        if not gen:
                            self._send(500, {"ok": False, "error": last_err or "Checkpoint produced no sheet after retries."})
                            return
                        if paused:
                            gen["sunoNotes"] = list(gen.get("sunoNotes") or []) + [
                                "Trainer was paused for this sheet, then resumed."
                            ]
                        self._send(200, {"ok": True, "generation": gen})
                    finally:
                        _resume_train()
                return
            if path == "/eval":
                gold = gold_sheet_score()
                with INFER_LOCK:
                    paused = _pause_train()
                    try:
                        report = eval_model(n=int(body.get("n") or 3)) if ready() else {"ok": False, "error": "Model not trained"}
                    finally:
                        if paused:
                            _resume_train()
                self._send(200, {"ok": True, "gold": gold, "model": report})
                return
            if path == "/export":
                self._send(200, export_ready())
                return
        except Exception as exc:
            self._send(500, {"ok": False, "error": str(exc), "traceback": traceback.format_exc()[-1200:]})
            return
        self._send(404, {"ok": False, "error": "not found"})


def serve(host: str = FOUNDRY_HOST, port: int = FOUNDRY_PORT) -> None:
    _oom_adj(os.getpid(), -200)
    httpd = ThreadingHTTPServer((host, port), Handler)
    httpd.allow_reuse_address = True
    st = _read_status()
    write_status(
        phase=st.get("phase") or "idle",
        training=bool(st.get("training")),
        trained=ready() or bool(st.get("trained")),
        server=f"{host}:{port}",
        serve_pid=os.getpid(),
    )
    if ready():
        def _warm_up():
            try:
                from .infer import load_bundle

                load_bundle()
            except Exception:
                pass

        threading.Thread(target=_warm_up, daemon=True).start()

    print(f"[+] Scansion-LM Foundry server listening on http://{host}:{port}")
    httpd.serve_forever()
