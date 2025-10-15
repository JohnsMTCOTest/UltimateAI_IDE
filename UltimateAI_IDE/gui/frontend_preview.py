import streamlit as st
import os
import time
from threading import Thread
import subprocess

def live_preview(html_file_path, project_path=None, refresh_interval=2):
    """
    Display a live preview of the frontend HTML in Streamlit.
    Auto-refreshes when the file is updated. Optionally rebuilds React if project_path is provided.

    :param html_file_path: Path to build/index.html
    :param project_path: Optional project root to auto-build frontend
    :param refresh_interval: Seconds between checks
    """
    if not os.path.exists(html_file_path):
        st.error(f"File not found: {html_file_path}")
        return

    # Placeholder for live preview
    if 'preview_placeholder' not in st.session_state:
        st.session_state['preview_placeholder'] = st.empty()
    placeholder = st.session_state['preview_placeholder']

    # Track last modified time
    if 'last_mod_time' not in st.session_state:
        st.session_state['last_mod_time'] = 0

    def watcher():
        src_folder = os.path.join(project_path, 'frontend', 'src') if project_path else None
        last_src_mod = 0

        while True:
            try:
                # Auto-build if src folder provided
                if src_folder and os.path.exists(src_folder):
                    current_src_mod = max(os.path.getmtime(os.path.join(dp, f))
                                          for dp, dn, filenames in os.walk(src_folder)
                                          for f in filenames)
                    if current_src_mod != last_src_mod:
                        last_src_mod = current_src_mod
                        st.info("Detected frontend src change. Rebuilding React app...")
                        subprocess.run(['npm', 'install'], cwd=os.path.join(project_path,'frontend'))
                        subprocess.run(['npm', 'run', 'build'], cwd=os.path.join(project_path,'frontend'))
                        st.success("React build complete!")

                # Update preview if build file changed
                if os.path.exists(html_file_path):
                    current_mod_time = os.path.getmtime(html_file_path)
                    if current_mod_time != st.session_state['last_mod_time']:
                        st.session_state['last_mod_time'] = current_mod_time
                        with open(html_file_path, 'r', encoding='utf-8') as f:
                            html_content = f.read()
                        placeholder.components.v1.html(html_content, height=600, scrolling=True)

                time.sleep(refresh_interval)
            except Exception as e:
                st.error(f"Error in live preview watcher: {e}")
                time.sleep(refresh_interval)

    if 'preview_thread_started' not in st.session_state:
        Thread(target=watcher, daemon=True).start()
        st.session_state['preview_thread_started'] = True

