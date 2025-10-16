import os
import psutil
import time
import streamlit as st
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

# ---------- Load environment ----------
load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY", "not_set")
huggingface_key = os.getenv("HUGGINGFACE_API_KEY", "not_set")

# ---------- App Setup ----------
st.set_page_config(page_title="UltimateAI_IDE", layout="wide")
st.title("🧠 UltimateAI_IDE — AI Development Console")

tabs = st.tabs(["Agent", "Architect", "🤗 Hugging Face Sandbox", "⚙️ Settings", "📊 System Monitor"])

# ------------------------------------------------
# 1️⃣ Agent Tab
# ------------------------------------------------
with tabs[0]:
    st.header("Agent Console")
    user_input = st.text_area("Enter a task or question:", height=150)
    if st.button("Run Agent"):
        st.info(f"🤖 Agent received: {user_input}")
        st.success("Agent simulation complete (placeholder).")

# ------------------------------------------------
# 2️⃣ Architect Tab
# ------------------------------------------------
with tabs[1]:
    st.header("Architect Workspace")
    code_input = st.text_area("Enter or paste code to analyze:", height=200)
    if st.button("Analyze Code"):
        if code_input.strip():
            st.code(code_input, language="python")
            st.info("Code review completed (placeholder).")
        else:
            st.warning("Please provide code to analyze.")

# ------------------------------------------------
# 3️⃣ Hugging Face Inference Tab
# ------------------------------------------------
with tabs[2]:
    st.header("🤗 Hugging Face Sandbox — Cloud Inference Mode")
    st.caption(f"Hugging Face Key Loaded: {'✅' if huggingface_key != 'not_set' else '❌ Not Set'}")

    model_name = st.text_input("Model Name", value="gpt2")
    prompt = st.text_area("Enter your text prompt:", height=150)
    generate_button = st.button("Generate")

    if generate_button and prompt.strip():
        try:
            st.write("🚀 Sending prompt to Hugging Face Inference API…")
            client = InferenceClient(token=huggingface_key)
            result = client.text_generation(
                model=model_name,
                prompt=prompt,
                max_new_tokens=120,
                temperature=0.7,
            )
            st.subheader("Generated Output:")
            st.write(result)
        except Exception as e:
            st.error(f"⚠️ Error during inference: {e}")

# ------------------------------------------------
# 4️⃣ Settings Tab
# ------------------------------------------------
with tabs[3]:
    st.header("⚙️ Settings")
    st.text_input("OpenAI API Key", value=openai_key, type="password")
    st.text_input("Hugging Face API Key", value=huggingface_key, type="password")
    st.selectbox("Theme", ["Dark", "Light"], index=0)
    st.info("Settings are for display only — persistent config coming soon.")

# ------------------------------------------------
# 5️⃣ System Monitor Tab (real-time resource usage)
# ------------------------------------------------
with tabs[4]:
    st.header("📊 System Resource Monitor")
    st.caption("Real-time CPU and memory usage of this Render instance")

    placeholder = st.empty()

    # Auto-refresh system stats every 2 seconds
    for _ in range(60):  # runs for ~2 minutes before stopping auto-refresh
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        used = round(mem.used / (1024 ** 2), 2)
        total = round(mem.total / (1024 ** 2), 2)
        percent = mem.percent

        with placeholder.container():
            col1, col2 = st.columns(2)
            with col1:
                st.metric("🧮 CPU Usage", f"{cpu} %")
            with col2:
                st.metric("💾 Memory Usage", f"{used} MB / {total} MB", f"{percent}%")

            st.progress(percent / 100)
            st.caption("Auto-refreshing every 2 seconds…")

        time.sleep(2)
