import json
import re


def project_dict_to_str(project: dict):
    return '\n'.join([f"{file}:\n```\n{content}\n```" for file, content in project.items()])


def project_str_to_dict(project: str):
    file_data = {}
    pattern = r'([^:^\n]+):\s*```\s*([\s\S]+?)```'
    matches = re.finditer(pattern, project, re.DOTALL)

    for match in matches:
        file_path = match.group(1).strip()
        file_content = match.group(2).strip()
        file_data[file_path] = file_content

    return file_data


def remove_empty_lines(swift_code: str):
    return '\n'.join([line for line in swift_code.splitlines() if line.strip()])


def remove_comments(swift_code: str):
    # Find all strings like "...//..." and replace them with placeholders
    pattern = r'"(.*?//.*?)"'
    preserved_strings = re.findall(pattern, swift_code)
    for i, string in enumerate(preserved_strings):
        placeholder = f'[000__PRESERVED_STRING_{i}__000]'
        swift_code = swift_code.replace(string, placeholder)

    # Remove single-line comments
    swift_code = re.sub(r'//[^\n]*', '', swift_code)

    # Remove multi-line comments
    swift_code = re.sub(r'/\*(.*?)\*/', '', swift_code, flags=re.DOTALL)

    # Restore preserved strings
    for i, string in enumerate(preserved_strings):
        placeholder = f'[000__PRESERVED_STRING_{i}__000]'
        swift_code = swift_code.replace(placeholder, string)

    return swift_code


def parse_names(project: str):
    names = {
        'class': set(),
        'struct': set(),
        'func': set(),
        'var': set(),
    }

    # parse class names
    pattern = r'class\s+([A-Z][a-zA-Z0-9_]+)\s*(:|\{)'
    matches = re.finditer(pattern, project)
    for match in matches:
        names['class'].add(match.group(1))

    # parse struct names
    pattern = r'struct\s+([A-Z][a-zA-Z0-9_]+)\s*(:|\{)'
    matches = re.finditer(pattern, project)
    for match in matches:
        names['struct'].add(match.group(1))

    # parse func names
    pattern = r'func\s+([a-z][a-zA-Z0-9_]+)\s*\('
    matches = re.finditer(pattern, project)
    for match in matches:
        names['func'].add(match.group(1))

    # parse var names
    pattern = r'var\s+([a-z][a-zA-Z0-9_]+)\s*(:|=)'
    matches = re.finditer(pattern, project)
    for match in matches:
        names['var'].add(match.group(1))

    # parse let names
    pattern = r'let\s+([a-z][a-zA-Z0-9_]+)\s*(:|=)'
    matches = re.finditer(pattern, project)
    for match in matches:
        names['var'].add(match.group(1))

    # sets to tuple and return json
    for key in names.keys():
        names[key] = tuple(names[key])

    return json.dumps(names)
