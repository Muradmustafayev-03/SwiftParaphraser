import os
import random
import regex as re
from .file_utils import project_contains_string
from .names import *


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


def generate_random_name(prefix='', old_name='', suffix=''):
    """
    Generates a random name.

    :param old_name:
    :param prefix: prefix to add to the name
    :param suffix: suffix to add to the name
    :return: generated name
    """
    if old_name:
        name = random.choice(name_prefixes) + first_letter_upper(old_name)
    else:
        name = random.choice(name_prefixes) + random.choice(name_roots)
        name += str(random.randint(0, len(name) * 100))
    name = first_letter_upper(name) if prefix else first_letter_lower(name)
    return prefix + name + suffix


def new_var_name(name: str):
    """
    Generates a new variable name based on the old one or generates a random name.

    :param name: old variable name
    :return: new variable name
    """
    return generate_random_name(prefix='var', old_name=name)


def new_type_name(name: str):
    """
    Generates a new type name based on the old one or generates a random name.

    :param name: old type name
    :return: new type name
    """
    return generate_random_name(prefix='Type', old_name=name)


def rename_local_variables(code, function: str):
    """
    Renames local variables in the code.

    :param code: source code
    :param function: function to rename local variables in
    :return: code with renamed local variables
    """
    func_body = function[function.find('{') + 1:function.rfind('}')]
    var_pattern = r'(?<!override)\s*(var|let)\s+([a-zA-Z_]+)'
    variables = re.finditer(var_pattern, function)

    for var_match in variables:
        var_name = var_match.group(2)
        new_name = new_var_name(var_name)

        old_pattern = r'(?<![a-zA-Z_.])' + re.escape(var_name) + r'(?!\w)(?=(?:(?:[^"]*"){2})*[^"]*$)'
        new_pattern = r'\\\(' + re.escape(var_name) + r'\)'

        # exclude declaration and assignment to itself at the same time
        if re.search(rf'{var_name}\s*=\s*{var_name}', function):
            continue
        if re.search(rf'{var_name}\s*:\s*{var_name}', function):
            continue

        # check if var_name is used before declaration
        declaration_idx = function.find(var_match.group(0))
        first_occurrence_idx = function.find(var_name)
        if first_occurrence_idx < declaration_idx:
            continue

        pattern = r'\(|,' + r's*' + var_name + r':'
        if re.search(pattern, func_body):
            continue

        new_func_body = re.sub(old_pattern, new_name, func_body, flags=re.MULTILINE)
        new_func_body = re.sub(new_pattern, f'\\({new_name})', new_func_body)
        new_func_body = new_func_body.replace(f'...{var_name}', f'...{new_name}')
        new_function = function.replace(func_body, new_func_body)
        code = code.replace(function, new_function)

    return code


def rename_variables(code: str) -> str:
    """
    Renames all variables in a string to random names.

    :param code: input code string
    :return: output code string
    """

    # parsing functions
    pattern = re.compile(
        r'(?:(?<!class)(\s*?)(public|private|protected|internal|fileprivate|open|override|@objc)\s+)?(static\s+)?func\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\s*(.*?)\s*\)\s*(?:\s*->\s*(?:.*?)?)?\s*{')
    functions = [match.group(0) for match in pattern.finditer(code)]

    for declaration in functions:
        open_brackets = 1
        idx = code.find(declaration) + len(declaration)

        while open_brackets > 0 and idx < len(code):
            if code[idx] == '{':
                open_brackets += 1
            elif code[idx] == '}':
                open_brackets -= 1
            idx += 1

        if open_brackets == 0:
            entire_function = code[code.find(declaration):idx]
            code = rename_local_variables(code, entire_function)
    return code


def parse_type_names(swift_code: str, include_types: tuple = ('class', 'struct', 'enum')):
    """
    Parses type names from the Swift code. Types are specified in the include_types parameter.

    :param swift_code: Swift code to parse
    :param include_types: tuple of types to parse
    :return: list of parsed type names
    """
    names = []

    core_data_imported = 'import CoreData' in swift_code

    for typedef in include_types:
        pattern = rf'{typedef}\s+([A-Z][a-zA-Z0-9_]+)\s*(:|\{{)'
        matches = re.finditer(pattern, swift_code)
        for match in matches:
            # extract the part of the code before declaration
            code_before = swift_code[:match.start()]
            if code_before.count('{') != code_before.count('}'):
                continue
            if f'@objc({match.group(1)})' in swift_code:
                continue
            if core_data_imported and match.group(1) + ':' in match.group(0):
                continue
            names.append(match.group(1))
    return list(set(names))


def parse_framework_types(swift_code: str):
    types = ('class', 'struct', 'enum', 'protocol', 'typealias', 'extension', 'interface')
    names = []

    for typedef in types:
        pattern = rf'{typedef}\s+([A-Z][a-zA-Z0-9_]+)'
        matches = re.finditer(pattern, swift_code)
        for match in matches:
            names.append(match.group(1))

    return list(set(names))


def parse_types_in_project(project: dict,
                           include_types: tuple = ('class', 'struct', 'enum', 'protocol'),
                           exclude_names: tuple = ('SceneDelegate', 'AppDelegate', 'ContentState')):
    """
    Parses type names from the project. Types are specified in the include_types parameter.

    :param project: dict, project to parse
    :param include_types: tuple of types to parse
    :param exclude_names: tuple of names to exclude
    :return: list of parsed type names
    """
    names = []

    for file_path, file_content in project.items():
        if 'AppDelegate' in file_path or 'SceneDelegate' in file_path:
            continue
        if file_path.endswith('.swift'):
            names += parse_type_names(file_content, include_types)
    names = list(set(names))
    for name in names:
        if project_contains_string(project, f'import {name}'):
            names.remove(name)
        elif name in exclude_names:
            names.remove(name)
    return names


