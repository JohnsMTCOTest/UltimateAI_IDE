import os
import sys
import streamlit as st
import subprocess
import time
from threading import Thread

# ---- Fix Python module import ----
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ---- Imports ----
from modules.load_models import load_models
from modules.app_builder import build_app
from modules.saas_builder import build_saas
from modules.reasoning import plan_project
from modules.sandbox_runner import run_code
from modules.project_scaffolder import scaffold_project

from prompts.templates import TO_DO_APP, SAAS_CRM, BLOG_APP
from gui.file_tree import file_tree
from gui.multi_file_editor import multi_file_editor
from gui.git_integration import git_controls
from gui.frontend_preview import live_preview

# ---- Page Config ----
st.set_page_config(page_title="UltimateAI_IDE", layout="wide")
st.title("UltimateAI_IDE")
st.markdown("**Status:** Initial deployment successful! Render app is running.")

# ---- Layout: Agent & Architect ----
col1, col2 = st.columns(2)
with col1:
    st.header("Agent Workspace")
    agent_output = st.text_area("Agent Output", height=300, placeholder="Agent output will appear here...")
with col2:
    st.header("Architect Workspace")
    architect_feedback = st.text_area("Architect Feedback", height=300, placeholder="Architect feedback will appear here...")

# ---- Bottom Controls ----
st.markdown("---")
st.write("Controls Panel")
st.button("Run Agent")
st.button("Approve Code")
st.button("Request Changes")

# ---- Projects Folder ----
os.makedirs('projects', exist_ok=True)

# ---- Load AI Models (once) ----
if 'models_loaded' not in st.session_state:
    st.text("Loading AI models...")
    load_models()
    st.session_state['models_loaded'] = True
    st.success("AI models loaded!")

# ---- Sidebar: Mode & Templates ----
mode = st.sidebar.selectbox('Mode', ['Plan Project','Build App','Generate & Test Code','Build SaaS'])
template_choice = st.sidebar.selectbox('Template', ['None','To-Do App','SaaS CRM','Blog App'])
templates = {'To-Do App': TO_DO_APP,'SaaS CRM': SAAS_CRM,'Blog App': BLOG_APP}
user_prompt = templates[template_choice] if template_choice != 'None' else st.text_area('Enter prompt:')

# ---- Sidebar: New Project ----
st.sidebar.subheader('Create New Project')
template_to_use = st.sidebar.selectbox('Template for new project', ['starter_fullstack'])
new_project_name = st.sidebar.text_input('New Project Name (optional)')

if st.sidebar.button('Create Project'):
    try:
        project_path = scaffold_project(template_to_use, new_project_name)
        st.success(f'Project created at: {project_path}')
        multi_file_editor(project_path)
        file_tree(project_path)
        git_controls(project_path)
        watch_and_preview(project_path)
    except Exception as e:
        st.error(str(e))

# ---- Main Run Button ----
if st.button('Run'):
    if not user_prompt.strip():
        st.warning('Enter prompt or select template!')
    else:
        project_name = f'{mode.replace(" ","_")}_Project'
        project_path = os.path.join('projects', project_name)
        os.makedirs(project_path, exist_ok=True)

        if mode=='Plan Project':
            plan = plan_project(user_prompt)
            st.subheader('Project Plan')
            st.code(plan)

        elif mode=='Build App':
            code = build_app(user_prompt)
            with open(os.path.join(project_path,'main.py'),'w') as f:
                f.write(code)
            st.subheader('Generated App Code')
            st.code(code)
            multi_file_editor(project_path)
            file_tree(project_path)
            git_controls(project_path)
            watch_and_preview(project_path)

        elif mode=='Generate & Test Code':
            code = build_app(user_prompt)
            st.subheader('Generated Code')
            st.code(code)
            st.subheader('Sandbox Output')
            output = run_code(code)
            st.text(output)

        elif mode=='Build SaaS':
            code = build_saas(user_prompt)
            with open(os.path.join(project_path,'main.py'),'w') as f:
                f.write(code)
            st.subheader('Generated SaaS Code')
            st.code(code)
            multi_file_editor(project_path)
            file_tree(project_path)
            git_controls(project_path)
            watch_and_preview(project_path)


# ----  Hot-Reload Frontend Preview ----
def watch_and_preview(project_path):
    """
    Watch frontend/src for changes, rebuild React, and preview in Streamlit.
    """
    frontend_src = os.path.join(project_path, 'frontend', 'src')
    frontend_build = os.path.join(project_path, 'frontend', 'build', 'index.html')

    if not os.path.exists(frontend_src):
        st.info("No frontend src folder detected. Skipping live preview.")
        return

    def watcher():
        last_mod_time = 0
        while True:
            try:
                # Get latest modification time of all files in src
                current_mod = max(os.path.getmtime(os.path.join(dp, f))
                                  for dp, dn, filenames in os.walk(frontend_src) for f in filenames)
                if current_mod != last_mod_time:
                    last_mod_time = current_mod
                    st.info("Detected frontend change. Building React app...")
                    # Run npm build
                    subprocess.run(['npm', 'install'], cwd=os.path.join(project_path,'frontend'))
                    subprocess.run(['npm', 'run', 'build'], cwd=os.path.join(project_path,'frontend'))
                    st.success("Build complete!")
                    if os.path.exists(frontend_build):
                        live_preview(frontend_build)
                time.sleep(2)
            except Exception as e:
                st.error(f"Error in watcher: {e}")
                time.sleep(5)

    # Run watcher in background thread
    if 'watcher_started' not in st.session_state:
        Thread(target=watcher, daemon=True).start()
        st.session_state['watcher_started'] = True

