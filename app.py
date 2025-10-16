import os
import io
import psutil
import shlex
import subprocess
import streamlit as st
from pathlib import Path
from openai import OpenAI

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="UltimateAI IDE (Replit-style)", layout="wide")
WORKSPACE = Path("workspace")
WORKSPACE.mkdir(exist_ok=True)
DEFAULT_FILE = WORKSPACE / "main.py"
DEFAULT_FILE.touch(exist_ok=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# =========================
# SIDEBAR
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

st.sidebar.markdown("---")
cpu = psutil.cpu_percent(interval=0.2)
ram = psutil.virtual_memory().percent
st.sidebar.write(f"CPU: {cpu}% | RAM: {ram}%")

# =========================
# TOP BAR
# =========================
col_a, col_b = st.columns([3, 1])
with col_a:
    st.title("🧠 UltimateAI IDE (OpenAI Edition)")
with col_b:
    st.caption("Replit-style workspace")

# =========================
# MAIN LAYOUT
# =========================
col_editor, col_console = st.columns([2, 1.2])

# ---- Editor ----
with col_editor:
    st.subheader("💻 Code Editor")

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
    except Exception:
        content = st.text_area("Code", value=current_file.read_text() if current_file else "", height=400)

    if st.button("💾 Save"):
        if current_file:
            current_file.write_text(content)
            st.success(f"Saved {current_file.name}")

# ---- Console ----
with col_console:
    st.subheader("🧪 Console")

    def run_file(path: Path, timeout=15):
        if not path.suffix == ".py":
            return f"Cannot run non-Python file: {path}"
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

    if st.button("▶️ Run"):
        if current_file:
            out = run_file(current_file)
            st.code(out, language="bash")

# =========================
# AGENT / ARCHITECT
# =========================
st.markdown("---")
st.subheader("🤖 Agent & 🛠️ Architect")

col1, col2 = st.columns(2)

# ---- AGENT ----
with col1:
    st.markdown("### 🤖 Agent (Generate Code)")
    prompt = st.text_area("Describe what to build", height=120)
    target_file = st.text_input("Target file", value=str(current_file.relative_to(WORKSPACE)) if current_file else "main.py")
    stream_mode = st.checkbox("⚡ Stream output live", value=True)

    if st.button("✨ Generate"):
        if not os.getenv("OPENAI_API_KEY"):
            st.error("Missing OPENAI_API_KEY environment variable.")
        elif not prompt.strip():
            st.warning("Enter a description.")
        else:
            dest = WORKSPACE / target_file
            st.info("Generating code...")
            try:
                if stream_mode:
                    # Stream tokens like ChatGPT
                    response_stream = client.chat.completions.stream(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are an expert code generator. Write clean, complete code only."},
                            {"role": "user", "content": prompt},
                        ],
                        max_tokens=1000,
                        temperature=0.4,
                    )
                    output = ""
                    placeholder = st.empty()
                    for event in response_stream:
                        if event.type == "message.delta" and event.delta.content:
                            output += event.delta.content
                            placeholder.code(output, language="python")
                    dest.write_text(output)
                    st.success(f"✅ Code saved to {dest}")
                else:
                    # Full completion
                    resp = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are an expert code generator. Return only code."},
                            {"role": "user", "content": prompt},
                        ],
                        max_tokens=1000,
                        temperature=0.4,
                    )
                    output = resp.choices[0].message.content
                    dest.write_text(output)
                    st.code(output, language="python")
                    st.success(f"✅ Saved to {dest}")
            except Exception as e:
                st.error(f"Error: {e}")

# ---- ARCHITECT ----
with col2:
    st.markdown("### 🛠️ Architect (Review Code)")
    review_file = st.text_input("File to review", value=str(current_file.relative_to(WORKSPACE)) if current_file else "main.py")

    if st.button("🔍 Review"):
        if not os.getenv("OPENAI_API_KEY"):
            st.error("Missing OPENAI_API_KEY.")
        else:
            path = WORKSPACE / review_file
            if not path.exists():
                st.error("File not found.")
            else:
                code_text = path.read_text()
                st.info("Reviewing...")
                try:
                    resp = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are a senior software architect reviewing Python code for quality, security, and clarity."},
                            {"role": "user", "content": f"Review this code:\n\n{code_text}"},
                        ],
                        max_tokens=800,
                        temperature=0.3,
                    )
                    review = resp.choices[0].message.content
                    st.markdown("#### 🧾 Review Feedback")
                    st.write(review)
                except Exception as e:
                    st.error(f"Review failed: {e}")

st.markdown("---")
st.caption("Streamlit • Replit-style IDE • OpenAI Realtime Streaming")


