import os
import subprocess
import shlex
import threading
import time
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
default_file = "app.py" if "app.py" in rel_paths else rel_paths[0] if rel_paths else None
selected_file = st.sidebar.selectbox("Select File", rel_paths, index=rel_paths.index(default_file) if default_file else 0)
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
    console = st.empty()
    log_lines = []
    flask_process = None

    def run_flask_app(path: Path):
        global flask_process
        rel_path = path.relative_to(WORKSPACE)
        cmd = f"python -u {shlex.quote(str(rel_path))}"
        flask_process = subprocess.Popen(
            cmd,
            shell=True,
            cwd=str(WORKSPACE),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        for line in flask_process.stdout:
            log_lines.append(line)
            console.code("".join(log_lines), language="bash")

    if st.button("▶️ Run Flask App"):
        if current_file and current_file.suffix == ".py":
            threading.Thread(target=run_flask_app, args=(current_file,), daemon=True).start()
        else:
            st.warning("Select a .py file to run.")

# ---- Live Preview ----
with tab3:
    st.subheader("🌐 Live Web Preview")
    st.markdown("Below is an iframe preview of the Flask app (Render deployments only).")
    preview_url = os.getenv("PREVIEW_URL", "https://your-render-url.onrender.com")
    st.components.v1.iframe(preview_url, height=500)

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

