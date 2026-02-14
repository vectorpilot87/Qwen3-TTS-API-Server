#!/usr/bin/env python3
import argparse
import json
import re
import sys
import urllib.request


def post_with_urllib(url: str, payload: dict, timeout: float):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        return resp.status, body


def infer_instruct(text: str) -> str:
    t = text.lower()

    if any(k in t for k in ["urgent", "warning", "alert", "asap", "immediately"]):
        return "clear, serious, urgent tone"
    if any(k in t for k in ["sorry", "apolog", "sad", "miss you", "feel better", "sick"]):
        return "soft, caring, comforting tone"
    if any(k in t for k in ["sleep", "goodnight", "breathe", "relax", "calm"]):
        return "gentle, soothing, sleepy tone"
    if any(k in t for k in ["hype", "let's go", "lets go", "excited", "win", "party"]):
        return "energetic, upbeat, playful tone"

    exclamations = len(re.findall(r"!", text))
    if exclamations >= 2:
        return "playful, excited tone"

    return "warm, natural conversational tone"


def main():
    parser = argparse.ArgumentParser(description="Send text to qwen3 speak API")
    parser.add_argument("text", help="Text to speak")
    parser.add_argument("--url", default="http://192.168.50.196:8000/speak", help="Speak API URL")
    parser.add_argument("--language", default="English", help="Language value")
    parser.add_argument("--voice", default="Vivian", help="Voice value")
    parser.add_argument(
        "--instruct",
        default=None,
        help="Style instruction (omit to auto-infer from text context)",
    )
    parser.add_argument("--timeout", type=float, default=20, help="Request timeout seconds")

    args = parser.parse_args()
    instruct = args.instruct if args.instruct else infer_instruct(args.text)

    payload = {
        "text": args.text,
        "language": args.language,
        "voice": args.voice,
        "instruct": instruct,
    }

    try:
        import requests  # type: ignore

        r = requests.post(args.url, json=payload, timeout=args.timeout)
        print(f"status={r.status_code}")
        if r.text:
            print(r.text)
        r.raise_for_status()
    except ModuleNotFoundError:
        status, body = post_with_urllib(args.url, payload, args.timeout)
        print(f"status={status}")
        if body:
            print(body)
        if status >= 400:
            raise SystemExit(1)
    except Exception as e:
        print(f"qwen3-speak error: {e}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()