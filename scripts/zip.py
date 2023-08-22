import zipfile


CHANGEABLE_FILE_TYPES = ('.swift', '.storyboard', '.xib')


def list_files_in_zip(zip_path, file_types: tuple[str] = CHANGEABLE_FILE_TYPES):
    file_list = []
    with zipfile.ZipFile(zip_path, 'r') as zip_file:
        for file in zip_file.namelist():
            for file_type in file_types:
                if file.endswith(file_type) and not file.split('/')[-1].startswith('._'):
                    file_list.append(file)
    return file_list


def list_exclude_files_in_zip(zip_path, exclude: tuple[str] = CHANGEABLE_FILE_TYPES):
    file_list = []
    with zipfile.ZipFile(zip_path, 'r') as zip_file:
        for file in zip_file.namelist():
            if file.split('/')[-1].startswith('._'):
                continue
            file_type = file.split('/')[-1].split('.')[-1]
            if file_type not in exclude:
                file_list.append(file)
    return file_list


def read_file_content_from_zip(zip_path, file_path):
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            content = zip_file.read(file_path)
            return content.decode('utf-8').strip()
    except FileNotFoundError:
        return f"Error: File '{file_path}' not found."
    except IOError as e:
        return f"Error: Could not read the file '{file_path}'. {e}"
    except UnicodeDecodeError as e:
        return f"Error: Could not read the file '{file_path}'. {e}"


def read_project_from_zip(zip_path, changeable: bool = True):
    file_list = list_files_in_zip(zip_path) if changeable else list_exclude_files_in_zip(zip_path)
    project = {}
    for file in file_list:
        project[file] = read_file_content_from_zip(zip_path, file)
    return project


def save_zip(zip_path, data: dict[str, str]):
    with zipfile.ZipFile(zip_path, 'w') as zip_file:
        for file_path, file_content in data.items():
            zip_file.writestr(file_path, file_content)
