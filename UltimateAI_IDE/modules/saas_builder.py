from modules.code_generator import generate_code

def build_saas(prompt):
    return generate_code(prompt + ' as SaaS')