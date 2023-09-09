import regex as re
from .rename_utils import rename_local_variables, generate_random_name


def remove_whitespace(input_string: str) -> str:
    """
    Removes all whitespace characters from a string.

    :param input_string: input string
    :return: output string with no whitespace characters
    """
    # Use regular expression to match whitespace characters and replace them with an empty string
    return re.sub(r'\s+', '', input_string)


async def remove_empty_lines(swift_code: str) -> str:
    """
    Removes all empty lines from a string.

    :param swift_code: input string
    :return: output string with no empty lines
    """
    return '\n'.join([line for line in swift_code.splitlines() if line.strip()])


async def remove_comments(swift_code: str) -> str:
    """
    Removes all comments from a string. Preserves strings like "...//...".

    :param swift_code: input code string
    :return: output code string with no comments
    """
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


def parse_functions(code: str) -> list:
    """
    Parses all functions from a string. Returns a list of tuples (name, parameters, body, entire_function, declaration).

    :param code: input code string
    :return: list of tuples (name, parameters, body, entire_function, declaration)
    """
    pattern = r'(?:(?<!class)(\s*?)(public|private|protected|internal|fileprivate|open|override|@objc)\s+)?(static\s+)?func\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\s*(.*?)\s*\)\s*(?:\s*->\s*(?:.*?)?)?\s*{'
    functions = re.finditer(pattern, code)

    parsed_functions = []
    for match in functions:
        declaration = match.group(0)
        name = match.group(4)
        parameters = match.group(5)
        open_brackets = 1
        idx = code.find(declaration) + len(declaration)

        while open_brackets > 0 and idx < len(code):
            if code[idx] == '{':
                open_brackets += 1
            elif code[idx] == '}':
                open_brackets -= 1
            idx += 1

        if open_brackets == 0:
            body = code[len(declaration):idx - 1]
            entire_function = code[code.find(declaration):idx]
            parsed_functions.append((name, parameters, body, entire_function, declaration))
    return parsed_functions


def parse_parameters(parameters: str) -> list:
    """
    Parses all parameters from a string (pre-parsed from a function). Returns a list of tuples (type, name).

    :param parameters: input parameters string
    :return: list of tuples (name, type)
    """
    parameters = parameters.split(',')
    parameters = [parameter.strip() for parameter in parameters]
    parameters = [parameter.split(':')[0] for parameter in parameters]
    parameters = [(parameter.split()[0], parameter.split()[1]) if len(parameter.split()) > 1 else
                  (parameter, parameter) for parameter in parameters]
    return parameters


def parse_guard_statements(code: str) -> list:
    """
    Parses all guard statements from a string. Returns a list of tuples (statement, condition, else_body).

    :param code: input code string
    :return: list of tuples (statement, condition, else_body)
    """
    guard_pattern = r'[\s*?]guard\s+([\S\s]*?)\s+else\s+{'
    statements = re.finditer(guard_pattern, code)

    parsed_statements = []
    for match in statements:
        condition = match.group(1)
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


def parse_loops(code: str) -> list:
    """
    Parses all loops from a string. Returns a list of tuples (statement, variable_name, sequence_name, loop_body).

    :param code: input code string
    :return: list of tuples (statement, variable_name, sequence_name, loop_body)
    """
    for_pattern = r'(\s*?)for\s+([a-zA-Z0-9_]+?)\s+in\s+([\S\s]+?){'
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


async def rename_variables(code: str) -> str:
    """
    Renames all variables in a string to random names.

    :param code: input code string
    :return: output code string
    """
    functions = parse_functions(code)
    functions = [function[3] for function in functions]
    return rename_local_variables(code, functions)


async def transform_conditions(code: str) -> str:
    """
    Transforms all guard statements in a string by converting them to if statements.

    :param code: input code string
    :return: output code string
    """
    guard_statements = parse_guard_statements(code)
    for statement, conditions, else_body in guard_statements:

        # # skip guard let statements
        # pattern = r'\b' + 'let' + r'\b'
        # if re.search(pattern, condition):
        #     continue

        transformed_statement = ''

        names = []
        for condition in conditions.split(','):
            name = generate_random_name(prefix='condition', suffix=str(len(names)))
            names.append(name)
            transformed_statement += f'''
var {name} = false
if {condition.strip()} {{
    {name} = true
}}
'''

        summary_condition = ' && '.join(names)

        transformed_statement += f'\nif !({summary_condition}) {{\n{else_body}\n}}\n'
        print(transformed_statement)
        code = code.replace(statement, transformed_statement)
    return code


async def transform_loops(code: str) -> str:
    """
    Transforms all loops in a string by converting them to while loops.

    :param code: input code string
    :return: output code string
    """
    for_loops = parse_loops(code)
    n = 0
    for loop, val, sequence, body in for_loops:
        condition = 'true'
        if 'where' in sequence:
            sequence, condition = sequence.split('where')

        sequence_name = generate_random_name(prefix='sequence', suffix=str(n))
        index_name = generate_random_name(prefix='index', suffix=str(n))

        transformed_loop = f"""
let {sequence_name} = Array({sequence})
var {index_name} = 0
while {index_name} < {sequence_name}.count {{
    let {val} = {sequence_name}[{index_name}]
    if {condition} {{
        {body}
    }}
    {index_name} += 1
}}
"""
        code = code.replace(loop, transformed_loop)
    return code


def find_all_imports(code: str) -> list:
    """
    Finds all imports in a string.

    :param code: input code string
    :return: list of import names
    """
    pattern = r'^import\s+([a-zA-Z0-9_]+)'
    matches = re.findall(pattern, code, flags=re.MULTILINE)
    return matches


def add_missing_imports(source: str, result: str) -> str:
    """
    Adds missing imports from source to result.

    :param source: code before transformation
    :param result: code after transformation
    :return: result with missing imports added
    """
    source_imports = find_all_imports(source)
    result_imports = find_all_imports(result)

    for import_name in source_imports:
        if import_name not in result_imports:
            result = f'import {import_name}\n' + result

    return result
