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


def add_comments(project: dict) -> dict:
    return project
