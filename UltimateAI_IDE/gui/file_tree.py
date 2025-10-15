
import streamlit as st
import os
import shutil

def file_tree(project_path):
    st.subheader('Project File Tree')
    for root, dirs, files in os.walk(project_path):
        level = root.replace(project_path, '').count(os.sep)
        indent = '  ' * level
        st.text(f'{indent}{os.path.basename(root)}/')
        subindent = '  ' * (level + 1)
        for f in files:
            st.text(f'{subindent}{f}')

    st.subheader('Move File')
    tree_files = [os.path.join(dp, f) for dp, dn, fn in os.walk(project_path) for f in fn]
    source_file = st.selectbox('Select file to move', tree_files)
    destination_folder = st.text_input('Destination folder (relative to project)')

    if st.button('Move File'):
        if source_file and destination_folder:
            dest_path = os.path.join(project_path, destination_folder)
            os.makedirs(dest_path, exist_ok=True)
            shutil.move(source_file, dest_path)
            st.success(f'Moved {os.path.basename(source_file)} to {dest_path}')
