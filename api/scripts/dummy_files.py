import random

from .rename_utils import generate_random_name


def generate_dummy_body(return_type, loop, operator):
    string = generate_random_name()
    n1 = random.randint(1, 10000)
    n2 = random.randint(1, 10000)
    f1 = random.uniform(1, 10000)
    f2 = random.uniform(1, 10000)

    if return_type == 'Int':
        if loop:
            return f'''
            var {string} = {int(f1)}
            for i in 0...{n1} {{
                {string} = {string} {operator} {int(f2)}
            }}
            return {string}
            '''
        else:
            return f'return {n1} {operator} {n2}'
    elif return_type == 'String':
        if loop:
            return f'var {string} = "{string}"\n\t\tfor i in 0...{n1} {{\n\t\t\t{string} += "{string}"\n\t\t}}\n\t\treturn {string}'
        else:
            return f'return "{string}"'
    elif return_type == 'Bool':
        if loop:
            return f'''
            var {string} = {f1}
            for i in 0...{n1} {{
                {string} = {string} {operator} {f2}
            }}
            return {string} {random.choice(['>', '<', '==', '!='])} {n2}
            '''
        else:
            return f"return {n1} {random.choice(['>', '<', '==', '!='])} {n2}"
    elif return_type == 'Double':
        if loop:
            return f'''
            var {string} = {f1}
            for i in 0...{n1} {{
                {string} = {string} {operator} {f2}
            }}
            return {string}
            '''
        else:
            return f'return {f1} {operator} {f2}'
    elif return_type == 'Float':
        if loop:
            return f'''
            var {string} = {f1}
            for i in 0...{n1} {{
                {string} = {string} {operator} {f2}
            }}
            return Float({string})
            '''
        else:
            return f'return Float({f1} {operator} {f2})'
    elif return_type == 'Void':
        if loop:
            return f'''
            for i in 0...{n1} {{
                print("{string}")
                }}
            '''
        else:
            return f'print("{string}")'


def generate_dummy_function():
    name = generate_random_name('func')

    return_type = random.choice(['Int', 'String', 'Bool', 'Double', 'Float', 'Void'])

    condition = random.choice([True, False])
    loop = random.choice([True, False])
    operator = random.choice(['+', '-', '*'])

    if condition:
        i = random.randint(1, 10000)
        j = random.randint(1, 10000)

        res = f'''
        func {name}() -> {return_type} {{
            if {i} {random.choice(['>', '<', '==', '!='])} {j} {{
                {generate_dummy_body(return_type, loop, operator)}
            }}
            else {{
                {generate_dummy_body(return_type, loop, operator)}
            }}
        }}
        '''
        return res
    else:
        return f'func {name}() -> {return_type} {{\n\t\t{generate_dummy_body(return_type, loop, operator)}\n\t}}'


def generate_dummy_protocol(name, function):
    declaration = function.split('{')[0]
    return f'protocol {name} {{\n\t{declaration}\n}}'


def generate_dummy_extension(protocol_name):
    function = generate_dummy_function()
    return f'extension {protocol_name} {{\n\t{function}\n}}'


def generate_conforming_class(class_name, protocol_name, function):
    other_functions = '\n\t'.join([generate_dummy_function() for _ in range(10)])
    return f'class {class_name}: {protocol_name} {{\n\t{function}\n\t{other_functions}\n}}'


def generate_dummy_enum():
    name = generate_random_name('enum')
    cases = [generate_random_name('case') for _ in range(random.randint(1, 20))]
    cases = '\n\t'.join(cases)
    enum = f'enum {name} {{\n\t{cases}\n}}'
    return enum


def generate_file_content(class_name):
    protocol_name = generate_random_name('protocol')
    function = generate_dummy_function()

    protocol = generate_dummy_protocol(protocol_name, function)

    content = f'import Foundation\n\n{protocol}\n\n'
    for i in range(100):
        content += generate_dummy_extension(protocol_name) + '\n\n'

    for i in range(10):
        content += generate_conforming_class(class_name, protocol_name, function) + '\n\n'

    for i in range(100):
        content += generate_dummy_enum() + '\n\n'

    return content


def add_dummy_files(project, number=10, root=None):
    try:
        root = '/'.join(list(project.keys())[0].split('/')[:4])
    except IndexError:
        print('No files in project')
    dummy_folder = f'{root}/DUMMY'

    for i in range(len(project) * number):
        class_name = generate_random_name('Type')
        content = generate_file_content(class_name)
        project[f'{dummy_folder}/{class_name}.swift'] = content

    return project
