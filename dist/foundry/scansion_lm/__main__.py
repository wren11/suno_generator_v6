"""python -m scansion_lm <extract|tokenize|train|eval|export|serve|infer>"""

from __future__ import annotations

import json
import sys


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    cmd = (args[0] if args else "serve").lower()
    rest = args[1:]

    if cmd in ("serve", "server"):
        from .server import serve

        serve()
        return 0

    if cmd == "extract":
        from .corpus import build_all

        n = int(rest[0]) if rest else 640
        print(json.dumps(build_all(n), indent=2))
        return 0

    if cmd == "tokenize":
        from .tokenize import train_tokenizer

        print(str(train_tokenizer()))
        return 0

    if cmd == "train":
        from .train import train

        steps = int(rest[0]) if rest and rest[0].isdigit() else 300
        corpus_n = int(rest[1]) if len(rest) > 1 and rest[1].isdigit() else 640
        resume = any(a in ("resume", "--resume") for a in rest)
        print(json.dumps(train(steps=steps, corpus_n=corpus_n, resume=resume, rebuild=not resume), indent=2))
        return 0

    if cmd == "eval":
        from .eval_guide import eval_model, gold_sheet_score

        print(json.dumps({"gold": gold_sheet_score(), "model": eval_model()}, indent=2))
        return 0

    if cmd == "export":
        from .export_bundle import export_ready

        print(json.dumps(export_ready(), indent=2))
        return 0

    if cmd == "infer":
        from .infer import infer_composer

        composer = json.loads(rest[0]) if rest else {
            "title": "Heat Line",
            "idea": "A man scraping survival out of desert heat, stubborn will over panic.",
            "pov": "third",
            "genres": [{"name": "Rock", "weight": 70}, {"name": "Thrash metal", "weight": 30}],
            "vocalGender": "male",
            "vocalRange": "Baritone",
            "vocalDelivery": "Raspy, gritty, chest-forward",
            "tempo": "Allegro",
            "bpm": 115,
            "timeSignature": "4/4",
            "energy": 78,
            "structure": "standard",
            "rhyme": "ABAB",
            "meterStagger": True,
            "extraBreaks": True,
            "callAndResponse": False,
            "hitIds": [],
        }
        print(json.dumps(infer_composer(composer), indent=2))
        return 0

    if cmd == "check":
        from .export_bundle import export_ready

        info = export_ready()
        print(json.dumps(info, indent=2))
        return 0 if info.get("ok") else 1

    print("usage: python -m scansion_lm [extract|tokenize|train|eval|export|serve|infer|check]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
