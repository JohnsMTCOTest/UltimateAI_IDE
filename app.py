import os
import subprocess
import shlex
from pathlib import Path

import psutil
import streamlit as st
from streamlit_ace import st_ace

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="UltimateAI IDE", layout="wide")
WORKSPACE = Path("workspace")
TEMPLATE_DIR = WORKSPACE / "templates"
MAIN_FILE = WORKSPACE / "app.py"
INDEX_FILE = TEMPLATE_DIR / "index.html"
STYLE_FILE = TEMPLATE_DIR / "style.css"
WORKSPACE.mkdir(exist_ok=True)
TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)

# =========================
# AUTO-CREATE FILES
# =========================
if not MAIN_FILE.exists():
    MAIN_FILE.write_text("""\
from flask import Flask, render_template
app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
""")

if not INDEX_FILE.exists():
    INDEX_FILE.write_text("""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>PassageCare — Compassionate Funeral Services</title>
  <link rel="stylesheet" href="style.css" />
</head>
<body>
  <header class="hero">
    <h1>PassageCare</h1>
    <p>Modern tools. Timeless compassion.</p>
    <a href="#services" class="cta">Explore Services</a>
  </header>

  <section id="services" class="section">
    <h2>Our Services</h2>
    <div class="grid">
      <div class="card">
        <h3>Funeral Coordination</h3>
        <p>From planning to ceremony — handled with care and dignity.</p>
      </div>
      <div class="card">
        <h3>Cremation Options</h3>
        <p>Personalized cremation services guided by compassion.</p>
      </div>
      <div class="card">
        <h3>Memorial Design</h3>
        <p>Modern, customizable memorial tributes built for remembrance.</p>
      </div>
    </div>
  </section>

  <section id="about" class="section alt">
    <h2>About PassageCare</h2>
    <p>We blend modern technology with empathy — providing families with transparency, efficiency, and grace in every detail of the funeral process.</p>
  </section>

  <footer>
    <p>&copy; 2025 PassageCare. Compassion. Innovation. Integrity.</p>
  </footer>
</body>
</html>
""")

if not STYLE_FILE.exists():
    STYLE_FILE.write_text("""\
body {
  font-family: 'Inter', sans-serif;
  margin: 0;
  background: #f7f8fa;
  color: #333;
  line-height: 1.6;
}
.hero {
  background: linear-gradient(135deg, #5a6fa3, #a0b3d9);
  color: white;
  text-align: center;
  padding: 5rem 1rem;
}
.hero h1 {
  font-size: 3rem;
  margin-bottom: 0.5rem;
}
.hero p {
  font-size: 1.25rem;
  opacity: 0.9;
}
.cta {
  background: white;
  color: #5a6fa3;
  padding: 0.75rem 1.5rem;
  border-radius: 50px;
  text-decoration: none;
  font-weight: bold;
  display: inline-block;
  margin-top: 1rem;
  transition: all 0.3s ease;
}
.cta:hover {
  background: #f0f0f0;
}
.section {
  padding: 4rem 2rem;
  max-width: 900px;
  margin: auto;
}
.section h2 {
  text-align: center;
  color: #5a6fa3;
  margin-bottom: 2rem;
}
.grid {
  display: grid;
  gap: 1.5rem;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
}
.card {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  text-align: center;
  transition: transform 0.2s ease;
}
.card:hover {
  transform: translateY(-5px);
}
.alt {
  background: #eef1f7;
  text-align: center;
}
footer {
  background: #5a6fa3;
  color: white;
  text-align: center;
  padding: 1rem;
}
""")

# =========================
# SIDEBAR FILE EXPLORER
# =========================
st.sidebar.title("📁")

def list_files(root):
    return sorted([p for p in root.rglob("*") if p.is_file()])

files = list_files(WORKSPACE)
rel_paths = [str(p.relative_to(WORKSPACE)) for p in files]
default_file = "app.py" if "app.py" in rel_paths else rel_paths[0] if rel_paths else None
selected_file = st.sidebar.selectbox("Select File", rel_paths, index=rel_paths.index(default_file) if default_file else 0)
current_file = WORKSPACE / selected_file if selected_file else None

# =========================
# MAIN LAYOUT
# =========================
tab1, tab2, tab3 = st.tabs(["💻", "🧪", "🌐"])

# ---- Editor ----
with tab1:
    st.subheader("💻")
    code = current_file.read_text() if current_file and current_file.exists() else ""
    content = st_ace(value=code, language="python", theme="twilight", key="ace_editor", min_lines=20)
    if st.button("💾"):
        if current_file:
            current_file.write_text(content)
            st.success(f"Saved {current_file.name}")

# ---- Console ----
with tab2:
    st.subheader("🧪")
    def run_file(path: Path):
        rel_path = path.relative_to(WORKSPACE)
        cmd = f"python -u {shlex.quote(str(rel_path))}"
        proc = subprocess.Popen(
            cmd, shell=True, cwd=str(WORKSPACE),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        log_area = st.empty()
        logs = []
        for line in proc.stdout:
            logs.append(line)
            log_area.code("".join(logs), language="bash")

    if st.button("▶️"):
        if current_file and current_file.suffix == ".py":
            st.info("Running Flask app in background...")
            run_file(current_file)
        else:
            st.warning("Select a .py file to run.")

# ---- Preview ----
with tab3:
    st.subheader("🌐")
    if INDEX_FILE.exists():
        html = (INDEX_FILE.read_text()
                .replace('href=\"style.css\"', f'href=\"{STYLE_FILE.name}\"')
                .replace('src=\"', f'src=\"{TEMPLATE_DIR}/'))
        st.components.v1.html(html, height=700, scrolling=True)
    else:
        st.info("No HTML found to preview.")

# ---- System Stats ----
cpu = psutil.cpu_percent(interval=0.2)
ram = psutil.virtual_memory().percent
st.sidebar.markdown("---")
st.sidebar.write(f"CPU: {cpu}% | RAM: {ram}%")


