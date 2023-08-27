import zipfile
import os


CHANGEABLE_FILE_TYPES = ('.swift', '.storyboard', '.xib', '.xml')
STATIC_FILE_TYPES = ('json', '.png', '.jpg', '.jpeg', '.gif', '.pdf', '.txt', '.md', '.html', '.css', '.js',
                     '.wav', '.mp3', '.mp4', '.mov', '.avi')


def unzip(zip_path, target_path):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(target_path)


def list_files_in_dir(dir_path, file_types: tuple[str] = CHANGEABLE_FILE_TYPES) -> list[str]:
    file_list = []
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            for file_type in file_types:
                if file.endswith(file_type) and not file.startswith('._'):
                    file_list.append((os.path.join(root, file)).replace('\\', '/'))
    return file_list


def read_file_content(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            return content.strip()
    except FileNotFoundError:
        return f"Error: File '{file_path}' not found."
    except IOError as e:
        return f"Error: Could not read the file '{file_path}'. {e}"
    except UnicodeDecodeError as e:
        return f"Error: Could not read the file '{file_path}'. {e}"


def read_project(dir_path, file_types: tuple[str] = CHANGEABLE_FILE_TYPES):
    file_list = list_files_in_dir(dir_path, file_types)
    project = {}
    for file in file_list:
        project[file] = read_file_content(file)
    return project


def save_project(data: dict[str, str]):
    for file_path, content in data.items():
        path = file_path.replace('unzipped', 'result')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as file:
            file.write(content)


def copy_files(source_dir_path, target_dir_path, file_types: tuple[str] = STATIC_FILE_TYPES):
    for root, dirs, files in os.walk(source_dir_path):
        for file in files:
            for file_type in file_types:
                if file.endswith(file_type) and not file.startswith('._'):
                    source_file_path = os.path.join(root, file)
                    target_file_path = source_file_path.replace(source_dir_path, target_dir_path)
                    os.makedirs(os.path.dirname(target_file_path), exist_ok=True)
                    with open(source_file_path, 'rb') as source_file:
                        with open(target_file_path, 'wb') as target_file:
                            target_file.write(source_file.read())


def zip_dir(dir_path, zip_name):
    with zipfile.ZipFile(dir_path + '/' + zip_name, 'w') as zip_file:
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                zip_file.write(file_path, file_path.replace(dir_path, ''))
