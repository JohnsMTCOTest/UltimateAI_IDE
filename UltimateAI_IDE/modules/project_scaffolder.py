import os, shutil, subprocess, uuid

def scaffold_project(template_name, new_project_name=None):
    templates_dir = 'templates'
    projects_dir = 'projects'
    if not new_project_name:
        new_project_name = f'{template_name}_{uuid.uuid4().hex[:6]}'
    template_path = os.path.join(templates_dir, template_name)
    project_path = os.path.join(projects_dir, new_project_name)
    if not os.path.exists(template_path):
        raise FileNotFoundError(f'Template {template_name} not found')
    shutil.copytree(template_path, project_path)
    subprocess.run(['git','init'], cwd=project_path)
    frontend_path = os.path.join(project_path,'frontend')
    if os.path.exists(os.path.join(frontend_path,'package.json')):
        subprocess.run(['npm','install'], cwd=frontend_path)
    return project_path