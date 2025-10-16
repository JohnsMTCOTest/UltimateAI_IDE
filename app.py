# UltimateAI IDE — Replit-Style with Smart Agent + Console + Web Preview

import os
import shlex
import subprocess
import socket
from pathlib import Path
import streamlit as st
import psutil
from openai import OpenAI

# =========================
# CONFIG + SETUP
# =========================
st.set_page_config(page_title="UltimateAI IDE (Replit-style)", layout="wide")
WORKSPACE = Path("workspace")
WORKSPACE.mkdir(exist_ok=True)
DEFAULT_FILE = WORKSPACE / "main.py"
DEFAULT_FILE.touch(exist_ok=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# =========================
# SIDEBAR: Files + Metrics
# =========================
st.sidebar.title("📁 Project Files")

def list_files(root):
    return sorted([p for p in root.rglob("*") if p.is_file()])

def select_file_ui():
    files = list_files(WORKSPACE)
    rel_paths = [str(p.relative_to(WORKSPACE)) for p in files] or ["(no files)"]
    selected = st.sidebar.selectbox("Select file", rel_paths)
    return WORKSPACE / selected if selected != "(no files)" else None

current_file = select_file_ui()

with st.sidebar.expander("➕ Create / Delete"):
    new_path = st.text_input("New path", value="new_file.py")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Create File"):
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
                st.success("Deleted!")
                st.rerun()

cpu = psutil.cpu_percent(interval=0.2)
ram = psutil.virtual_memory().percent
st.sidebar.markdown("---")
st.sidebar.write(f"CPU: {cpu}% | RAM: {ram}%")

# =========================
# MAIN UI LAYOUT
# =========================
st.title("🧠 UltimateAI IDE (Replit-style)")
col_agent, col_console = st.columns([1.8, 1.2])

# =========================
# LEFT: Agent
# =========================
with col_agent:
    st.subheader("🤖 AI Agent (Generate Code)")
    prompt = st.text_area("Describe what to build", height=120)
    target_file = st.text_input("Target file", value="main.py")
    stream_mode = st.checkbox("⚡ Stream output live", value=True)
    auto_run = st.checkbox("🚀 Auto-Run after generation", value=True)

    if st.button("✨ Generate"):
        dest = WORKSPACE / target_file
        dest.parent.mkdir(parents=True, exist_ok=True)

        if not os.getenv("OPENAI_API_KEY"):
            st.error("Missing OPENAI_API_KEY.")
        elif not prompt.strip():
            st.warning("Please enter a prompt.")
        else:
            st.info("Generating code...")
            output = ""
            try:
                if stream_mode:
                    stream = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "You are an expert developer. Output clean, working code only."},
                            {"role": "user", "content": prompt},
                        ],
                        stream=True,
                        max_tokens=1000,
                        temperature=0.5,
                    )
                    placeholder = st.empty()
                    for chunk in stream:
                        delta = chunk.choices[0].delta
                        if delta.content:
                            output += delta.content
                            placeholder.code(output, language="python")
                else:
                    resp = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "You are an expert developer."},
                            {"role": "user", "content": prompt},
                        ],
                        max_tokens=1000,
                        temperature=0.4,
                    )
                    output = resp.choices[0].message.content
                    st.code(output, language="python")

                dest.write_text(output)
                st.success(f"✅ Saved to {dest.relative_to(WORKSPACE)}")

                if auto_run and dest.suffix == ".py":
                    st.info("Auto-running...")
                    st.session_state.run_target = dest

            except Exception as e:
                st.error(f"Generation failed: {e}")

# =========================
# RIGHT: Console
# =========================
with col_console:
    st.subheader("🧪 Console")
    console = st.empty()

    def run_file(path: Path, timeout=15):
        if not path.exists():
            return f"❌ File not found: {path}"
        if path.suffix != ".py":
            return f"❌ Cannot run non-Python file: {path.name}"
        cmd = f"python -u {shlex.quote(str(path))}"
        try:
            proc = subprocess.run(
                cmd, shell=True, cwd=str(WORKSPACE),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=timeout, text=True
            )
            return f"$ {cmd}\n\n{proc.stdout}{proc.stderr}\nExit code: {proc.returncode}"
        except subprocess.TimeoutExpired:
            return f"❌ Timed out after {timeout}s."

    run_path = st.session_state.get("run_target", DEFAULT_FILE)

    if st.button("▶️ Run"):
        out = run_file(run_path)
        console.code(out, language="bash")

        if "Flask" in out or "Running on http://" in out:
            hostname = os.getenv("RENDER_EXTERNAL_HOSTNAME") or socket.gethostname()
            st.success("🌐 Flask app likely running.")
            st.markdown(f"**Open in browser:** [https://{hostname}](https://{hostname})")

# =========================
# Optional: File Editor Below
# =========================
with st.expander("📝 Code Editor (View/Edit Any File)"):
    try:
        from streamlit_ace import st_ace
        code = current_file.read_text() if current_file else ""
        content = st_ace(
            value=code,
            language="python",
            theme="twilight",
            min_lines=20,
            key="ace_editor",
        )
    except:
        content = st.text_area("Edit", value=current_file.read_text() if current_file else "", height=400)

    if st.button("💾 Save Changes"):
        if current_file:
            current_file.write_text(content)
            st.success(f"Saved: {current_file.name}")

st.caption("Built with ❤️ by UltimateAI • Replit-style IDE for Render")
