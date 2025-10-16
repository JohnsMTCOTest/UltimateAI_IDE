import os
import psutil
import streamlit as st
from openai import OpenAI

# ---- App Configuration ----
st.set_page_config(page_title="UltimateAI_IDE", layout="wide")
st.title("🧠 UltimateAI IDE (OpenAI Edition)")
st.markdown("A lightweight, stable AI-powered code workspace using your OpenAI API key.")

# ---- Sidebar: API Key & Settings ----
st.sidebar.header("⚙️ Settings")

# Retrieve key from environment or sidebar
api_key = os.getenv("OPENAI_API_KEY") or st.sidebar.text_input("Enter your OpenAI API Key", type="password")

model = st.sidebar.selectbox(
    "Choose Model",
    ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
    index=0
)

max_tokens = st.sidebar.slider("Max Tokens", 50, 2000, 400)
temperature = st.sidebar.slider("Creativity (Temperature)", 0.0, 1.5, 0.7)

# ---- CPU / RAM Monitor ----
st.sidebar.header("🖥️ System Monitor")
cpu = psutil.cpu_percent(interval=0.5)
ram = psutil.virtual_memory().percent
st.sidebar.progress(cpu / 100)
st.sidebar.write(f"**CPU:** {cpu}% | **RAM:** {ram}%")

# ---- Input Section ----
st.subheader("💬 Prompt Input")
user_prompt = st.text_area("Enter your request:", height=150, placeholder="e.g., Generate a Python Flask API for user authentication...")

# ---- Output Section ----
st.subheader("🧩 Output")

if st.button("Generate Response"):
    if not api_key:
        st.error("⚠️ Please enter your OpenAI API key in the sidebar.")
    elif not user_prompt.strip():
        st.warning("Enter a prompt before generating!")
    else:
        try:
            st.info("Generating... please wait ⏳")
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert AI coding assistant."},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            output_text = response.choices[0].message.content
            st.success("✅ Response Generated!")
            st.text_area("AI Output", value=output_text, height=300)
        except Exception as e:
            st.error(f"⚠️ Error: {e}")

# ---- Footer ----
st.markdown("---")
st.caption("Built with ❤️ using Streamlit + OpenAI API. No Hugging Face dependencies.")

