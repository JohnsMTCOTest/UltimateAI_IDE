
import streamlit as st
import subprocess

def git_controls(project_path):
    st.subheader('Git Controls')
    if st.button('Init Git Repo'):
        subprocess.run(['git','init'], cwd=project_path)
        st.success('Git repo initialized')

    commit_msg = st.text_input('Commit message','Update project')
    if st.button('Commit Changes'):
        subprocess.run(['git','add','.'], cwd=project_path)
        subprocess.run(['git','commit','-m', commit_msg], cwd=project_path)
        st.success('Changes committed')
