import torch
import numpy as np
import sounddevice as sd
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from qwen_tts import Qwen3TTSModel

app = FastAPI(title="Local Qwen3-TTS Dual-Mode Speaker API (CustomVoice + VoiceDesign)")

# ────────────────────────────────────────────────
# Model Configuration
# ────────────────────────────────────────────────
CUSTOM_VOICE_MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
VOICE_DESIGN_MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"

SAMPLE_RATE = 24000
SILENCE_PADDING_SEC = 1.0

# Global defaults
DEFAULT_LANGUAGE = "English"
DEFAULT_INSTRUCT = "neutral tone, clear and natural speech"

# Load both models at startup (on GPU)
print("Loading CustomVoice model...")
custom_model = Qwen3TTSModel.from_pretrained(
    CUSTOM_VOICE_MODEL_ID,
    torch_dtype=torch.bfloat16,
    device_map="cuda",
    # attn_implementation="flash_attention_2",  # uncomment if installed
)
print("CustomVoice model loaded!")

print("Loading VoiceDesign model...")
design_model = Qwen3TTSModel.from_pretrained(
    VOICE_DESIGN_MODEL_ID,
    torch_dtype=torch.bfloat16,
    device_map="cuda",
    # attn_implementation="flash_attention_2",
)
print("VoiceDesign model loaded on GPU!")

class TTSRequest(BaseModel):
    text: str
    language: str = DEFAULT_LANGUAGE
    instruct: str = DEFAULT_INSTRUCT
    voice: str | None = None  # If provided → use CustomVoice with this speaker

@app.post("/speak")
async def speak(request: TTSRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    try:
        print(f"Request: '{request.text}' | lang: {request.language} | instruct: {request.instruct[:80]}...")

        if request.voice and request.voice.strip():
            # ── CustomVoice mode ──
            speaker = request.voice.strip()
            print(f"Using CustomVoice mode with speaker: {speaker}")

            wavs, sr = custom_model.generate_custom_voice(
                text=request.text,
                language=request.language,
                speaker=speaker,
                instruct=request.instruct,
            )
            mode_used = "CustomVoice"
        else:
            # ── VoiceDesign mode ──
            print("Using VoiceDesign mode (no speaker specified)")
            wavs, sr = design_model.generate_voice_design(
                text=request.text,
                language=request.language,
                instruct=request.instruct,
            )
            mode_used = "VoiceDesign"

        audio = wavs[0]  # First waveform

        if sr != SAMPLE_RATE:
            print(f"Warning: sr {sr} != expected {SAMPLE_RATE}")

        # Pad with silence to fix cutoff
        silence_samples = int(SILENCE_PADDING_SEC * sr)
        if audio.ndim == 1:
            silence = np.zeros(silence_samples, dtype=audio.dtype)
        else:
            silence = np.zeros((silence_samples, audio.shape[1]), dtype=audio.dtype)

        audio_padded = np.concatenate([audio, silence], axis=0)

        print(f"Playing ({mode_used}) with {SILENCE_PADDING_SEC}s padding...")
        sd.play(audio_padded, sr)
        sd.wait()
        time.sleep(0.2)  # Extra buffer

        return {
            "status": "played",
            "mode": mode_used,
            "text": request.text,
            "language": request.language,
            "instruct_summary": request.instruct[:100] + "..." if len(request.instruct) > 100 else request.instruct,
            "voice": request.voice if request.voice else None,
            "padded_duration_sec": round(len(audio_padded) / sr, 2)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "models_loaded": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
