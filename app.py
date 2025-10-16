import os
import gc
import streamlit as st
from dotenv import load_dotenv

# Optional: isolate heavy import to prevent reload on every rerun
@st.cache_resource
def get_pipeline(model_name):
    from transformers import pipeline
    return pipeline("text-generation", model=model_name)

# Load .env keys
load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY", "not_set")
huggingface_key = os.getenv("HUGGINGFACE_API_KEY", "not_set")

st.set_page_config(page_title="UltimateAI_IDE", layout="wide")
st.title("🧠 UltimateAI_IDE — AI Dev Console")

tabs = st.tabs(["Agent", "Architect", "Hugging Face Sandbox", "Settings"])

# ---- Agent ----
with tabs[0]:
    st.header("Agent Console")
    user_input = st.text_area("Enter a task or question:", height=150)
    if st.button("Run Agent"):
        st.write(f"🤖 Agent received: {user_input}")
        st.success("Agent simulation complete (placeholder).")

# ---- Architect ----
with tabs[1]:
    st.header("Architect Workspace")
    code_input = st.text_area("Enter or paste code to analyze:", height=200)
    if st.button("Analyze Code"):
        if code_input.strip():
            st.code(code_input, language="python")
            st.info("Code review completed (placeholder).")
        else:
            st.warning("Please provide code to analyze.")

# ---- Hugging Face Sandbox ----
with tabs[2]:
    st.header("🤗 Hugging Face Sandbox")
    st.caption(f"Hugging Face Key Loaded: {'✅' if huggingface_key != 'not_set' else '❌ Not Set'}")

    model_name = st.text_input("Model Name", value="distilgpt2")
    prompt = st.text_area("Enter your text prompt:", height=150)
    generate_button = st.button("Generate")

    if generate_button and prompt.strip():
        try:
            st.write("Loading model… please wait ⏳")
            generator = get_pipeline(model_name)
            output = generator(prompt, max_length=100, num_return_sequences=1)
            st.subheader("Generated Output:")
            st.write(output[0]["generated_text"])
        except Exception as e:
            st.error(f"⚠️ Error running Hugging Face model: {e}")
        finally:
            # clear memory on completion
            gc.collect()
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception:
                pass

# ---- Settings ----
with tabs[3]:
    st.header("⚙️ Settings")
    st.text_input("OpenAI API Key", value=openai_key, type="password")
    st.text_input("Hugging Face API Key", value=huggingface_key, type="password")
    st.selectbox("Theme", ["Dark", "Light"])
    st.info("Settings placeholders — persistent config coming soon.")

