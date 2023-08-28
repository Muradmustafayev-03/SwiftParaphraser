import regex as re

FUNC_PREFIXES_RESTRICTED_TO_RENAME = [
    'get', 'set', 'willSet', 'didSet', 'AF', 'UI', 'NS', 'CG', 'MK', 'WK', 'SCN', 'SK', 'AV', 'CA', 'CI', 'CL', 'CN',
    'KF', 'URL', 'JSON', 'Firestore', 'FIR', 'URLSession', 'URLSessionDataTask', 'URLSessionDownloadTask', 'Observ',
    'with', 'Unsafe', '@', 'mutable'
]

FUNC_RESTRICTED_TO_RENAME = [
    'String', 'Int', 'Double', 'Float', 'Bool', 'Array', 'Dictionary', 'Set', 'Optional', 'Any', 'AnyObject', 'AnyClass',
    'Character', 'Error', 'ErrorType', 'NSRange', 'Selector', 'isEmpty', 'count', 'first', 'last', 'lowercased',
    'uppercased', 'trimmingCharacters', 'removeAll', 'remove', 'append', 'insert', 'removeFirst', 'removeLast',
    'removeSubrange', 'removeAll', 'removeValue', 'removeAll', 'removeAll', 'removeAll', 'removeAll', 'removeAll',
    'hasPrefix', 'hasSuffix', 'contains', 'split', 'joined', 'replacingOccurrences', 'replacingCharacters',
    'insert', 'remove', 'append', 'first', 'last', 'popLast', 'popFirst', 'removeAll', 'remove', 'removeAll',
    'filter', 'map', 'flatMap', 'reduce', 'sorted', 'sortedBy', 'sortedByDescending', 'sortedDescending',
    'updateValue', 'update', 'removeValue', 'remove', 'removeAll', 'remove', 'removeAll', 'removeAll', 'remove',
    'map', 'insert', 'init', 'deinit', 'subscript', 'description', 'hash', 'copy', 'alloc', 'dealloc', 'application',
    'subscript'
]


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


def transform_conditions(code):
    # Define the regular expression pattern for guard statements
    guard_pattern = r'(\s*?)guard\s+([\S\s]*?)\s+else\s+{([\S\s]*?)}'

    # Find all matches of the pattern in the input string
    matches = re.findall(guard_pattern, code)

    # Process each match and perform the transformation
    for match in matches:
        indent, condition, else_body = match

        if 'let ' in condition:
            continue

        transformed_string = \
            f"{indent}if !({condition}) {{\n{indent}\t{else_body}\n}}"

        # Replace the matched patterns with the transformed strings
        code = re.sub(guard_pattern, transformed_string, code, 1)

    return remove_empty_lines(code)


def transform_loops(code, index='index'):
    # Define the regular expression pattern
    for_pattern = r'(\s*?)for\s+([\S\s]*?)\s+in\s+([\S\s]*?){([\S\s]*?)}'

    # Find all matches of the pattern in the input string
    matches = re.findall(for_pattern, code)

    # Process each match and perform the transformation
    for match in matches:
        indent, val, sequence, body = match
        body = body.replace('\n', f'\n\t')

        condition = 'true'

        # check if there is a where clause
        if 'where' in sequence:
            sequence, condition = sequence.split('where')

        transformed_string = \
            f"{indent}let sequence = {sequence}\n{indent}var {index} = 0\n{indent}while {index} < sequence.count " \
            f"{{\n{indent}\tlet {val} = sequence[sequence.index(sequence.startIndex, offsetBy:{index})]\n{indent}\tif " \
            f"({condition}) {{\n{indent}\t\t{body}}}\n{indent}\t{index} += 1\n{indent}\t}}"

        # Replace the matched patterns with the transformed strings
        code = re.sub(for_pattern, transformed_string, code, 1)

    return remove_empty_lines(code)


def parse_struct_names(swift_code: str):
    names = []

    for struct_type in ['class', 'struct', 'enum']:
        pattern = rf'{struct_type}\s+([A-Z][a-zA-Z0-9_]+)\s*(:|\{{)'
        matches = re.finditer(pattern, swift_code)
        for match in matches:
            names.append(match.group(1))

    # functions that are not overridden
    pattern = r'(?<!override\s+)func\s+([a-zA-Z0-9_]+)\s*\('
    matches = re.finditer(pattern, swift_code)
    for match in matches:
        name = match.group(1)
        for prefix in FUNC_PREFIXES_RESTRICTED_TO_RENAME:
            if name.startswith(prefix):
                continue
            if name in FUNC_RESTRICTED_TO_RENAME:
                continue
            names.append(name)

    # # variables
    # pattern = r'var\s+([a-zA-Z0-9_]+)\s*(:|=)'
    # matches = re.finditer(pattern, swift_code)
    # for match in matches:
    #     name = match.group(1)
    #     names.append(name)
    #
    # # constants
    # pattern = r'let\s+([a-zA-Z0-9_]+)\s*(:|=)'
    # matches = re.finditer(pattern, swift_code)
    # for match in matches:
    #     name = match.group(1)
    #     names.append(name)

    names = list(set(names))
    if 'SceneDelegate' in names:
        names.remove('SceneDelegate')
    if 'AppDelegate' in names:
        names.remove('AppDelegate')
    return names


def find_all_names(project: dict):
    names = []

    for file_path, file_content in project.items():
        if 'AppDelegate' in file_path or 'SceneDelegate' in file_path:
            continue
        if file_path.endswith('.swift'):
            file_names = parse_struct_names(file_content)
            names += file_names
    return list(set(names))


def rename_item(project: dict, old_name: str, new_name: str):
    new_project = {}
    # rename .swift file named after class, rename class itself,
    # rename references to class in other files including .xib and .storyboard files
    for file_path, file_content in project.items():
        word_regex = r'\b' + re.escape(old_name) + r'\b'
        new_path = file_path
        new_content = re.sub(word_regex, new_name, file_content)

        if file_path.endswith('.swift'):
            if file_path.split('/')[-1] == old_name + '.swift':
                new_path = file_path.replace(old_name + '.swift', new_name + '.swift')

        new_project[file_path] = new_content

    return new_project


def rename_items(project: dict, names: dict):
    for old_name, new_name in names.items():
        project = rename_item(project, old_name, new_name)

    return project


def find_all_imports(code: str):
    pattern = r'^import\s+([a-zA-Z0-9_]+)'
    matches = re.findall(pattern, code, flags=re.MULTILINE)
    return matches


def add_missing_imports(source, result):
    source_imports = find_all_imports(source)
    result_imports = find_all_imports(result)

    for import_name in source_imports:
        if import_name not in result_imports:
            result = f'import {import_name}\n' + result

    return result
