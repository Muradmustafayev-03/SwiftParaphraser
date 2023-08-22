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


def apply_to_project(project: dict, func: callable, *args, **kwargs):
    for file_path, file_content in project.items():
        if file_path.endswith('.swift'):
            project[file_path] = func(file_content, *args, **kwargs)
    return project


def parse_names(swift_code: str):
    names = []

    # parse class names
    pattern = r'class\s+([A-Z][a-zA-Z0-9_]+)\s*(:|\{)'
    matches = re.finditer(pattern, swift_code)
    for match in matches:
        names.append(match.group(1))

    # parse struct names
    pattern = r'struct\s+([A-Z][a-zA-Z0-9_]+)\s*(:|\{)'
    matches = re.finditer(pattern, swift_code)
    for match in matches:
        names.append(match.group(1))

    # parse enum names
    pattern = r'enum\s+([A-Z][a-zA-Z0-9_]+)\s*(:|\{)'
    matches = re.finditer(pattern, swift_code)
    for match in matches:
        names.append(match.group(1))

    # parse protocol names
    pattern = r'protocol\s+([A-Z][a-zA-Z0-9_]+)\s*(:|\{)'
    matches = re.finditer(pattern, swift_code)
    for match in matches:
        names.append(match.group(1))

    # parse extension names
    pattern = r'extension\s+([A-Z][a-zA-Z0-9_]+)\s*(:|\{)'
    matches = re.finditer(pattern, swift_code)
    for match in matches:
        names.append(match.group(1))

    # parse typealias names
    pattern = r'typealias\s+([A-Z][a-zA-Z0-9_]+)\s*(:|\{)'
    matches = re.finditer(pattern, swift_code)
    for match in matches:
        names.append(match.group(1))

    names = list(set(names))
    if 'SceneDelegate' in names:
        names.remove('SceneDelegate')
    if 'AppDelegate' in names:
        names.remove('AppDelegate')
    return names


def find_all_names(project: dict):
    names = []

    for file_path, file_content in project.items():
        if file_path.endswith('.swift'):
            file_names = parse_names(file_content)
            names += file_names
    return list(set(names))


def rename_item(project: dict, old_name: str, new_name: str):
    new_project = {}
    # rename .swift file named after class, rename class itself,
    # rename references to class in other files including .xib and .storyboard files
    for file_path, file_content in project.items():
        if file_path.endswith('.swift'):
            # old_name surrounded by non-alphanumeric characters
            pattern = rf'([^a-zA-Z0-9_]){old_name}([^a-zA-Z0-9_])'

            new_path = file_path
            if file_path.split('/')[-1] == old_name + '.swift':
                new_path = file_path.replace(old_name + '.swift', new_name + '.swift')

            new_project[new_path] = re.sub(pattern, rf'\1{new_name}\2', file_content)

        elif file_path.endswith('.xib') or file_path.endswith('.storyboard'):
            new_project[file_path] = file_content.replace(f'"{old_name}"', f'"{new_name}"')

    return new_project


def rename_items(project: dict, names: dict):
    for old_name, new_name in names.items():
        project = rename_item(project, old_name, new_name)

    return project
