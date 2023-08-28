import os


CHANGEABLE_FILE_TYPES = ('.swift', '.xml', '.xib', '.storyboard', '.plist')
STATIC_FILE_TYPES = ('json', '.png', '.jpg', '.jpeg', '.gif', '.pdf', '.txt', '.md', '.html', '.css', '.js',
                     '.wav', '.mp3', '.mp4', '.mov', '.avi')


def dir_to_dict(dir_path, file_types: tuple[str] = CHANGEABLE_FILE_TYPES) -> dict[str, str]:
    file_list = []
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            for file_type in file_types:
                if file.endswith(file_type) and not file.startswith('._'):
                    file_list.append((os.path.join(root, file)).replace('\\', '/'))

    project = {}
    for file in file_list:
        with open(file, 'r') as f:
            project[file] = f.read()

    # remove files in file_list from the dir_path
    for file in file_list:
        os.remove(file)

    return project


def dict_to_dir(data: dict[str, str]):
    for file_path, content in data.items():
        with open(file_path, 'w') as file:
            file.write(content)
