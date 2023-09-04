import random
import regex as re
from .constants import *


def open_abbreviation(name: str):
    abbreviations = list(ABBREVIATIONS.items())
    random.shuffle(abbreviations)
    for abbr, opening in abbreviations:
        if opening in name:
            name = name.replace(opening, abbr)
        elif abbr in name:
            name = name.replace(abbr, opening)
    return name


def first_letter_upper(name: str):
    return name[0].upper() + name[1:] if len(name) > 0 else name


def first_letter_lower(name: str):
    return name[0].lower() + name[1:] if len(name) > 0 else name


def generate_random_name(prefix='', suffix=''):
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
    name = open_abbreviation(name)
    name = first_letter_upper(name)

    prefix = random.choice(['var', 'variable', 'value'])

    if random.choice([True, False]):
        return prefix + random.choice(ADJECTIVES) + name
    else:
        return generate_random_name(prefix)


def new_func_name(name: str):
    name = open_abbreviation(name)
    name = first_letter_lower(name)

    prefix = random.choice(['func', 'function'])
    return prefix + random.choice(ADJECTIVES) + name


def new_type_name(name: str):
    name = open_abbreviation(name)
    name = first_letter_upper(name)

    if random.choice([True, False]):
        return 'Type' + random.choice(ADJECTIVES) + name
    else:
        return generate_random_name('Type')


def rename_local_variables(code, functions: list[str]):
    for function in functions:
        var_pattern = r'(?<!override)\s*var\s+([a-zA-Z_]+)'
        variables = re.finditer(var_pattern, function)

        for var_match in variables:
            var_name = var_match.group(1)
            new_name = new_var_name(var_name)

            old_pattern = rf'(?<![a-zA-Z_.]){var_name}(?![a-zA-Z_])'

            # exclude declaration and assignment to itself at the same time
            if re.search(rf'var\s+{old_pattern}\s*=\s*{old_pattern}', function):
                continue
            if re.search(rf'var\s+{old_pattern}\s*:\s*{old_pattern}', function):
                continue

            new_function = re.sub(old_pattern, new_name, function)
            code = code.replace(function, new_function)

    return code


def parse_type_names(swift_code: str, include_types: tuple = ('class', 'struct', 'enum')):
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
    names = []

    for file_path, file_content in project.items():
        if 'AppDelegate.swift' in file_path or 'SceneDelegate.swift' in file_path:
            continue
        if file_path.endswith('.swift'):
            file_names = parse_type_names(file_content, include_types)
            names += file_names
    return list(set(names))


def generate_rename_map(names: list[str]):
    return {name: new_type_name(name) for name in names}


def rename_type(project: dict, old_name: str, new_name: str, rename_files: bool = False):
    new_project = {}
    renamed_files = []

    for file_path, file_content in project.items():
        if file_path.endswith('.swift'):
            new_path = file_path

            if file_path.split('/')[-1] == old_name + '.swift' and rename_files:
                new_path = file_path.replace(old_name + '.swift', new_name + '.swift')
                renamed_files.append((old_name, new_name))

            # pattern if not declaration variable or function name
            pattern = r'(?<!let)(?<!var)(?<!func)(?<!\.)\b' + re.escape(old_name) + r'\b'
            new_content = re.sub(pattern, new_name, file_content)
            new_project[new_path] = new_content
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
            new_content = re.sub(pattern, r'>' + new_name + r'<', file_content)
            new_project[file_path] = new_content
            continue

        else:
            new_project[file_path] = file_content
            continue

    return new_project


def rename_types(project, rename_map, rename_files=False):
    for old_name, new_name in rename_map.items():
        project = rename_type(project, old_name, new_name, rename_files)
    return project
