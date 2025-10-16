import streamlit as st
from transformers import pipeline

# Page setup
st.set_page_config(page_title="UltimateAI_IDE", layout="wide")
st.title("🧠 UltimateAI_IDE — Streamlit AI Development Console")

# Tabs
tabs = st.tabs(["Agent", "Architect", "Hugging Face Sandbox", "Settings"])

# --- AGENT TAB ---
with tabs[0]:
    st.header("Agent Console")
    user_input = st.text_area("Enter a task or question:", height=150)
    if st.button("Run Agent"):
        st.write(f"🤖 Agent received: {user_input}")
        st.success("Agent simulation complete (placeholder).")

# --- ARCHITECT TAB ---
with tabs[1]:
    st.header("Architect Workspace")
    code_input = st.text_area("Enter or paste code to analyze:", height=200)
    if st.button("Analyze Code"):
        if code_input.strip():
            st.code(code_input, language="python")
            st.info("Code review completed (placeholder).")
        else:
            st.warning("Please provide code to analyze.")

# --- HUGGING FACE SANDBOX TAB ---
with tabs[2]:
    st.header("🤗 Hugging Face Sandbox")

    model_name = st.text_input(
        "Model Name (default: distilgpt2)",
        value="distilgpt2",
        help="Enter a Hugging Face model like distilgpt2, gpt2, etc."
    )

    prompt = st.text_area("Enter your text prompt:", height=150)
    generate_button = st.button("Generate")

    if generate_button and prompt.strip():
        try:
            st.write("Loading model… this may take a few seconds ⏳")
            generator = pipeline("text-generation", model=model_name)
            output = generator(prompt, max_length=100, num_return_sequences=1)
            st.subheader("Generated Output:")
            st.write(output[0]["generated_text"])
        except Exception as e:
            st.error(f"⚠️ Error running Hugging Face model: {e}")

# --- SETTINGS TAB ---
with tabs[3]:
    st.header("⚙️ Settings")
    st.text_input("OpenAI API Key (optional)", type="password")
    st.text_input("Hugging Face API Key (optional)", type="password")
    st.selectbox("Theme", ["Dark", "Light"])
    st.info("Settings are placeholders — full config coming soon.")
