import streamlit as st
import os
from transformers import pipeline

# --- Streamlit Page Setup ---
st.set_page_config(page_title="UltimateAI_IDE - Hugging Face Test", layout="wide")

st.title("🤖 UltimateAI_IDE - Render Hugging Face Test")
st.write("If you can see this page, your Streamlit app deployed correctly on Render!")

st.divider()

# --- Hugging Face Section ---
st.header("Hugging Face Text Generation Test")

@st.cache_resource
def load_model():
    """Load a lightweight Hugging Face model for testing."""
    os.environ["TRANSFORMERS_CACHE"] = "/tmp/huggingface"
    try:
        model = pipeline("text-generation", model="sshleifer/tiny-gpt2")
        return model
    except Exception as e:
        st.error(f"❌ Failed to load model: {e}")
        return None

if st.button("Load Model and Generate Text"):
    generator = load_model()
    if generator:
        st.success("✅ Model loaded successfully!")
        user_prompt = st.text_input("Enter a prompt:", "Render is working")
        if st.button("Generate"):
            with st.spinner("Generating text..."):
                try:
                    result = generator(user_prompt, max_new_tokens=40)
                    st.write("**Generated Text:**")
                    st.success(result[0]["generated_text"])
                except Exception as e:
                    st.error(f"❌ Error generating text: {e}")
    else:
        st.warning("Model not loaded yet. Please try again.")

st.divider()

# --- Footer ---
st.caption("© 2025 UltimateAI_IDE • Streamlit + Hugging Face Demo")


