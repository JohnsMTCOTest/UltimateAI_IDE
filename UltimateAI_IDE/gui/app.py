import sys
import os
import streamlit as st

# -------------------------------
# Absolute path to UltimateAI_IDE root
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # go up from gui/ to UltimateAI_IDE
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)
# -------------------------------
# Configure Streamlit for Render
# -------------------------------
# Use Render's PORT or default 8501
port = int(os.environ.get("PORT", 8501))
os.environ["STREAMLIT_SERVER_PORT"] = str(port)
os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
os.environ["STREAMLIT_SERVER_ENABLECORS"] = "false"
os.environ["STREAMLIT_SERVER_ADDRESS"] = "0.0.0.0"

# -------------------------------
# Imports from your modules
# -------------------------------
from modules.load_models import load_models
from modules.app_builder import build_app
from modules.saas_builder import build_saas
from modules.reasoning import plan_project
from modules.sandbox_runner import run_code
from modules.project_scaffolder import scaffold_project

from prompts.templates import TO_DO_APP, SAAS_CRM, BLOG_APP
from gui.file_tree import file_tree
from gui.multi_file_editor import multi_file_editor
from gui.frontend_preview import live_preview
from gui.git_integration import git_controls

# -------------------------------
# Streamlit Config
# -------------------------------
st.set_page_config(page_title="UltimateAI_IDE", layout="wide")
st.title("UltimateAI_IDE")
st.markdown("**Status:** Initial deployment successful! Render app is running.")
st.text(f"Streamlit running on port {port}")

# -------------------------------
# Layout: 2 Columns for Agent & Architect
# -------------------------------
col1, col2 = st.columns(2)

with col1:
    st.header("Agent Workspace")
    st.write("This is where the Agent will generate and preview code.")
    st.text_area("Agent Output", height=300, placeholder="Agent output will appear here...")

with col2:
    st.header("Architect Workspace")
    st.write("This is where the Architect reviews Agent code and approves or requests changes.")
    st.text_area("Architect Feedback", height=300, placeholder="Architect feedback will appear here...")

# -------------------------------
# Bottom Controls Panel
# -------------------------------
st.markdown("---")
st.write("Controls Panel (for future buttons, file uploads, and other actions)")
st.button("Run Agent")
st.button("Approve Code")
st.button("Request Changes")

# -------------------------------
# Ensure projects folder exists
# -------------------------------
os.makedirs('projects', exist_ok=True)

# -------------------------------
# Load AI Models
# -------------------------------
st.text('Loading AI models...')
load_models()
st.success('AI models loaded!')

# -------------------------------
# Sidebar: Mode & Template Selection
# -------------------------------
mode = st.sidebar.selectbox('Mode', ['Plan Project','Build App','Generate & Test Code','Build SaaS'])
template_choice = st.sidebar.selectbox('Template', ['None','To-Do App','SaaS CRM','Blog App'])
templates = {'To-Do App': TO_DO_APP,'SaaS CRM': SAAS_CRM,'Blog App': BLOG_APP}

# User Prompt Handling
if template_choice != 'None':
    user_prompt = templates[template_choice]
else:
    user_prompt = st.text_area('Enter prompt:')

# -------------------------------
# Sidebar: Create New Project
# -------------------------------
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

        # Frontend live preview
        frontend_file = os.path.join(project_path, 'frontend', 'build', 'index.html')
        if os.path.exists(frontend_file):
            live_preview(frontend_file)
    except Exception as e:
        st.error(str(e))

# -------------------------------
# Run Mode Actions
# -------------------------------
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
