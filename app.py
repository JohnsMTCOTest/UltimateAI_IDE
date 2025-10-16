import os
import streamlit as st

# -------------------------------
# Page setup
# -------------------------------
st.set_page_config(page_title="UltimateAI IDE | Render Test", layout="wide")
st.title("✅ Render Deployment Check")
st.write("If you can see this, your Streamlit server is connected and running.")

st.markdown("---")

# -------------------------------
# OpenAI API Test
# -------------------------------
st.header("🔮 OpenAI Text Generation Test")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.warning("⚠️ No OpenAI API key found. Add it in Render → Environment → Key: `OPENAI_API_KEY`.")
else:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)

        prompt = st.text_area("Enter a prompt:", "Write a short haiku about Streamlit on Render.")
        if st.button("Generate with OpenAI"):
            with st.spinner("Generating..."):
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=100
                )
                st.success("✅ Generated Text:")
                st.write(response.choices[0].message.content)

    except Exception as e:
        st.error(f"OpenAI API error: {e}")

st.markdown("---")

# -------------------------------
# Hugging Face Local Test
# -------------------------------
st.header("🤗 Hugging Face Local Text Generator (CPU-safe)")

try:
    from transformers import pipeline

    if st.button("Load Hugging Face Model"):
        with st.spinner("Loading model... This takes ~10s on first run."):
            generator = pipeline("text-generation", model="distilgpt2")
        st.session_state["generator"] = generator
        st.success("✅ Model loaded successfully!")

    if "generator" in st.session_state:
        user_prompt = st.text_area("Enter a prompt for Hugging Face model:", "Once upon a time")
        if st.button("Run HF Model"):
            with st.spinner("Generating text..."):
                result = st.session_state["generator"](user_prompt, max_length=60, num_return_sequences=1)
                st.success("✅ Generated Text:")
                st.write(result[0]["generated_text"])
except Exception as e:
    st.error(f"Hugging Face error: {e}")

st.markdown("---")
st.caption("🚀 UltimateAI IDE | Render environment validation complete.")

