import random

from .rename_utils import generate_random_name


def generate_dummy_function():
    name = generate_random_name('func')
    num1 = random.randint(1, 10000)
    num2 = random.randint(1, 10000)
    operator = random.choice(['+', '-', '*', '%'])

    return f'func {name}() -> Int {{\n\t\treturn {num1} {operator} {num2}\n\t}}'


def generate_dummy_protocol(name, function):
    declaration = function.split('{')[0]
    return f'protocol {name} {{\n\t{declaration}\n}}'


def generate_dummy_extension(protocol_name):
    function = generate_dummy_function()
    return f'extension {protocol_name} {{\n\t{function}\n}}'


def generate_conforming_class(class_name, protocol_name, function):
    another_function = generate_dummy_function()
    return f'class {class_name}: {protocol_name} {{\n\t{function}\n\t{another_function}\n}}'


def generate_file_content(class_name):
    protocol_name = generate_random_name('protocol')
    function = generate_dummy_function()

    protocol = generate_dummy_protocol(protocol_name, function)

    content = f'import Foundation\n\n{protocol}\n\n'
    for i in range(100):
        content += generate_dummy_extension(protocol_name) + '\n\n'

    conforming_class = generate_conforming_class(class_name, protocol_name, function)
    content += conforming_class
    return content


def add_dummy_files(project):
    root = '/'.join(list(project.keys())[0].split('/')[:4])
    dummy_folder = f'{root}/DUMMY'

    for i in range(len(project) * 10):
        class_name = generate_random_name('Type')
        content = generate_file_content(class_name)
        project[f'{dummy_folder}/{class_name}.swift'] = content

    return project