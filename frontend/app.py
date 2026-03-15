import streamlit as st
import requests
import io
import os
import base64
from PIL import Image

st.set_page_config(page_title="Athena AI", page_icon="✨", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for ChatGPT-like Interface
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Message container padding adjustments */
    .stChatMessage {
        background-color: transparent !important;
        border: none !important;
        padding: 1.5rem !important;
    }

    /* Chat avatars */
    .stChatMessage [data-testid="stChatAvatar"] {
        background-color: transparent;
    }
    
    /* Removing the default streamlit block gap */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 6rem !important;
        max-width: 800px !important;
        margin: auto !important;
    }

    /* Input container at the bottom */
    [data-testid="stChatInput"] {
        border-radius: 1rem !important;
        box-shadow: 0 0 15px rgba(0,0,0,0.05) !important;
    }

    .empty-state {
        text-align: center;
        margin-top: 25vh;
        font-size: 1.2rem;
        font-weight: 500;
        opacity: 0.7;
    }
    
    .athena-title {
        text-align: center;
        font-size: 2.5rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        background: -webkit-linear-gradient(45deg, #FF6B6B, #6B66FF, #00D2D3);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
</style>
""", unsafe_allow_html=True)

backend_url = os.environ.get("BACKEND_URL", "http://localhost:8000")

# Fetch constraints and state
if "messages" not in st.session_state:
    st.session_state.messages = []
    try:
        response = requests.get(f"{backend_url}/history")
        if response.status_code == 200:
            history_data = response.json().get("history", [])
            for msg in history_data:
                parsed_msg = {"role": msg["role"], "text": msg.get("text", "")}
                if msg.get("image_base64"):
                    parsed_msg["image"] = base64.b64decode(msg["image_base64"])
                if msg.get("audio_base64"):
                    parsed_msg["audio"] = base64.b64decode(msg["audio_base64"])
                st.session_state.messages.append(parsed_msg)
    except Exception as e:
        print("Error fetching history:", e)

# Header / Empty state
if len(st.session_state.messages) == 0:
    st.markdown('<div class="empty-state">', unsafe_allow_html=True)
    st.markdown('<div class="athena-title">Athena AI</div>', unsafe_allow_html=True)
    st.markdown('<div>How can I help you today?</div></div>', unsafe_allow_html=True)

# Audio / Image inputs side drawer
with st.sidebar:
    st.markdown("### New Chat")
    if st.button("Clear Chat History", use_container_width=True):
        try:
            requests.get(f"{backend_url}/clear-history")
        except: pass
        st.session_state.messages = []
        st.rerun()

st.markdown("</div>", unsafe_allow_html=True)
# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar="✨" if message["role"] == "assistant" else "👤"):
        if "text" in message:
            st.markdown(message["text"])
        if "image" in message and message["image"]:
            st.image(message["image"], caption="Attached Image" if message["role"] == "user" else "Generated Image")
        if "audio" in message and message["audio"]:
            st.audio(message["audio"], format="audio/mp3")


# Accept user input
prompt_data = st.chat_input(
    "Message Athena...",
    accept_file=True,
    file_type=["png", "jpg", "jpeg"],
    accept_audio=True
)

if prompt_data:
    user_text = prompt_data.text if prompt_data.text else ""
    uploaded_image = prompt_data.files[0] if prompt_data.files else None
    recorded_audio_file = prompt_data.audio if prompt_data.audio else None
    
    recorded_audio = recorded_audio_file.getvalue() if recorded_audio_file else None

    if not user_text:
        if recorded_audio: user_text = "(Voice message attached)"
        elif uploaded_image: user_text = "(Image attached)"
        else: user_text = ""

    # Display user message
    st.session_state.messages.append({"role": "user", "text": user_text})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_text)
        if uploaded_image:
            st.image(uploaded_image, width=200)
        if recorded_audio:
            st.audio(recorded_audio, format="audio/wav")

    # Display assistant response
    with st.chat_message("assistant", avatar="✨"):
        message_placeholder = st.empty()
        message_placeholder.markdown("...")
        
        files = {}
        data = {}
        if user_text and user_text not in ["(Voice message attached)", "(Image attached)"]:
            data["text"] = user_text
        if uploaded_image:
             files["image"] = (uploaded_image.name, uploaded_image.getvalue(), uploaded_image.type)
        if recorded_audio:
             files["audio"] = ("audio.wav", recorded_audio, "audio/wav")
             
        try:
            response = requests.post(f"{backend_url}/ask-athena", data=data, files=files)
            if response.status_code == 200:
                res_json = response.json()
                bot_text = res_json.get("text", "")
                
                message_placeholder.markdown(bot_text)
                
                audio_b64 = res_json.get("audio_base64")
                image_b64 = res_json.get("image_base64")
                
                audio_bytes = None
                img_bytes = None
                
                if audio_b64:
                    audio_bytes = base64.b64decode(audio_b64)
                    st.audio(audio_bytes, format="audio/mp3", autoplay=True)
                
                if image_b64:
                    img_bytes = base64.b64decode(image_b64)
                    st.image(img_bytes, caption="Athena generated this.")
                    
                st.session_state.messages.append({
                    "role": "assistant", 
                    "text": bot_text,
                    "audio": audio_bytes,
                    "image": img_bytes
                })
            else:
                message_placeholder.error(f"Error: {response.status_code}")
        except Exception as e:
            message_placeholder.error(f"Failed: {e}")