def parse_types_in_frameworks(dir_path: str):
    types = []
    for root, dirs, files in os.walk(dir_path):
        # Check if any folder in the path is in FRAMEWORKS
        if 'Pods' not in root.replace('\\', '/').split('/') and 'Frameworks' not in root.replace('\\', '/').split('/'):
            continue
        for file in files:
            if file.endswith('.swift') or file.endswith('.h') or file.endswith('.hpp'):
                path = (os.path.join(root, file)).replace('\\', '/')
                with open(path, 'r', encoding='utf-8') as f:
                    try:
                        content = f.read().replace('\u2028', ' ')
                        types += parse_framework_types(content)
                    except UnicodeDecodeError:
                        pass
    return list(set(types))


def list_file_names(project: dict, exclude_names: tuple = ('TuneUpPopUp', 'TopUIButtonStyleKit')):
    """
    Lists file names of .swift files in the project.

    :param exclude_names:
    :param project: project to list files in
    :return: list of file names
    """
    names = []

    for file_path in project.keys():
        if file_path.endswith('.swift'):
            name = file_path.split('/')[-1][:-6]
        elif file_path.endswith('.xib'):
            name = file_path.split('/')[-1][:-4]
        else:
            continue
        if '+' in name or '-' in name or ' ' in name:
            continue
        if name not in exclude_names:
            names.append(name)
    return list(set(names))


def generate_rename_map(names: list):
    """
    Generates a renaming map (dictionary) for the given names.


    :param names: names to rename
    :return: dict, renaming map in the format {old_name: new_name}
    """
    return {name: new_type_name(name) for name in names}


def rename_type(project: dict, old_name: str, new_name: str):
    """
    Renames the type in the project. If rename_files is True, the files will be renamed as well.

    :param project: project to rename the type in
    :param old_name: old type name
    :param new_name: new type name
    :return: dict, renamed project
    """
    new_project = {}

    if project_contains_string(project, f'@{old_name}'):
        return project

    if project_contains_string(project, f'typealias {old_name}'):
        return project

    for file_path, file_content in project.items():
        if file_path.endswith('.swift'):
            # pattern if old name is not surrounded by alphanumeric characters
            old_pattern = r'(?<!\w)' + re.escape(old_name) + r'(?!\w)(?=(?:(?:[^"]*"){2})*[^"]*$)'
            new_content = re.sub(old_pattern, new_name, file_content, flags=re.MULTILINE)

            new_pattern = r'\\\([\S\s]*?\)'
            matches = re.finditer(new_pattern, new_content)

            for match in matches:
                pattern = r'(?<!\w)' + re.escape(old_name) + r'(?!\w)'
                new_match = re.sub(pattern, new_name, match.group(0))
                new_content = new_content.replace(match.group(0), new_match)

            in_string_pattern = r'\"' + re.escape(old_name) + r'\"'
            new_content = re.sub(in_string_pattern, f'"{new_name}"', new_content)

            new_project[file_path] = new_content
            continue
        elif file_path.endswith('.xib') or file_path.endswith('.storyboard'):
            pattern = r'customClass="' + re.escape(old_name) + r'"'
            new_content = re.sub(pattern, 'customClass="' + new_name + '"', file_content)
            new_project[file_path] = new_content
            continue
        else:
            new_project[file_path] = file_content
            continue

    return new_project


def rename_types(project: dict, rename_map: dict):
    """
    Renames types in the project according to the renaming map.

    :param project: project to rename types in
    :param rename_map: renaming map in the format {old_name: new_name}
    :return: dict, renamed project
    """
    for old_name, new_name in rename_map.items():
        project = rename_type(project, old_name, new_name)
    return project


def rename_files(project: dict, rename_map: dict) -> dict:
    """
    Renames files in the project according to the renaming map.

    :param project: project to rename files in
    :param rename_map: renaming map in the format {old_name: new_name}
    :return: dict, renamed project
    """

    new_project = {}

    for file_path, file_content in project.items():
        new_path = file_path
        new_content = file_content

        if '/Pods/' in file_path:
            new_project[new_path] = file_content
            continue

        if file_path.endswith('.pbxproj'):
            for old_name, new_name in rename_map.items():
                new_content = new_content.replace(f'/* {old_name}.swift ', f'/* {new_name}.swift ')
                new_content = new_content.replace(f'path = {old_name}.swift;', f'path = {new_name}.swift;')

                new_content = new_content.replace(f'/* {old_name}.xib ', f'/* {new_name}.xib ')
                new_content = new_content.replace(f'path = {old_name}.xib;', f'path = {new_name}.xib;')

            new_project[new_path] = new_content
            continue

        elif file_path.endswith('.storyboard'):
            for old_name, new_name in rename_map.items():
                new_content = new_content.replace(f'customClass="{old_name}"', f'customClass="{new_name}"')

            new_project[new_path] = new_content
            continue

        for old_name, new_name in rename_map.items():
            new_path = new_path.replace('/' + old_name + '.swift', '/' + new_name + '.swift')
            new_path = new_path.replace('/' + old_name + '.xib', '/' + new_name + '.xib')

            new_content = new_content.replace(f'loadNibNamed("{old_name}"', f'loadNibNamed("{new_name}"')
            new_content = new_content.replace(f'loadNibNamed:@"{old_name}"', f'loadNibNamed:@"{new_name}"')

        new_project[new_path] = new_content

    return new_project
