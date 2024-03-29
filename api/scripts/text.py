import random

import regex as re
from .rename_utils import generate_random_name
from .dummy_files import generate_dummy_function


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
    version_comment = re.search(r'\/\/ swift-tools-version:.*', swift_code)

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

    # Restore swift-tools-version comment
    if version_comment:
        swift_code = version_comment.group() + '\n' + swift_code

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
            else_body = statement[len(statement_start): -1]
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
    # parsing functions
    pattern = re.compile(
        r'(?:\b(?:open|public|internal|fileprivate|private|final|class|static|dynamic|convenience|required|mutating|override|@objc)\s+)*func\s+([a-zA-Z_][a-zA-Z0-9_]*)'
    )
    declarations = [match.group(0) for match in pattern.finditer(code)]

    def parse_params(unparsed: str):
        parsed = []

        # replace patterns in [], (), and {}
        inner_pattern = re.compile(r'\[[\S\s]*?\]')
        unparsed = re.sub(inner_pattern, '', unparsed)
        inner_pattern = re.compile(r'\([\S\s]*?\)')
        unparsed = re.sub(inner_pattern, '', unparsed)
        inner_pattern = re.compile(r'\{[\S\s]*?\}')
        unparsed = re.sub(inner_pattern, '', unparsed)

        for param in unparsed.split(','):
            type_ = None

            if ':' in param:
                type_ = param.split(':')[1]
                param = param.split(':')[0]
            param = param.strip()

            if not param:
                continue
            split_params = param.split(' ')
            left = split_params[0]
            right = split_params[-1]
            if 'inout' in type_:
                right = '&' + right
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
        if '@MainActor' in code.split('\n')[line_id - 1]:
            continue

        try:
            declaration_start_index = declaration_end_index = code.find(declaration)

            while not (code[declaration_end_index] == '{' and
                       declaration.count('(') == declaration.count(')') and
                       declaration.count('{') == declaration.count('}')):
                declaration_end_index += 1
                declaration = code[declaration_start_index:declaration_end_index]
        except IndexError:
            continue

        if declaration.find('}') < declaration.find('{'):
            continue  # skip functions without body

        if declaration.count('{') > 1 or declaration.count('}') > 0:
            continue  # skip functions with multiple bodies

        if declaration.count('func') > 1:
            continue  # skip functions with multiple func keywords

        if '<' in declaration:
            continue  # skip generic functions

        if code.split('\n')[line_id - 1].strip() == '@objc' and '@objc' not in declaration:
            declaration = code.split('\n')[line_id - 1] + '\n' + declaration
        if '@objc' in code.split('\n')[line_id] and '@objc' not in declaration:
            declaration = '@objc ' + declaration

        open_brackets = 1
        func_start_index = code.find(declaration)
        body_start_index = func_start_index + len(declaration) + 2
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
        if function.count('{') != function.count('}'):
            continue
        if not function.replace(declaration, '').strip():
            continue
        name = declaration.split('func')[1].split('(')[0].strip()

        if not name.isalnum():
            continue

        param_start = declaration.find('(') + 1  # first occurrence of '('
        open_brackets = 1
        param_end = param_start
        while open_brackets > 0 and param_end < len(declaration):
            if declaration[param_end] == '(':
                open_brackets += 1
            elif declaration[param_end] == ')':
                open_brackets -= 1
            param_end += 1
        if open_brackets != 0:
            continue
        unparsed_params = declaration[param_start:param_end - 1].strip()
        params = parse_params(unparsed_params)

        body = code[body_start_index:body_end_index - 1]
        returns_value = ('->' in declaration and 'Void' not in declaration) or 'return ' in body

        # skip if there are nested functions
        if 'func ' in body:
            continue

        declaration = declaration.strip()

        # skip if there are new lines in declaration
        if '\n' in declaration and declaration.index('\n') > declaration.index(')'):
            continue

        yield [function, name, params, declaration, body, returns_value]


def compose_call(name: str, params: list, return_value: bool = False, is_async: bool = False):
    for i in range(len(params)):
        if params[i][0] == 'inout':
            params[i] = (params[i][0], '&' + params[i][1])
    call = f'{name}({", ".join([f"{param[0]}: {param[1]}" for param in params])})'
    if is_async:
        call = f'await {call}'
    if return_value:
        return f'return {call}'
    return call


def compose_wrapper_function(declaration, new_name, params, return_value):
    pattern = re.compile(r'\basync\b')
    is_async = pattern.search(declaration) is not None
    return f'{declaration}{{\n{compose_call(new_name, params, return_value, is_async)}\n}}'


def compose_performing_function(old_name: str, new_name: str, declaration: str, body: str, returns_value: bool):
    declaration = declaration.replace(old_name, new_name, 1)
    declaration = declaration.replace('override', '').strip()
    declaration = declaration.strip()
    if returns_value and 'return' not in body and 'Group' not in body and 'if' in body and 'else' in body and 'some' in declaration:
        body = f'Group {{\n\t\t{body}\n\t}}'
    return f'{declaration}{{\n{body}\n}}'


def restructure_function(code, function_data):
    function, name, params, declaration, body, returns_value = function_data

    if not name.strip():
        return code
    if 'throws' in declaration:
        return code

    new_name = generate_random_name('func', old_name=name)
    wrapper_function = compose_wrapper_function(declaration, new_name, params, returns_value)
    performing_function = compose_performing_function(name, new_name, declaration, body, returns_value)

    if not performing_function.strip():
        return code
    if not wrapper_function.strip():
        return code

    dummy_function = generate_dummy_function()

    return code.replace(function, '\n\n\t'.join([performing_function, wrapper_function, dummy_function]))


def restructure_functions(code: str):
    new_code = code
    for function_data in parse_functions(code):
        new_code = restructure_function(new_code, function_data)
    return new_code
