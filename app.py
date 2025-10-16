import os
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
# SIDEBAR: FILES + SYSTEM
# =========================
st.sidebar.title("📁 Project Files")

def list_files(root: Path):
    return sorted([p for p in root.rglob("*") if p.is_file()])

def select_file_ui():
    files = list_files(WORKSPACE)
    rel_paths = [str(p.relative_to(WORKSPACE)) for p in files] or ["(no files)"]
    selected = st.sidebar.selectbox("Select file", rel_paths, index=0)
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
# HEADER
# =========================
st.title("🧠 UltimateAI IDE — Replit-style Flow")
st.caption("Agent → (auto) Architect Review → Console → Terminal")

# =========================
# EDITOR (Reference view)
# =========================
st.markdown("## 💻 Code Editor (current file)")
try:
    from streamlit_ace import st_ace
    code = current_file.read_text() if current_file else ""
    edited = st_ace(
        value=code,
        language="python",
        theme="twilight",
        min_lines=18,
        key="ace_editor",
    )
except Exception:
    edited = st.text_area(
        "Code",
        value=current_file.read_text() if current_file else "",
        height=320,
    )

cols_save = st.columns([1, 3])
with cols_save[0]:
    if st.button("💾 Save"):
        if current_file:
            current_file.write_text(edited)
            st.success(f"Saved {current_file.name}")

# =========================
# REPLIT-STYLE VERTICAL FLOW
# =========================
st.markdown("---")
st.header("🤖 Agent (chat-to-build)")

# Agent inputs
prompt = st.text_area("Describe what to build or change", height=140, placeholder="e.g., Add a FastAPI server with /health and /items endpoints…")
target_file = st.text_input("Target file (relative to workspace/)", value=str(current_file.relative_to(WORKSPACE)) if current_file else "main.py")
stream_mode = st.checkbox("⚡ Stream generation live", value=True)
auto_run = st.checkbox("🚀 Auto-run after generation (if .py)", value=True)

# Placeholders for Agent output, Architect review, and Console run
agent_out_box = st.empty()
review_box = st.empty()
run_box = st.empty()

def run_file(path: Path, timeout=20) -> str:
    if path.suffix != ".py":
        return f"Cannot run non-Python file: {path}"
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

def architect_review(code_text: str) -> str:
    """Call the Architect to review generated code."""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are the Architect: a senior reviewer. "
                    "Provide concise findings: correctness, security, edge cases, performance, "
                    "naming/structure, and a short prioritized fix list. Use markdown bullets."
                ),
            },
            {"role": "user", "content": f"Review this code:\n\n{code_text}"},
        ],
        max_tokens=900,
        temperature=0.2,
    )
    return resp.choices[0].message.content

# Generate button: Agent → save file → Architect review → (optional) run
if st.button("✨ Generate with Agent"):
    if not os.getenv("OPENAI_API_KEY"):
        st.error("Missing OPENAI_API_KEY environment variable.")
    elif not prompt.strip():
        st.warning("Enter a description for the Agent.")
    else:
        dest = WORKSPACE / target_file
        dest.parent.mkdir(parents=True, exist_ok=True)

        st.info("Agent is generating code…")
        generated = ""

        try:
            if stream_mode:
                stream = client.chat.completions.stream(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are the Agent: write clean, complete code only. "
                                "No explanations, no backticks. If multiple files are needed, write the main target file only."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=1300,
                    temperature=0.35,
                )
                live = st.empty()
                for event in stream:
                    if event.type == "message.delta" and event.delta.content:
                        generated += event.delta.content
                        # Show the streaming code output
                        live.code(generated, language="python")
            else:
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are the Agent: return ONLY code for the requested change."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=1300,
                    temperature=0.35,
                )
                generated = resp.choices[0].message.content
                agent_out_box.code(generated, language="python")

            # Save code produced by Agent
            dest.write_text(generated)
            st.success(f"✅ Agent saved to {dest.relative_to(WORKSPACE)}")

            # Show final generated code block (even if we streamed)
            agent_out_box.code(generated, language="python")

            # Architect auto-review
            st.info("🏗️ Calling Architect for automatic review…")
            try:
                review_text = architect_review(generated)
                review_box.markdown("### 🧾 Architect Review")
                review_box.write(review_text)
            except Exception as e:
                review_box.error(f"Architect review failed: {e}")

            # Optional auto-run
            if auto_run and dest.suffix == ".py":
                st.info("🚀 Running generated code…")
                run_output = run_file(dest)
                run_box.markdown("### 🧪 Console Output")
                run_box.code(run_output, language="bash")

        except Exception as e:
            st.error(f"Agent error: {e}")

# =========================
# MANUAL CONSOLE (Run Selected File)
# =========================
st.markdown("---")
st.header("🧪 Console (Run current file)")

console_col1, console_col2 = st.columns([1, 3])
with console_col1:
    run_now = st.button("▶️ Run Selected File")
with console_col2:
    console_output = st.empty()

if run_now and current_file:
    console_output.code(run_file(current_file), language="bash")

# =========================
# TERMINAL (Interactive, persistent)
# =========================
st.markdown("---")
st.header("💻 Terminal")

if "terminal_history" not in st.session_state:
    st.session_state.terminal_history = ""

cmd = st.text_input("Enter shell command (runs in workspace/)", placeholder="e.g., ls -la, pip list, python main.py")

t1, t2 = st.columns([1, 1])
with t1:
    run_cmd = st.button("▶️ Run Command")
with t2:
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
st.caption("Replit-style vertical flow • Agent → Architect → Console → Terminal • OpenAI Streaming")
