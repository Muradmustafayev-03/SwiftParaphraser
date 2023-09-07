import random
import regex as re
from .constants import *


def open_abbreviation(name: str):
    """
    Replaces abbreviations with their full form and vice versa.
    """
    abbreviations = list(ABBREVIATIONS.items())
    random.shuffle(abbreviations)
    for abbr, opening in abbreviations:
        if opening in name:
            name = name.replace(opening, abbr)
        elif abbr in name:
            name = name.replace(abbr, opening)
    return name


def first_letter_upper(name: str):
    """
    Capitalizes the first letter of the name.
    """
    return name[0].upper() + name[1:] if len(name) > 0 else name


def first_letter_lower(name: str):
    """
    Makes the first letter of the name lowercase.
    """
    return name[0].lower() + name[1:] if len(name) > 0 else name


def generate_random_name(prefix='', suffix=''):
    """
    Generates a random name.

    :param prefix: prefix to add to the name
    :param suffix: suffix to add to the name
    :return: generated name
    """
    name = ''
    for _ in range(random.randint(5, 15)):
        letter = random.choice(ALPHABET)
        if random.random() < 0.2:
            letter = letter.upper()
        name += letter
    name = first_letter_upper(name) if prefix else first_letter_lower(name)
    name = prefix + name + suffix
    return name


def new_var_name(name: str):
    """
    Generates a new variable name based on the old one or generates a random name.

    :param name: old variable name
    :return: new variable name
    """
    name = open_abbreviation(name)
    name = first_letter_upper(name)

    prefix = random.choice(['var', 'variable', 'value'])

    if random.choice([True, False]):
        return prefix + random.choice(ADJECTIVES) + name
    else:
        return generate_random_name(prefix)


def new_func_name(name: str):
    """
    Generates a new function name based on the old one or generates a random name.

    :param name: old function name
    :return: new function name
    """
    name = open_abbreviation(name)
    name = first_letter_lower(name)

    prefix = random.choice(['func', 'function'])
    return prefix + random.choice(ADJECTIVES) + name


def new_type_name(name: str):
    """
    Generates a new type name based on the old one or generates a random name.

    :param name: old type name
    :return: new type name
    """
    name = open_abbreviation(name)
    name = first_letter_upper(name)

    if random.choice([True, False]):
        return 'Type' + random.choice(ADJECTIVES) + name
    else:
        return generate_random_name('Type')


def rename_local_variables(code, functions: list):
    """
    Renames local variables in the code.

    :param code: source code
    :param functions: list of functions in the code
    :return: code with renamed local variables
    """
    for function in functions:
        func_body = function[function.find('{') + 1:function.rfind('}')]
        var_pattern = r'(?<!override)\s*var\s+([a-zA-Z_]+)'
        variables = re.finditer(var_pattern, function)

        for var_match in variables:
            var_name = var_match.group(1)
            new_name = new_var_name(var_name)

            old_pattern = rf'(?<![a-zA-Z_.]){var_name}(?![a-zA-Z_])'

            # exclude declaration and assignment to itself at the same time
            if re.search(rf'var\s+{var_name}\s*=\s*{var_name}', function):
                continue
            if re.search(rf'var\s+{var_name}\s*:\s*{var_name}', function):
                continue

            new_func_body = re.sub(old_pattern, new_name, func_body)
            new_function = function.replace(func_body, new_func_body)
            code = code.replace(function, new_function)

    return code


def parse_type_names(swift_code: str, include_types: tuple = ('class', 'struct', 'enum')):
    """
    Parses type names from the Swift code. Types are specified in the include_types parameter.

    :param swift_code: Swift code to parse
    :param include_types: tuple of types to parse
    :return: list of parsed type names
    """
    names = []

    for typedef in include_types:
        pattern = rf'{typedef}\s+([A-Z][a-zA-Z0-9_]+)\s*(:|\{{)'
        matches = re.finditer(pattern, swift_code)
        for match in matches:
            names.append(match.group(1))

    names = list(set(names))
    if 'SceneDelegate' in names:
        names.remove('SceneDelegate')
    if 'AppDelegate' in names:
        names.remove('AppDelegate')
    return names


def parse_types_in_project(project: dict, include_types: tuple = ('class', 'struct', 'enum')):
    """
    Parses type names from the project. Types are specified in the include_types parameter.

    :param project: dict, project to parse
    :param include_types: tuple of types to parse
    :return: list of parsed type names
    """
    names = []

    for file_path, file_content in project.items():
        if 'AppDelegate' in file_path or 'SceneDelegate' in file_path:
            continue
        if file_path.endswith('.swift'):
            names += parse_type_names(file_content, include_types)
    return list(set(names))


def generate_rename_map(names: list):
    """
    Generates a renaming map (dictionary) for the given names.


    :param names: names to rename
    :return: dict, renaming map in the format {old_name: new_name}
    """
    return {name: new_type_name(name) for name in names}


def rename_type(project: dict, old_name: str, new_name: str, rename_files: bool = False):
    """
    Renames the type in the project. If rename_files is True, the files will be renamed as well.

    :param project: project to rename the type in
    :param old_name: old type name
    :param new_name: new type name
    :param rename_files: bool, whether to rename files or not
    :return: dict, renamed project
    """
    new_project = {}
    renamed_files = []

    for file_path, file_content in project.items():
        if file_path.endswith('.swift'):
            new_path = file_path

            if file_path.split('/')[-1] == old_name + '.swift' and rename_files:
                new_path = file_path.replace(old_name + '.swift', new_name + '.swift')
                renamed_files.append((old_name, new_name))

            # pattern if not declaration variable or function name
            pattern = r'\b' + re.escape(old_name) + r'\b'
            new_project[new_path] = re.sub(pattern, new_name, file_content)
            continue

        elif file_path.endswith('.xib') or file_path.endswith('.storyboard'):
            pattern = r'customClass="' + re.escape(old_name) + r'"'
            new_content = re.sub(pattern, r'customClass="' + new_name + r'"', file_content)

            for old_filename, new_filename in renamed_files:
                pattern = r'customModule="' + re.escape(old_filename) + r'"'
                new_content = re.sub(pattern, r'customModule="' + new_filename + r'"', new_content)

            new_project[file_path] = new_content
            continue

        elif file_path.endswith('.xml') or file_path.endswith('.pbxproj') or file_path.endswith('.plist'):
            pattern = r'>' + re.escape(old_name) + r'<'
            new_project[file_path] = re.sub(pattern, r'>' + new_name + r'<', file_content)
            continue

        else:
            new_project[file_path] = file_content
            continue

    return new_project


def rename_types(project: dict, rename_map: dict, rename_files=False):
    """
    Renames types in the project according to the renaming map.

    :param project: project to rename types in
    :param rename_map: renaming map in the format {old_name: new_name}
    :param rename_files: bool, whether to rename files or not
    :return: dict, renamed project
    """
    for old_name, new_name in rename_map.items():
        project = rename_type(project, old_name, new_name, rename_files)
    return project
