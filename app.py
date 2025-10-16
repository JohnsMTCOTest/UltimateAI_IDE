import os
import psutil
import shlex
import subprocess
import streamlit as st
from pathlib import Path
from openai import OpenAI
from difflib import unified_diff

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="UltimateAI IDE (Replit-Style Auto)", layout="wide")
WORKSPACE = Path("workspace")
WORKSPACE.mkdir(exist_ok=True)
DEFAULT_FILE = WORKSPACE / "main.py"
DEFAULT_FILE.touch(exist_ok=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# =========================
# SIDEBAR
# =========================
st.sidebar.title("📁 Project Files")

def list_files(root: Path):
    return sorted([p for p in root.rglob("*") if p.is_file()])

def select_file_ui():
    files = list_files(WORKSPACE)
    rel_paths = [str(p.relative_to(WORKSPACE)) for p in files] or ["(no files)"]
    selected = st.sidebar.selectbox("Select file", rel_paths)
    return WORKSPACE / selected if selected != "(no files)" else None

current_file = select_file_ui()

with st.sidebar.expander("➕ Create / Delete"):
    new_path = st.text_input("New path", value="new_file.py")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Create File"):
            p = WORKSPACE / new_path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.touch(exist_ok=True)
            st.success(f"Created {p}")
            st.rerun()
    with c2:
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
# UTILITIES
# =========================
def run_file(path: Path, timeout=25):
    cmd = f"python -u {shlex.quote(str(path))}"
    try:
        proc = subprocess.run(
            cmd, shell=True, cwd=str(WORKSPACE),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=timeout, text=True
        )
        return f"$ {cmd}\n\n{proc.stdout}{proc.stderr}\nExit code: {proc.returncode}"
    except subprocess.TimeoutExpired:
        return f"$ {cmd}\n\n❌ Timed out after {timeout}s."

def show_split_diff(before: str, after: str):
    """Render side-by-side diff with dark style."""
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 🧩 Before (Agent Output)")
        st.code(before, language="python")
    with col2:
        st.markdown("#### ⚙️ After (Auto-Fixed by Architect)")
        st.code(after, language="python")

def architect_review(code_text: str) -> str:
    """Architect reviews code and suggests improvements."""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are the Architect. Review Python code for quality, "
                    "security, structure, and clarity. Give detailed but concise feedback."
                ),
            },
            {"role": "user", "content": f"Review this code:\n\n{code_text}"},
        ],
        max_tokens=900,
        temperature=0.25,
    )
    return resp.choices[0].message.content

def apply_fixes_with_agent(code_text: str, review_text: str) -> str:
    """Agent applies fixes from Architect's review autonomously."""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are the Agent. Rewrite the provided Python code by applying "
                    "all improvements mentioned in the Architect review. Return only the full corrected code."
                ),
            },
            {"role": "user", "content": f"Architect Review:\n{review_text}\n\nOriginal Code:\n{code_text}"},
        ],
        max_tokens=1300,
        temperature=0.35,
    )
    return resp.choices[0].message.content

# =========================
# HEADER
# =========================
st.title("🧠 UltimateAI IDE — Replit-Style Autonomous Flow")
st.caption("Agent → Architect → Auto-Fix → Run")

# =========================
# EDITOR (Reference)
# =========================
st.markdown("## 💻 Code Editor")
try:
    from streamlit_ace import st_ace
    code = current_file.read_text() if current_file else ""
    edited = st_ace(value=code, language="python", theme="twilight", min_lines=18, key="ace_editor")
except Exception:
    edited = st.text_area("Code", value=current_file.read_text() if current_file else "", height=320)

if st.button("💾 Save"):
    if current_file:
        current_file.write_text(edited)
        st.success(f"Saved {current_file.name}")

# =========================
# REPLIT-STYLE FLOW
# =========================
st.markdown("---")
st.header("🤖 Agent (Chat-to-Build)")

prompt = st.text_area("Describe what to build or modify:", height=140)
target_file = st.text_input("Target file:", value=str(current_file.relative_to(WORKSPACE)) if current_file else "main.py")

agent_box = st.empty()
review_box = st.empty()
fix_box = st.empty()
run_box = st.empty()

if st.button("✨ Generate with Agent"):
    if not os.getenv("OPENAI_API_KEY"):
        st.error("Missing OPENAI_API_KEY.")
    elif not prompt.strip():
        st.warning("Enter a description.")
    else:
        dest = WORKSPACE / target_file
        st.info("🚧 Generating code with Agent...")
        generated = ""

        try:
            # ---- AGENT PHASE ----
            stream = client.chat.completions.stream(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are the Agent. Write full, clean, self-contained code only."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1300,
                temperature=0.35,
            )
            for event in stream.iter_events():
                if event.type == "message.delta" and event.delta.content:
                    generated += event.delta.content
                    agent_box.code(generated, language="python")

            dest.write_text(generated)
            st.success(f"✅ Code generated and saved to {dest}")

            # ---- ARCHITECT PHASE ----
            st.info("🏗️ Architect reviewing generated code...")
            review_text = architect_review(generated)
            review_box.markdown("### 🧾 Architect Review")
            review_box.write(review_text)

            # ---- AUTO-FIX PHASE ----
            st.info("🤝 Applying Architect’s fixes automatically...")
            fixed_code = apply_fixes_with_agent(generated, review_text)

            show_split_diff(generated, fixed_code)
            dest.write_text(fixed_code)
            fix_box.success("✅ Auto-fixed file saved.")

            # ---- RUN PHASE ----
            st.info("🚀 Running final version…")
            run_output = run_file(dest)
            run_box.code(run_output, language="bash")

        except Exception as e:
            st.error(f"Process failed: {e}")

# =========================
# TERMINAL
# =========================
st.markdown("---")
st.header("💻 Terminal")

if "terminal_history" not in st.session_state:
    st.session_state.terminal_history = ""

cmd = st.text_input("Enter shell command:", placeholder="e.g., ls -la, pip list, python main.py")

c1, c2 = st.columns([1, 1])
with c1:
    run_cmd = st.button("▶️ Run Command")
with c2:
    if st.button("🧹 Clear Terminal"):
        st.session_state.terminal_history = ""
        st.experimental_rerun()

term_box = st.empty()

if run_cmd and cmd.strip():
    try:
        process = subprocess.Popen(
            cmd, shell=True, cwd=str(WORKSPACE),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        for line in process.stdout:
            st.session_state.terminal_history += line
            term_box.code(st.session_state.terminal_history, language="bash")
        process.wait()
    except Exception as e:
        st.session_state.terminal_history += f"\n⚠️ Error: {e}\n"
        term_box.code(st.session_state.terminal_history, language="bash")

term_box.code(st.session_state.terminal_history or "(Terminal idle…)", language="bash")

st.markdown("---")
st.caption("Replit-Style IDE • Agent → Architect → Auto-Fix → Run • Dark Theme")


