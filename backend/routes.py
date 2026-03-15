from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
from .gemini_service import process_prompt
import json
import os
import base64

router = APIRouter()
HISTORY_FILE = "chat_history.json"

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return []

def save_message(role: str, text: str, image_b64: str = None, audio_b64: str = None):
    history = load_history()
    history.append({
        "role": role,
        "text": text,
        "image_base64": image_b64,
        "audio_base64": audio_b64
    })
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f)

@router.get("/history")
async def get_history():
    return {"history": load_history()}

@router.get("/clear-history")
async def clear_history():
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
    return {"status": "cleared"}

@router.post("/ask-athena")
async def ask_athena(
    text: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None)
):
    try:
        image_bytes = await image.read() if image and image.filename else None
        audio_bytes = await audio.read() if audio and audio.filename else None

        # Save user message
        user_text = text if text else "Media Attachment"
        user_img_b64 = base64.b64encode(image_bytes).decode('utf-8') if image_bytes else None
        user_aud_b64 = base64.b64encode(audio_bytes).decode('utf-8') if audio_bytes else None
        save_message("user", user_text, user_img_b64, user_aud_b64)

        response_dict = process_prompt(
            text=text,
            image_bytes=image_bytes,
            audio_bytes=audio_bytes
        )

        # Save assistant message
        save_message("assistant", response_dict.get("text", ""), response_dict.get("image_base64"), response_dict.get("audio_base64"))

        return response_dict
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
