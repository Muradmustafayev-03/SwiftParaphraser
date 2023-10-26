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
    extension = generate_dummy_extension(protocol_name)

    conforming_class = generate_conforming_class(class_name, protocol_name, function)
    return f'{protocol}\n\n{extension}\n\n{conforming_class}'
