import regex as re


def remove_whitespace(input_string):
    # Use regular expression to match whitespace characters and replace them with an empty string
    return re.sub(r'\s+', '', input_string)


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


def parse_functions(code: str):
    pattern = r'(\s*?)func[\S\s]*?{'
    functions = re.finditer(pattern, code)

    parsed_functions = []
    for match in functions:
        func_start = match.group(0)
        open_brackets = 1
        idx = code.find(func_start) + len(func_start)

        while open_brackets > 0 and idx < len(code):
            if code[idx] == '{':
                open_brackets += 1
            elif code[idx] == '}':
                open_brackets -= 1
            idx += 1

        if open_brackets == 0:
            parsed_functions.append(code[code.find(func_start):idx])
    return parsed_functions


def parse_guard_statements(code: str):
    guard_pattern = r'(\s*?)guard\s+(?!let\s+)([\S\s]*?)\s+else\s+{'
    statements = re.finditer(guard_pattern, code)

    parsed_statements = []
    for match in statements:
        condition = match.group(2)
        statement_start = match.group(0)
        open_brackets = 1
        idx = code.find(statement_start) + len(statement_start)

        while open_brackets > 0 and idx < len(code):
            if code[idx] == '{':
                open_brackets += 1
            elif code[idx] == '}':
                open_brackets -= 1
            idx += 1

        if open_brackets == 0:
            statement = code[code.find(statement_start):idx]
            else_body = statement[statement.find('{') + 1: -1]
            parsed_statements.append((statement, condition, else_body))

    return parsed_statements


def parse_loops(code: str):
    for_pattern = r'(\s*?)for\s+([\S\s]*?)\s+in\s+([\S\s]*?){'
    matches = re.finditer(for_pattern, code)

    parsed_loops = []
    for match in matches:
        val = match.group(2)
        sequence = match.group(3)
        loop_start = match.group(0)
        open_brackets = 1
        idx = code.find(loop_start) + len(loop_start)

        while open_brackets > 0 and idx < len(code):
            if code[idx] == '{':
                open_brackets += 1
            elif code[idx] == '}':
                open_brackets -= 1
            idx += 1

        if open_brackets == 0:
            loop = code[code.find(loop_start):idx]
            body = loop[loop.find('{') + 1: -1]
            parsed_loops.append((loop, val, sequence, body))

    return parsed_loops


def transform_conditions(code):
    guard_statements = parse_guard_statements(code)
    for statement, condition, else_body in guard_statements:
        transformed_statement = f'\nif !({condition}) {{\n{else_body}\n}}\n'
        code = code.replace(statement, transformed_statement)
    return code


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
