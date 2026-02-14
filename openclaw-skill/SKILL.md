---

name: qwen3-tts

description: Send speech text to a Qwen3 TTS-style HTTP API via POST. Use when the user says things like "speak", "say aloud", or asks for voice output through the custom endpoint at http://<ip>:<port>/speak with language/voice/instruct fields.

---



\# qwen3-tts



Use this skill to speak text through the custom local API instead of built-in TTS.



\## Quick use



Run the helper script and pass the exact text to speak:



```bash

python3 /home/edge/.openclaw/workspace/skills/qwen3-speak/scripts/qwen3\_speak.py "Hello Kevin"

```



\## Behavior



\- Default endpoint: `http://<ip>:<port>/speak`

\- Default payload fields:

&nbsp; - `language`: `English`

&nbsp; - `voice`: `Vivian`

&nbsp; - `instruct`: auto-inferred from message context

\- You can still force a specific style with `--instruct` when needed.

\- Replace only `text` in normal use.



\## Optional overrides



```bash

python3 /home/edge/.openclaw/workspace/skills/qwen3-speak/scripts/qwen3\_speak.py \\

&nbsp; "Custom line" \\

&nbsp; --url "http://<ip>:<port>/speak" \\

&nbsp; --language "English" \\

&nbsp; --voice "Vivian" \\

&nbsp; --instruct "playful tone"

```



\## Output handling



\- Script prints HTTP status and response body.

\- Treat non-2xx responses as failure and report concise error text.


