import regex as re
from .text import remove_comments


def find_all_imports(code: str) -> list:
    """
    Finds all imports in a string.

    :param code: input code string
    :return: list of import names
    """
    pattern = r'^import\s+([a-zA-Z0-9_]+)'
    matches = re.findall(pattern, code, flags=re.MULTILINE)
    return matches


def add_comments_to_imports(code: str) -> str:
    """
    Adds comments to all imports in a string.

    :param code: input code string
    :return: output code string
    """

    imports = find_all_imports(code)
    for imp in imports:
        comment = f'// importing {imp}'
        code = code.replace(f'import {imp}', f'import {imp}  {comment}\n')
    return code


def add_comments_to_declarations(code: str) -> str:
    """
    Adds comments to all declarations in a string.

    :param code: input code string
    :return: output code string
    """

    no_comments_code = remove_comments(code)

    # Add comments to variable declarations
    pattern = r'/var\s+([a-zA-Z0-9_]+)(?:\s*:\s*([a-zA-Z0-9_]+))?(?:\s*=\s*([\S\s]+?))?'
    matches = re.finditer(pattern, no_comments_code)
    for match in matches:
        name = match.group(1)
        try:
            type_name = match.group(2)
        except IndexError:
            type_name = 'Any'
        try:
            value = match.group(3)
        except IndexError:
            value = None

        comment = f'// declare a new variable {name} of type {type_name} and assign it the value {value}'
        code = code.replace(match.group(0), comment + '\n' + match.group(0))

    # Add comments to constant declarations
    pattern = r'/let\s+([a-zA-Z0-9_]+)(?:\s*:\s*([a-zA-Z0-9_]+))?(?:\s*=\s*([\S\s]+?))?'
    matches = re.finditer(pattern, no_comments_code)
    for match in matches:
        name = match.group(1)
        try:
            type_name = match.group(2)
        except IndexError:
            type_name = 'Any'
        try:
            value = match.group(3)
        except IndexError:
            value = None

        comment = f'// declare a new constant {name} of type {type_name} and assign it the value {value}'
        code = code.replace(match.group(0), comment + '\n' + match.group(0))

    # Add comments to function declarations
    pattern = r'/func\s+([a-zA-Z0-9_]+)\s*\(([\S\s]*?)\)\s*(?:->\s*([a-zA-Z0-9_]+))?\s*{'
    matches = re.finditer(pattern, no_comments_code)
    for match in matches:
        name = match.group(1)
        try:
            parameters = match.group(2)
        except IndexError:
            parameters = ''
        try:
            return_type = match.group(3)
        except IndexError:
            return_type = 'Void'

        comment = f'// declare a new function {name} with parameters {parameters} and return type {return_type}'
        code = code.replace(match.group(0), comment + '\n' + match.group(0))

    # Add comments to class declarations
    pattern = r'/class\s+([a-zA-Z0-9_]+)\s*:\s*([a-zA-Z0-9_]+)\s*{'
    matches = re.finditer(pattern, no_comments_code)
    for match in matches:
        name = match.group(1)
        try:
            superclass_name = match.group(2)
        except IndexError:
            superclass_name = 'AnyObject'

        comment = f'// declare a new class {name} with superclass {superclass_name}'
        code = code.replace(match.group(0), comment + '\n' + match.group(0))

    # Add comments to struct declarations
    pattern = r'/struct\s+([a-zA-Z0-9_]+)\s*{'
    matches = re.finditer(pattern, no_comments_code)
    for match in matches:
        name = match.group(1)

        comment = f'// declare a new struct {name}'
        code = code.replace(match.group(0), comment + '\n' + match.group(0))

    # Add comments to enum declarations
    pattern = r'/enum\s+([a-zA-Z0-9_]+)\s*{'
    matches = re.finditer(pattern, no_comments_code)
    for match in matches:
        name = match.group(1)

        comment = f'// declare a new enum {name}'
        code = code.replace(match.group(0), comment + '\n' + match.group(0))

    # Add comments to protocol declarations
    pattern = r'/protocol\s+([a-zA-Z0-9_]+)\s*{'
    matches = re.finditer(pattern, no_comments_code)
    for match in matches:
        name = match.group(1)

        comment = f'// declare a new protocol {name}'
        code = code.replace(match.group(0), comment + '\n' + match.group(0))

    # Add comments to extension declarations
    pattern = r'/extension\s+([a-zA-Z0-9_]+)\s*{'
    matches = re.finditer(pattern, no_comments_code)
    for match in matches:
        name = match.group(1)

        comment = f'// declare a new extension {name}'
        code = code.replace(match.group(0), comment + '\n' + match.group(0))

    return code


def add_comments_to_assignments(code: str) -> str:
    """
    Adds comments to all assignments in a string.

    :param code: input code string
    :return: output code string
    """

    no_comments_code = remove_comments(code)

    pattern = r'([a-zA-Z0-9_]+)\s*=\s*([^\n]+)'
    matches = re.finditer(pattern, no_comments_code)
    for match in matches:
        name = match.group(1)
        value = match.group(2)

        comment = f'/* assign the value {value} to the variable {name} */'
        code = code.replace(match.group(0), match.group(0).rstrip() + '  ' + comment + '\n')

    return code


def add_comments_to_conditionals(code: str) -> str:
    """
    Adds comments to all conditionals in a string.

    :param code: input code string
    :return: output code string
    """

    no_comments_code = remove_comments(code)

    pattern = r'/if\s+([\S\s]+?)\s*{'
    matches = re.finditer(pattern, no_comments_code)
    for match in matches:
        condition = match.group(1)

        comment = f'/* if {condition} is true, execute the following code */'
        code = code.replace(match.group(0), comment + '\n' + match.group(0))

    pattern = r'/else\s*{'
    matches = re.finditer(pattern, no_comments_code)
    for match in matches:
        comment = f'/* otherwise, execute the following code */'
        code = code.replace(match.group(0), match.group(0) + '  ' + comment)

    pattern = r'/switch\s+([\S\s]+?)\s*{'
    matches = re.finditer(pattern, no_comments_code)
    for match in matches:
        condition = match.group(1)

        comment = f'/* switch on {condition} and execute the following code */'
        code = code.replace(match.group(0), match.group(0) + '  ' + comment)

    pattern = r'/case\s+([\S\s]+?)\s*{'
    matches = re.finditer(pattern, no_comments_code)
    for match in matches:
        condition = match.group(1)

        comment = f'/* if {condition} is true, execute the following code */'
        code = code.replace(match.group(0), match.group(0) + '  ' + comment)

    pattern = r'/default\s*{'
    matches = re.finditer(pattern, no_comments_code)
    for match in matches:
        comment = f'/* otherwise, execute the following code */'
        code = code.replace(match.group(0), match.group(0) + '  ' + comment)

    return code


def add_comments(code: str) -> str:
    """
    Adds comments to a swift code.

    :param code: input code string
    :return: output code string
    """
    # code = add_comments_to_imports(code)
    code = add_comments_to_declarations(code)
    code = add_comments_to_assignments(code)
    code = add_comments_to_conditionals(code)
    return code
