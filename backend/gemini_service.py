import os
import io
import base64
from gtts import gTTS
from google import genai
from google.genai import types

# Hardcoded API key as requested
GEMINI_API_KEY = "" #Here put your ai api link .. it will work properly ... which is vertex ai

def get_client():
    return genai.Client(api_key=GEMINI_API_KEY)

def generate_tts_audio(text: str) -> str:
    """Generates an MP3 audio bytes base64 from text."""
    try:
        tts = gTTS(text=text, lang='en')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return base64.b64encode(fp.read()).decode('utf-8')
    except Exception as e:
        print(f"TTS Error: {e}")
        return None

def process_prompt(text: str = None, image_bytes: bytes = None, audio_bytes: bytes = None):
    client = get_client()
    contents = []
    
    # If there's audio but no text, transcribe it first so we can check for image generation keywords
    if audio_bytes and not text:
        try:
            transcribe_res = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[types.Part.from_bytes(data=audio_bytes, mime_type='audio/wav'), "Give a direct transcription of this audio. No extra text or formatting."]
            )
            text = transcribe_res.text.strip()
            print("Transcribed audio to:", text)
        except Exception as e:
            print("Transcription failed:", e)
            
    # Simple explicit check if the user asked for an image
    prompt_lower = text.lower() if text else ""
    image_keywords = ["generate an image", "create an image", "draw", "generate a picture", "generate me image", "give me photo", "photo of", "image of", "picture of", "generate me an image", "create a photo"]
    wants_image = any(kw in prompt_lower for kw in image_keywords)
    
    if wants_image:
        # Route to pollinations.ai for free image generation
        try:
            import requests as req
            import re
            
            # Clean up the prompt more robustly to send just the image concept
            safe_prompt = prompt_lower
            for kw in image_keywords:
                safe_prompt = safe_prompt.replace(kw, "")
            # Remove "as a", "of a", "of"
            safe_prompt = re.sub(r'^(as a|of a|of|as)\s+', '', safe_prompt.strip()).strip()
            if not safe_prompt:
                safe_prompt = "beautiful landscape" # fallback
                
            prompt_url = req.utils.quote(safe_prompt)
            url = f"https://image.pollinations.ai/prompt/{prompt_url}?width=1024&height=1024&nologo=true"
            img_resp = req.get(url)
            img_b64 = None
            if img_resp.status_code == 200:
                img_bytes = img_resp.content
                img_b64 = base64.b64encode(img_bytes).decode('utf-8')
                
            return {
                "text": f"Here is the image you requested based on: '{safe_prompt}'",
                "audio_base64": generate_tts_audio("Here is the completed image."),
                "image_base64": img_b64
            }
        except Exception as e:
            return {"text": f"Sorry, image generation failed: {e}", "audio_base64": None, "image_base64": None}

    # Otherwise, regular multimodal chat fallback to text response
    if text:
        contents.append(text)
    if image_bytes:
        contents.append(types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg'))
    if audio_bytes:
        contents.append(types.Part.from_bytes(data=audio_bytes, mime_type='audio/wav'))
        
    if not contents:
        return {"text": "No input provided.", "audio_base64": None, "image_base64": None}

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=contents,
    )
    
    text_response = response.text
    audio_b64 = generate_tts_audio(text_response)
    
    return {
        "text": text_response,
        "audio_base64": audio_b64,
        "image_base64": None
    }
