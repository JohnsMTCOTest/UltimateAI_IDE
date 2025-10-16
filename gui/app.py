import os
import streamlit as st

st.set_page_config(page_title="UltimateAI_IDE", layout="wide")

st.title("UltimateAI_IDE")
st.markdown("**Status:** Initial deployment successful! Render app is running.")

col1, col2 = st.columns(2)

with col1:
    st.header("Agent Workspace")
    st.text_area("Agent Output", height=300, placeholder="Agent output will appear here...")

with col2:
    st.header("Architect Workspace")
    st.text_area("Architect Feedback", height=300, placeholder="Architect feedback will appear here...")

st.markdown("---")
st.write("Controls Panel (for future buttons, file uploads, and other actions)")
st.button("Run Agent")
st.button("Approve Code")
st.button("Request Changes")

mode = st.sidebar.selectbox('Mode', ['Plan Project','Build App','Generate & Test Code','Build SaaS'])
user_prompt = st.sidebar.text_area('Enter prompt:')

if st.button('Run'):
    if not user_prompt.strip():
        st.warning('Enter prompt!')
    else:
        st.subheader(f'{mode} Output')
        st.code(f"Simulated {mode} result for prompt:\n{user_prompt}")