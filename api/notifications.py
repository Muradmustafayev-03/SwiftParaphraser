import os


def notify(project_id, message):
    os.makedirs('notifications/', exist_ok=True)
    with open(f'notifications/{project_id}.txt', 'w') as file:
        file.write(message)
    print(message)


def receive_notification(project_id):
    try:
        with open(f'notifications/{project_id}.txt', 'r') as file:
            message = file.read()
        return message
    except FileNotFoundError:
        return None


def remove_notification_file(project_id):
    try:
        os.remove(f'notifications/{project_id}.txt')
    except FileNotFoundError:
        pass


def assert_notify(project_id, message):
    assert receive_notification(project_id) is not None, 'Connection interrupted.'
    notify(project_id, message)
