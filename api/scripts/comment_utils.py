import regex as re


def find_all_imports(code: str) -> list:
    """
    Finds all imports in a string.

    :param code: input code string
    :return: list of import names
    """
    pattern = r'^import\s+([a-zA-Z0-9_]+)'
    matches = re.findall(pattern, code, flags=re.MULTILINE)
    return matches


def remove_all_imports(code: str) -> str:
    """
    Removes all imports from a string.

    :param code: input code string
    :return: output code string
    """
    pattern = r'^import\s+([a-zA-Z0-9_]+)'
    return re.sub(pattern, '', code, flags=re.MULTILINE)


def add_comments_to_imports(code: str) -> str:
    """
    Adds comments to all imports in a string.

    :param code: input code string
    :return: output code string
    """
    imports = find_all_imports(code)
    code = remove_all_imports(code)
    heading = '// MARK: - Imports\n'
    for import_name in imports:
        heading += f'import {import_name} // importing {import_name}\n'
    heading += '// MARK: - End of imports\n\n'
    return heading + code


def add_comments(code: str) -> str:
    """
    Adds comments to a swift code.

    :param code: input code string
    :return: output code string
    """
    code = add_comments_to_imports(code)
    return code
