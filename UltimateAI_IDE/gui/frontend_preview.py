
import streamlit as st
import subprocess
import threading
import time
import os

def start_react_dev_server(project_path):
    if os.path.exists(os.path.join(project_path,'package.json')):
        def run_server():
            subprocess.run(['npm','start'], cwd=project_path)
        threading.Thread(target=run_server, daemon=True).start()
        time.sleep(5)

def live_preview(file_path):
    st.subheader('Live Frontend Preview')
    if file_path and os.path.exists(file_path):
        with open(file_path,'r') as f:
            html_code = f.read()
        st.components.v1.html(html_code, height=600, scrolling=True)
    else:
        st.warning('HTML/React entry file not found')
