import os
import subprocess
import shlex
from pathlib import Path

import psutil
import streamlit as st
from streamlit_ace import st_ace

# =========================
# SETUP
# =========================
st.set_page_config(page_title="UltimateAI IDE", layout="wide")
WORKSPACE = Path("workspace")
TEMPLATE_DIR = WORKSPACE / "templates"
MAIN_FILE = WORKSPACE / "app.py"
INDEX_FILE = TEMPLATE_DIR / "index.html"
WORKSPACE.mkdir(exist_ok=True)
TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)

# Preload Flask app if not already present
if not MAIN_FILE.exists():
    MAIN_FILE.write_text("""\
from flask import Flask, render_template
import os

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "0") == "1")
""")

if not INDEX_FILE.exists():
    INDEX_FILE.write_text("""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Test Flask Site</title>
</head>
<body>
  <h1>Hello from Flask!</h1>
  <p>This is your IDE Preview working without OpenAI.</p>
</body>
</html>
""")

# =========================
# SIDEBAR — File Browser
# =========================
st.sidebar.title("📁 Workspace Files")

def list_files(root):
    return sorted([p for p in root.rglob("*") if p.is_file()])

files = list_files(WORKSPACE)
rel_paths = [str(p.relative_to(WORKSPACE)) for p in files]
selected_file = st.sidebar.selectbox("Select File", rel_paths)
current_file = WORKSPACE / selected_file if selected_file else None

with st.sidebar.expander("➕ Create / Delete"):
    new_path = st.text_input("New file path", "new_file.py")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Create"):
            p = WORKSPACE / new_path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.touch(exist_ok=True)
            st.success(f"Created {p}")
            st.rerun()
    with col2:
        if st.button("Delete"):
            p = WORKSPACE / new_path
            if p.exists():
                p.unlink()
                st.success(f"Deleted {p}")
                st.rerun()

# =========================
# MAIN TABS
# =========================
tab1, tab2, tab3 = st.tabs(["💻 Editor", "🧪 Console", "🌐 Preview"])

# ---- Code Editor ----
with tab1:
    st.subheader("💻 Code Editor")
    code = current_file.read_text() if current_file and current_file.exists() else ""
    content = st_ace(value=code, language="python", theme="twilight", key="ace_editor", min_lines=20)
    if st.button("💾 Save"):
        if current_file:
            current_file.write_text(content)
            st.success(f"Saved {current_file.name}")

# ---- Console Runner ----
with tab2:
    st.subheader("🧪 Console Output")
    def run_file(path: Path, timeout=20):
        cmd = f"python -u {shlex.quote(str(path))}"
        try:
            proc = subprocess.run(
                cmd, shell=True, cwd=str(WORKSPACE),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=timeout, text=True
            )
            return f"$ {cmd}\n\n{proc.stdout}\n{proc.stderr}\nExit code: {proc.returncode}"
        except subprocess.TimeoutExpired:
            return f"$ {cmd}\n\n❌ Timed out after {timeout}s."

    if st.button("▶️ Run File"):
        if current_file and current_file.suffix == ".py":
            st.code(run_file(current_file), language="bash")
        else:
            st.warning("Select a .py file to run.")

# ---- Live Preview ----
with tab3:
    st.subheader("🌐 Live Web Preview")
    st.markdown("This section assumes you're running a Flask app on Render.")
    st.info("👉 When deployed, you can embed your Render web URL here using an iframe.")
    st.code("https://your-render-url.onrender.com", language="text")
    # st.components.v1.iframe("https://your-render-url.onrender.com", height=500)

# =========================
# COMMENTED OUT: AGENT SECTION
# =========================
"""
# === Agent (Temporarily Disabled) ===
from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.markdown("---")
st.subheader("🤖 AI Agent (Disabled)")
prompt = st.text_area("Describe what to build")
if st.button("✨ Generate (disabled)"):
    st.warning("Agent temporarily disabled due to insufficient OpenAI quota.")
"""

# =========================
# SYSTEM STATS
# =========================
cpu = psutil.cpu_percent(interval=0.2)
ram = psutil.virtual_memory().percent
st.sidebar.markdown("---")
st.sidebar.write(f"CPU: {cpu}% | RAM: {ram}%")

