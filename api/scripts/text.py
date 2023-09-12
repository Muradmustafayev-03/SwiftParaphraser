import regex as re
from .rename_utils import generate_random_name


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


def split_conditions(condition: str) -> list:
    # split the condition by "," but ignore "," inside brackets and strings
    # Regular expression to match commas outside of parentheses and quotes
    pattern = r',(?=(?:[^\(\)]*\([^()]*\))*[^\(\)]*$)(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)'

    # Use re.split to split the string based on the pattern
    split_result = re.split(pattern, condition)

    # Remove any leading or trailing whitespace from each element in the result
    split_result = [s.strip() for s in split_result]

    return split_result


def transform_condition(statement: str, condition: str, else_body: str) -> str:
    """
    Transforms a guard statement by converting it to an if statement.

    :param statement: input guard statement
    :param condition: input condition
    :param else_body: input else body
    :return: output if statement
    """
    # skip guard let and guard var statements
    if re.search(r'\b' + 'let' + r'\b', condition):
        return statement
    if re.search(r'\b' + 'var' + r'\b', condition):
        return statement

    condition = " && ".join(split_conditions(condition))

    transformed_statement = f'\nif !({condition}) {{\n{else_body}\n}}\n'
    return transformed_statement


async def transform_conditions(code: str) -> str:
    """
    Transforms all guard statements in a string by converting them to if statements.

    :param code: input code string
    :return: output code string
    """
    guard_pattern = r'[\s*?]guard\s+([\S\s]*?)\s+else\s+{'
    statements = re.finditer(guard_pattern, code)

    transformed_code = code  # Create a new string to store the transformed code

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
            transformed_statement = transform_condition(statement, condition, else_body)
            transformed_code = transformed_code.replace(statement, transformed_statement)

    return transformed_code


def generate_while_loop(val: str, sequence: str, body: str, n: int) -> str:
    """
    Generates a while loop given a variable name, a sequence, and a body.

    :param val: Variable name
    :param sequence: Sequence to iterate over
    :param body: Loop body
    :param n: Unique identifier
    :return: Generated while loop
    """
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
    return transformed_loop


async def transform_loops(code: str) -> str:
    """
    Transforms all for loops in a string by converting them to while loops.

    :param code: input code string
    :return: output code string
    """
    for_pattern = r'(\s*?)for\s+([a-zA-Z0-9_]+?)\s+in\s+([\S\s]+?){'
    matches = re.finditer(for_pattern, code)

    transformed_code = code  # Create a new string to store the transformed code
    n = 0

    for match in matches:
        val = match.group(2)
        sequence = match.group(3)
        loop_start = match.group(0)
        open_brackets = 1
        idx = code.find(loop_start) + len(loop_start)

        if loop_start.count('(') > loop_start.count(')'):
            continue
        if loop_start.count('[') > loop_start.count(']'):
            continue
        if loop_start.count('{') - 1 > loop_start.count('}'):
            continue

        while open_brackets > 0 and idx < len(code):
            if code[idx] == '{':
                open_brackets += 1
            elif code[idx] == '}':
                open_brackets -= 1
            idx += 1

        if open_brackets == 0:
            loop = code[code.find(loop_start):idx]
            body = loop[loop.find('{') + 1: -1]
            transformed_loop = generate_while_loop(val, sequence, body, n)
            transformed_code = transformed_code.replace(loop, transformed_loop)
            n += 1

    return transformed_code


def find_all_imports(code: str) -> list:
    """
    Finds all imports in a string.

    :param code: input code string
    :return: list of import names
    """
    pattern = r'^import\s+([a-zA-Z0-9_]+)'
    matches = re.findall(pattern, code, flags=re.MULTILINE)
    return matches
