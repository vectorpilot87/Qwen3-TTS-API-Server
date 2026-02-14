# Local Qwen3-TTS API (CustomVoice + VoiceDesign)

A small **FastAPI** server that exposes a local `/speak` endpoint to synthesize speech using **Qwen3 TTS** in one of two modes:

- **VoiceDesign mode** (default): Generates a voice from the provided `instruct` prompt (no fixed speaker).
- **CustomVoice mode**: Uses a specific `speaker`/`voice` identifier to generate speech in a consistent voice.

> **Important:** This server **plays audio locally on the host machine** via `sounddevice`.  
> It does **not** return audio bytes in the HTTP response. The response is JSON metadata only.

---

## How it works

On startup the server loads **two Qwen3 TTS checkpoints** onto the GPU:

- `Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice`
- `Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign`

Requests are routed based on the presence of `voice` in the POST body:

- If `voice` is provided and non-empty → `custom_model.generate_custom_voice(...)` (**CustomVoice**)
- Otherwise → `design_model.generate_voice_design(...)` (**VoiceDesign**)

The first waveform (`wavs[0]`) is selected, then a short **silence padding** is appended to reduce playback cutoff at the end of the utterance. The audio is then played back using:

- `sd.play(audio_padded, sr)`
- `sd.wait()`

---

## API

### `POST /speak`

Synthesize and play audio on the server host.

**Request body (JSON)**

```json
{
  "text": "Hello world",
  "language": "English",
  "instruct": "neutral tone, clear and natural speech",
  "voice": "optional-speaker-id"
}
```

**Fields**
- `text` *(string, required)*: Text to synthesize.
- `language` *(string, optional)*: Language hint passed to the model. Default: `English`.
- `instruct` *(string, optional)*: Style/voice instruction prompt. Default: `neutral tone, clear and natural speech`.
- `voice` *(string | null, optional)*: If provided, selects **CustomVoice** mode and is used as the speaker identifier.

**Response (JSON)**
- `status`: `"played"` on success
- `mode`: `"CustomVoice"` or `"VoiceDesign"`
- `text`, `language`
- `instruct_summary`: first 100 chars of `instruct`
- `voice`: the provided `voice` (or `null`)
- `padded_duration_sec`: approximate playback duration including padding

---

### `GET /health`

Simple readiness check.

**Response**
```json
{ "status": "healthy", "models_loaded": true }
```

---

## Dependencies

### System requirements
- **NVIDIA GPU** with CUDA support (the server loads models with `device_map="cuda"`).
- Working **CUDA drivers/runtime** compatible with your PyTorch build.
- Audio output device accessible to the process (since playback uses `sounddevice`).

### Python dependencies
At minimum, the script imports:
- `torch`
- `numpy`
- `sounddevice`
- `fastapi`
- `pydantic`
- `uvicorn`
- `qwen_tts` (provides `Qwen3TTSModel`)

Example `pip` install (adjust PyTorch/CUDA wheels for your environment):
```bash
pip install fastapi uvicorn pydantic numpy sounddevice
pip install torch   # or install the correct CUDA build from pytorch.org
pip install qwen_tts
```

> Optional: If you want to enable FlashAttention, install it and uncomment:
> `attn_implementation="flash_attention_2"`

---

## Running the server

If your file is named `server.py`:

```bash
uvicorn server:app --host 0.0.0.0 --port 8000 --log-level info
```

You should see startup logs indicating both models were loaded.

---

## Testing with `curl`

### 1) VoiceDesign mode (no speaker / no `voice`)
This uses `design_model.generate_voice_design(...)`.

```bash
curl -X POST http://localhost:8000/speak \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is VoiceDesign mode speaking.",
    "language": "English",
    "instruct": "calm, warm, slightly upbeat, clear enunciation"
  }'
```

### 2) CustomVoice mode (provide `voice`)
This uses `custom_model.generate_custom_voice(...)`.

```bash
curl -X POST http://localhost:8000/speak \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is CustomVoice mode using a fixed speaker.",
    "language": "English",
    "instruct": "neutral tone, clear and natural speech",
  }'
```

### 3) Health check
```bash
curl http://localhost:8000/health
```

---

## Notes / caveats

- **Audio is played on the server host**, not streamed back to the client.
- The response only reports metadata such as which mode was used and the padded duration.
- The server loads **both** models at startup; expect significant GPU VRAM usage.
- Sample rate is expected to be **24 kHz** (`SAMPLE_RATE = 24000`). If the model returns a different rate, the server logs a warning.

---

## Security warning

This API currently requires **no authorization**. If exposed beyond localhost, it should be hardened (e.g., API keys, network segmentation, or a reverse proxy with auth/rate limiting) to prevent abuse.
