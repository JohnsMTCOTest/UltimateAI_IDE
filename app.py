import os
import psutil
import shlex
import subprocess
import streamlit as st
from pathlib import Path
from openai import OpenAI
import importlib.metadata

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="UltimateAI IDE", layout="wide")
WORKSPACE = Path("workspace")
WORKSPACE.mkdir(exist_ok=True)
DEFAULT_FILE = WORKSPACE / "main.py"
DEFAULT_FILE.touch(exist_ok=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

try:
    openai_version = importlib.metadata.version("openai")
except importlib.metadata.PackageNotFoundError:
    openai_version = "0.0.0"

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
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 🧩 Before (Agent Output)")
        st.code(before, language="python")
    with col2:
        st.markdown("#### ⚙️ After (Auto-Fixed by Architect)")
        st.code(after, language="python")

def architect_review(code_text: str) -> str:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are the Architect. Review Python code for quality and clarity."},
            {"role": "user", "content": f"Review this code:\n\n{code_text}"},
        ],
        max_tokens=900,
        temperature=0.25,
    )
    return resp.choices[0].message.content

def apply_fixes_with_agent(code_text: str, review_text: str) -> str:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are the Agent. Apply all suggested fixes and return corrected code."},
            {"role": "user", "content": f"Architect Review:\n{review_text}\n\nOriginal Code:\n{code_text}"},
        ],
        max_tokens=1300,
        temperature=0.35,
    )
    return resp.choices[0].message.content


# =========================
# HEADER
# =========================
st.title("🧠 UltimateAI IDE — Replit-Style Tabs")
st.caption("Agent • Editor • Console • Terminal")

# =========================
# MAIN TAB STRUCTURE
# =========================
tab_agent, tab_editor, tab_console, tab_terminal = st.tabs(
    ["🤖 Agent", "💻 Editor", "🧪 Console", "💬 Terminal"]
)

# ---------------------------------------------------------
# TAB 1 — AGENT
# ---------------------------------------------------------
with tab_agent:
    st.header("🤖 AI Agent (Chat-to-Build)")
    prompt = st.text_area("Describe what to build or modify:", height=140)
    target_file = st.text_input("Target file:", value=str(current_file.relative_to(WORKSPACE)) if current_file else "main.py")

    agent_box = st.empty()
    review_box = st.empty()
    fix_box = st.empty()
    run_box = st.empty()

    if st.button("✨ Generate with Agent", key="agent_generate"):
        if not os.getenv("OPENAI_API_KEY"):
            st.error("Missing OPENAI_API_KEY.")
        elif not prompt.strip():
            st.warning("Enter a description.")
        else:
            dest = WORKSPACE / target_file
            st.info(f"🚧 Generating code with Agent... (OpenAI v{openai_version})")
            generated = ""

            try:
                # ---- AGENT PHASE ----
                try:
                    stream = client.chat.completions.stream(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are the Agent. Write full, clean, self-contained code only."},
                            {"role": "user", "content": prompt},
                        ],
                        max_tokens=1300,
                        temperature=0.35,
                    )
                    iterator = getattr(stream, "iter_events", lambda: stream)()
                    for event in iterator:
                        delta = getattr(event, "delta", None)
                        if delta and getattr(delta, "content", None):
                            generated += delta.content
                            agent_box.code(generated, language="python")

                except Exception as stream_error:
                    st.warning(f"⚠️ Streaming failed ({stream_error}); using non-streaming mode.")
                    resp = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are the Agent. Return complete Python code only."},
                            {"role": "user", "content": prompt},
                        ],
                        max_tokens=1300,
                        temperature=0.35,
                    )
                    generated = resp.choices[0].message.content
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
                try:
                    run_output = run_file(dest)
                    st.markdown("### 🧪 Console Output")
                    if not run_output.strip():
                        run_box.warning("⚠️ No output captured from script.")
                    else:
                        run_box.code(run_output, language="bash")
                except subprocess.TimeoutExpired:
                    run_box.error("❌ Script timed out.")
                except FileNotFoundError:
                    run_box.error(f"⚠️ File not found: {dest}")
                except Exception as e:
                    run_box.error(f"⚠️ Error while running script: {e}")

            except Exception as e:
                st.error(f"Process failed: {e}")

# ---------------------------------------------------------
# TAB 2 — EDITOR
# ---------------------------------------------------------
with tab_editor:
    st.header("💻 Code Editor")
    try:
        from streamlit_ace import st_ace
        code = current_file.read_text() if current_file else ""
        edited = st_ace(value=code, language="python", theme="twilight", min_lines=18, key="ace_editor")
    except Exception:
        edited = st.text_area("Code", value=current_file.read_text() if current_file else "", height=320)

    if st.button("💾 Save", key="editor_save"):
        if current_file:
            current_file.write_text(edited)
            st.success(f"Saved {current_file.name}")

# ---------------------------------------------------------
# TAB 3 — CONSOLE
# ---------------------------------------------------------
with tab_console:
    st.header("🧪 Console (Run Selected File)")
    console_col1, console_col2 = st.columns([1, 3])
    with console_col1:
        run_now = st.button("▶️ Run Selected File", key="console_run")
    with console_col2:
        console_output = st.empty()

    if run_now and current_file:
        output = run_file(current_file)
        if not output.strip():
            console_output.warning("⚠️ No output captured from script.")
        else:
            console_output.code(output, language="bash")

# ---------------------------------------------------------
# TAB 4 — TERMINAL
# ---------------------------------------------------------
with tab_terminal:
    st.header("💬 Terminal")
    if "terminal_history" not in st.session_state:
        st.session_state.terminal_history = ""

    cmd = st.text_input("Enter shell command:", placeholder="e.g., ls -la, pip list, python main.py")

    c1, c2 = st.columns([1, 1])
    with c1:
        run_cmd = st.button("▶️ Run Command", key="terminal_run")
    with c2:
        if st.button("🧹 Clear Terminal", key="terminal_clear"):
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
st.caption("Replit-Style IDE • Tabs: Agent | Editor | Console | Terminal • Persistent Workspace")

