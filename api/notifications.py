def notify(project_id, message):
    with open(f'notifications/{project_id}.txt', 'w') as file:
        file.write(message)
    print(message)


def receive_notification(project_id):
    with open(f'notifications/{project_id}.txt', 'r') as file:
        message = file.read()
    return message
