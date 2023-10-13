import regex as re
from .rename_utils import generate_random_name


def remove_empty_lines(swift_code: str) -> str:
    """
    Removes all empty lines from a string.

    :param swift_code: input string
    :return: output string with no empty lines
    """
    return '\n'.join([line for line in swift_code.splitlines() if line.strip()])


def remove_comments(swift_code: str) -> str:
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


def transform_condition(statement: str, condition: str, else_body: str, comment_adding: bool = False) -> str:
    """
    Transforms a guard statement by converting it to an if statement.

    :param statement: input guard statement
    :param condition: input condition
    :param else_body: input else body
    :param comment_adding: bool, whether to add comments
    :return: output if statement
    """
    # skip guard let and guard var statements
    if re.search(r'\b' + 'let' + r'\b', condition):
        if comment_adding:
            return f"""
/* In order to proceed the following operations, the  condition {condition} must be satisfied: */
/* Conversion of the guard statement here is not supported because it is a guard let statement which is unsafe to transform. */
{statement}
/* Guarded that {condition} condition is true, the following will be proceeded: */
"""
        else:
            return statement
    if re.search(r'\b' + 'var' + r'\b', condition):
        if comment_adding:
            return f"""
/* In order to proceed the following operations, the  condition {condition} must be satisfied: */
/* Conversion of the guard statement here is not supported because it is a guard var statement which is unsafe to transform. */
{statement}
/* Guarded that {condition} condition is true, the following will be proceeded: */
"""
        return statement

    condition = " && ".join(split_conditions(condition))

    transformed_statement = f'\nif !({condition}) {{\n{else_body}\n}}\n'
    if comment_adding:
        transformed_statement = f"""

/* In order to proceed the following operations, the  condition {condition} must be satisfied: */
if !({condition}) {{ /* check the case when {condition} is false */

/* In this case, the following operations will be executed: */
{else_body} /* Exit statement so that the following operations will not be executed */

}}

/* Guarded that {condition} condition is true, the following will be proceeded: */

"""
    return transformed_statement


def transform_conditions(code: str, comment_adding: bool = False) -> str:
    """
    Transforms all guard statements in a string by converting them to if statements.

    :param code: input code string
    :param comment_adding: bool, whether to add comments
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
            transformed_statement = transform_condition(statement, condition, else_body, comment_adding=comment_adding)
            transformed_code = transformed_code.replace(statement, transformed_statement)

    return transformed_code


def generate_while_loop(val: str, sequence: str, body: str, n: int, comment_adding: bool = False) -> str:
    """
    Generates a while loop given a variable name, a sequence, and a body.

    :param val: Variable name
    :param sequence: Sequence to iterate over
    :param body: Loop body
    :param n: Unique identifier
    :param comment_adding: bool, whether to add comments
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

    if comment_adding:
        transformed_loop = f"""
    // we will iterate over the sequence {sequence} and check the condition {condition}
    let {sequence_name} = Array({sequence}) // declare a new array to store the sequence {sequence}
    var {index_name} = 0 // declare a new variable to store the index of the sequence {sequence}
    // while the index {index_name} is less than the length of the sequence {sequence_name}
    while {index_name} < {sequence_name}.count {{
        // the value of the sequence {sequence_name} at index {index_name} is {sequence_name}[{index_name}]
        let {val} = {sequence_name}[{index_name}]
        if {condition} {{ // check the condition {condition}
            // if the condition {condition} is true, the following operations will be executed:
            {body}
        }}
        // increment the index {index_name} by 1 to proceed to the next iteration
        {index_name} += 1
    }}
    """

    return transformed_loop


def transform_loops(code: str, comment_adding: bool = False) -> str:
    """
    Transforms all for loops in a string by converting them to while loops.

    :param code: input code string
    :param comment_adding: bool, whether to add comments
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
            transformed_loop = generate_while_loop(val, sequence, body, n, comment_adding)
            transformed_code = transformed_code.replace(loop, transformed_loop)
            n += 1

    return transformed_code


def parse_functions(code: str):
    functions = []

    # parsing functions
    pattern = re.compile(
        r'(?:(?<!class)(\s*?)(mutating|public|private|protected|internal|fileprivate|open|override|@objc)\s+)?(static\s+)?func\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\s*(.*?)\s*\)\s*(?:\s*->\s*(?:.*?)?)?\s*{')
    declarations = [match.group(0) for match in pattern.finditer(code)]

    def parse_params(unparsed: str):
        parsed = []

        for param in unparsed.split(','):
            param = param.split(':')[0].strip()
            if not param:
                continue
            split_params = param.split(' ')
            left = split_params[0]
            right = split_params[-1]
            parsed.append((left, right))

        return parsed

    for declaration in declarations:
        # check if @available is one line above declaration
        line_id = 0
        for line in code.split('\n'):
            if declaration in line:
                break
            line_id += 1
        if '@available' in code.split('\n')[line_id - 1]:
            continue

        if declaration.count('(') > declaration.count(')'):
            declaration_start_index = code.find(declaration)
            declaration_end_index = declaration_start_index + len(declaration)

            while not (code[declaration_end_index] == '{' and declaration.count('(') == declaration.count(')')):
                declaration_end_index += 1
                declaration = code[declaration_start_index:declaration_end_index]

        if '<' in declaration:
            continue  # skip generic functions

        open_brackets = 1
        func_start_index = code.find(declaration)
        body_start_index = func_start_index + len(declaration)
        body_end_index = body_start_index

        while open_brackets > 0 and body_end_index < len(code):
            if code[body_end_index] == '{':
                open_brackets += 1
            elif code[body_end_index] == '}':
                open_brackets -= 1
            body_end_index += 1

        if open_brackets != 0:
            continue

        function = code[func_start_index:body_end_index]
        name = declaration.split('func')[1].split('(')[0].strip()
        unparsed_params = declaration.split('(')[1].split(')')[0].strip()
        params = parse_params(unparsed_params)
        body = code[body_start_index:body_end_index - 1]
        returns_value = '->' in declaration or r'\breturn\b' in body

        functions.append([function, name, params, declaration, body, returns_value])

    return functions


def compose_call(name: str, params: list, return_value: bool = False):
    if return_value:
        return f'return {name}({", ".join([f"{param[0]}: {param[1]}" for param in params])})'
    return f'{name}({", ".join([f"{param[0]}: {param[1]}" for param in params])})'


def compose_wrapper_function(declaration, new_name, params, return_value):
    return f'{declaration}\n{compose_call(new_name, params, return_value)}\n}}'


def rename_function(function: str, old_name: str, new_name: str):
    pattern = rf'func\s+{old_name}'
    return re.sub(pattern, f'func {new_name}', function).replace('override ', '', 1).replace('override ', '')


def restructure_functions(code: str):
    new_code = code
    functions = parse_functions(code)
    for function, name, params, declaration, body, returns_value in functions:
        new_name = generate_random_name('func')
        wrapper_function = compose_wrapper_function(declaration, new_name, params, returns_value)
        performing_function = rename_function(function, name, new_name)
        new_code = new_code.replace(function, performing_function + '\n\n\t' + wrapper_function)

    return new_code
