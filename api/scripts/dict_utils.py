from .constants import CHANGEABLE_FILE_TYPES
import os


def dir_to_dict(dir_path: str, file_types: tuple = CHANGEABLE_FILE_TYPES) -> dict:
    """
    Converts a directory to a dictionary where the keys are the file paths and the values are the file contents.

    :param dir_path: path to the directory
    :param file_types: tuple of file types to include in the dictionary
    :return: dictionary where the keys are the file paths and the values are the file contents
    """
    file_list = []
    for root, dirs, files in os.walk(dir_path):
        # Check if any folder in the path is in FRAMEWORKS
        if 'Pods' in root.replace('\\', '/').split('/'):
            continue  # skip files in frameworks
        for file in files:
            for file_type in file_types:
                if file.endswith(file_type) and not file.startswith('._'):
                    file_list.append((os.path.join(root, file)).replace('\\', '/'))
            if file.endswith('.DS_Store'):
                os.remove(os.path.join(root, file))

    print(f'Found {len(file_list)} changeable files in {dir_path}')

    project = {}
    for file in file_list:
        with open(file, 'r', encoding='utf-8') as f:
            project[file.replace('\\', '/')] = f.read().replace('\u2028', ' ')

    # remove files in file_list from the dir_path
    for file in file_list:
        os.remove(file)

    return project


def dict_to_dir(data: dict):
    """
    Converts a dictionary to a directory where the keys are the file paths and the values are the file contents.

    :param data: dictionary where the keys are the file paths and the values are the file contents
    """
    for file_path, content in data.items():
        directory = '/'.join(file_path.split('/')[:-1])
        os.makedirs(directory, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)


def apply_to_project(project: dict, func: callable, exclude=(), *args, **kwargs):
    """
    Applies a function to a project. The function must take a file content as the first argument.

    :param project: project to apply the function to
    :param func: function to apply
    :param exclude: tuple of file names to exclude from the function
    :param args: args to pass to the function
    :param kwargs: kwargs to pass to the function
    :return:
    """

    for file_path, file_content in project.items():
        if file_path.endswith('.swift') and file_path.split('/')[-1] not in exclude:
            project[file_path] = func(file_content, *args, **kwargs)

    return project


def project_contains_string(project: dict, string: str) -> bool:
    """
    Checks if a project contains a string.

    :param project: project to check
    :param string: string to check
    :return: True if the project contains the string, False otherwise
    """
    for file_content in project.values():
        if string in file_content:
            return True
    return False
