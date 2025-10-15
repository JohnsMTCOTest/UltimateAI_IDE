import subprocess

def run_code(code_str):
    try:
        with open('temp_code.py','w') as f:
            f.write(code_str)
        result = subprocess.run(['python','temp_code.py'], capture_output=True, text=True)
        return result.stdout + result.stderr
    except Exception as e:
        return str(e)