import os
import streamlit as st

# Use Render’s PORT or default for local dev
port = int(os.environ.get("PORT", 8501))

# Set Streamlit config
st.set_page_config(page_title="UltimateAI_IDE", layout="wide")

# ---- Page Header ----
st.title("UltimateAI_IDE")
st.markdown("**Status:** Initial deployment successful! Render app is running.")

# ---- Layout: 2 Columns for Agent and Architect ----
col1, col2 = st.columns(2)

with col1:
    st.header("Agent Workspace")
    st.write("This is where the Agent will generate and preview code.")
    st.text_area("Agent Output", height=300, placeholder="Agent output will appear here...")

with col2:
    st.header("Architect Workspace")
    st.write("This is where the Architect reviews Agent code and approves or requests changes.")
    st.text_area("Architect Feedback", height=300, placeholder="Architect feedback will appear here...")

# ---- Bottom Section: Controls ----
st.markdown("---")
st.write("Controls Panel (for future buttons, file uploads, and other actions)")
st.button("Run Agent")
st.button("Approve Code")
st.button("Request Changes")

from modules.load_models import load_models
from modules.app_builder import build_app
from modules.saas_builder import build_saas
from modules.reasoning import plan_project
from modules.sandbox_runner import run_code
from prompts.templates import TO_DO_APP, SAAS_CRM, BLOG_APP
from gui.file_tree import file_tree
from gui.multi_file_editor import multi_file_editor
from gui.frontend_preview import live_preview, start_react_dev_server
from gui.git_integration import git_controls
from modules.project_scaffolder import scaffold_project

os.makedirs('projects', exist_ok=True)
st.title('Ultimate Personal AI IDE')
st.text('Loading AI models...')
load_models()
st.success('AI models loaded!')

mode = st.sidebar.selectbox('Mode', ['Plan Project','Build App','Generate & Test Code','Build SaaS'])
template_choice = st.sidebar.selectbox('Template', ['None','To-Do App','SaaS CRM','Blog App'])
templates = {'To-Do App': TO_DO_APP,'SaaS CRM': SAAS_CRM,'Blog App': BLOG_APP}

if template_choice != 'None':
    user_prompt = templates[template_choice]
else:
    user_prompt = st.text_area('Enter prompt:')

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
        frontend_file = os.path.join(project_path, 'frontend', 'public', 'index.html')
        live_preview(frontend_file)
    except Exception as e:
        st.error(str(e))

if st.button('Run'):
    if not user_prompt.strip():
        st.warning('Enter prompt or select template!')
    else:
        project_name = f'{mode.replace(" ","_")}_Project'
        if mode=='Plan Project':
            plan = plan_project(user_prompt)
            st.subheader('Project Plan')
            st.code(plan)
        elif mode=='Build App':
            code = build_app(user_prompt)
            project_path = os.path.join('projects', project_name)
            os.makedirs(project_path, exist_ok=True)
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
            project_path = os.path.join('projects', project_name)
            os.makedirs(project_path, exist_ok=True)
            with open(os.path.join(project_path,'main.py'),'w') as f:
                f.write(code)
            st.subheader('Generated SaaS Code')
            st.code(code)
            multi_file_editor(project_path)
            file_tree(project_path)
            git_controls(project_path)
