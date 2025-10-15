
import streamlit as st
import os

def multi_file_editor(project_path):
    st.subheader('Multi-File Editor')
    files = [os.path.join(dp, f) for dp, dn, fn in os.walk(project_path) for f in fn if f.endswith(('.py','.js','.jsx','.html','.css'))]
    selected_file = st.selectbox('Select file to edit', files)
    if selected_file:
        with open(selected_file, 'r') as f:
            code = f.read()
        edited_code = st.text_area(f'Editing {os.path.basename(selected_file)}', code, height=400)
        if st.button(f'Save {os.path.basename(selected_file)}'):
            with open(selected_file, 'w') as f:
                f.write(edited_code)
            st.success(f'{os.path.basename(selected_file)} saved!')
