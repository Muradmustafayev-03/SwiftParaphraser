import io
import multiprocessing
import shutil
import time
import asyncio
from typing import Optional
import random
import subprocess
import platform

from fastapi import FastAPI, UploadFile, File, Request, Query, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from websockets.exceptions import ConnectionClosedOK

from .pipeline import pipeline
from .notifications import *

app = FastAPI()

# Add CORS middleware to the FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,  # Set this to True if you want to allow credentials (e.g., cookies)
    allow_methods=["*"],  # You can specify HTTP methods here (e.g., ["GET", "POST"])
    allow_headers=["*"],  # You can specify HTTP headers here
)


def unzip_archive(zip_file, destination):
    system = platform.system()
    if system == "Linux":
        # install unzip if not installed
        if shutil.which("unzip") is None:
            subprocess.run(["# yum install unzip -y"])
        subprocess.run(["unzip", zip_file, "-d", destination])
    elif system == "Windows":
        zip_file = os.path.abspath(zip_file).replace('/', '\\')  # Convert path to Windows format
        destination = os.path.abspath(destination).replace('/', '\\')  # Convert path to Windows format
        subprocess.run(
            ["powershell", "Expand-Archive", "-Path", f'"{zip_file}"', "-DestinationPath", f'"{destination}"'],
        )
    else:
        print("Unsupported operating system.")


@app.get("/api/v1/get_id")
async def get_id(request: Request, shuffle: Optional[bool] = False):
    """
    Get a unique id for the project.

    :param request: Request
    :param shuffle: bool, whether to shuffle the unique id
    :return: str, unique id
    """
    unique_id = f'{request.client.host.replace(".", "")}N{time.time_ns()}N{random.randint(0, 1000000)}'
    if shuffle:
        unique_id = ''.join(random.sample(unique_id, len(unique_id)))
    return unique_id


# WebSocket route for notifications
@app.websocket("/ws/notifications/{unique_id}")
async def websocket_endpoint(websocket: WebSocket, unique_id: Optional[str] = None):
    """
    WebSocket endpoint for notifications.

    Request format example:
    ws://localhost:8000/ws/notifications/1234567890
    Use your domain name instead of localhost when the backend is deployed.

    :param websocket: WebSocket
    :param unique_id: str, optional, unique id of the project to listen for notifications
    """
    await websocket.accept()
    last_notification = None
    await websocket.send_text('Listening for notifications...')
    try:
        while True:  # continuously check for new notifications
            if unique_id is None:
                # If the unique_id is not provided, close the connection
                await websocket.send_text('Invalid unique_id.')
                await websocket.close()
                break
            notification = receive_notification(unique_id)
            if notification != last_notification and notification is not None:  # only send notification if it is new
                await websocket.send_text(notification)  # send the notification
                last_notification = notification
            await asyncio.sleep(.1)  # Add a delay to control the update frequency
    except WebSocketDisconnect:
        remove_notification_file(unique_id)
    except ConnectionClosedOK:
        remove_notification_file(unique_id)


def paraphrase(
        project_id: str,
        filename: str,
        condition_transformation: bool = Query(True),
        loop_transformation: bool = Query(True),
        type_renaming: bool = Query(True),
        types_to_rename: str = Query("class,struct,enum,protocol"),
        file_renaming: bool = Query(False),
        function_transformation: bool = Query(True),
        variable_renaming: bool = Query(True),
        comment_adding: bool = Query(True),
        dummy_file_adding: bool = Query(True),
        dummy_file_number: int = 10,
        renaming_images: bool = Query(True)
):
    root_dir = f'projects/{project_id}'
    folder = f'{root_dir}/{filename[:-4]}/'

    try:
        assert_notify(project_id, 'Extracting project...')

        # extract the zip file
        unzip_archive(f'{root_dir}/{filename}', folder)

        # remove the zip file
        os.remove(f'{root_dir}/{filename}')

        # recursively extract all zip files
        for root, dirs, files in os.walk(folder):
            if root == '__MACOSX':
                continue
            for file in files:
                if file.endswith('.zip') and not file.startswith('._'):
                    shutil.unpack_archive(f'{root}/{file}', root)
                    os.remove(f'{root}/{file}')

        assert_notify(project_id, 'Project extracted...')

        # remove .git folder
        for root, dirs, files in os.walk(folder):
            if '__MACOSX' in root:
                continue
            if '.git' in dirs:
                shutil.rmtree(f'{root}/.git')

        assert_notify(project_id, 'Starting paraphrasing...')

        pipeline(
            project_id, folder,
            condition_transformation=condition_transformation,
            loop_transformation=loop_transformation,
            type_renaming=type_renaming,
            types_to_rename=types_to_rename.split(','),  # Convert comma-separated string to a list
            file_renaming=file_renaming,
            function_transformation=function_transformation,
            variable_renaming=variable_renaming,
            comment_adding=comment_adding,
            dummy_file_adding=dummy_file_adding,
            dummy_files_number=dummy_file_number,
            renaming_images=renaming_images
        )
        assert_notify(project_id, 'Paraphrasing completed...')

        assert_notify(project_id, 'Archiving the project...')
        shutil.make_archive(f'{root_dir}/{filename[:-4]}', 'zip', folder)
        assert_notify(project_id, 'Finished archiving the project...')
        with open(f'{root_dir}/info.txt', 'r') as f:
            info = f.readlines()
        info = [line for line in info if 'Ready' not in line]
        info.append('Ready: True')
        with open(f'{root_dir}/info.txt', 'w') as f:
            f.writelines(info)
        time.sleep(10)
        assert_notify(project_id, 'Project is ready to download')
    except AssertionError:
        remove_notification_file(project_id)
        time.sleep(10)
        shutil.rmtree(root_dir)
    except Exception as e:
        notify(project_id, f'Error: {e}')
        remove_notification_file(project_id)
        time.sleep(10)
        shutil.rmtree(root_dir)


@app.post("/api/v1/upload")
async def upload(
        request: Request,
        background_tasks: BackgroundTasks,
        project_id: str = Query(None),
        user_id: str = Query(None),
        zip_file: UploadFile = File(...),
        condition_transformation: bool = Query(True),
        loop_transformation: bool = Query(True),
        type_renaming: bool = Query(True),
        types_to_rename: str = Query("class,struct,enum,protocol"),
        file_renaming: bool = Query(True),
        function_transformation: bool = Query(True),
        variable_renaming: bool = Query(True),
        comment_adding: bool = Query(True),
        dummy_file_adding: bool = Query(True),
        dummy_files_number: int = 10,
        renaming_images: bool = Query(True)
):
    if not project_id:
        project_id = await get_id(request)
    if not user_id:
        user_id = await get_id(request, shuffle=True)

    # check if id is not in use (if there is no notification file or project folder)
    if receive_notification(project_id) is not None or os.path.exists(f'projects/{project_id}'):
        return JSONResponse({'message': 'Project ID already in use. Please try again.'}, 400)

    notify(project_id, f'Received project: {zip_file.filename}...')

    # check if zip file is provided
    if not zip_file.filename.endswith('.zip'):
        return JSONResponse({'message': 'Invalid file type. Please upload a zip file.'}, 400)

    filename = zip_file.filename
    content = zip_file.file.read()

    root_dir = f'projects/{project_id}'
    folder = f'{root_dir}/{filename[:-4]}/'

    try:
        assert_notify(project_id, 'Saving project...')
        os.makedirs(folder, exist_ok=True)

        # save the zip file
        with open(f'{root_dir}/{filename}', 'wb') as f:
            f.write(content)

        with open(f'{root_dir}/info.txt', 'w') as f:
            lines = [
                f'Project ID: {project_id}\n',
                f'User ID: {user_id}\n',
                f'Filename: {filename}\n',
                'Ready: False'
            ]
            f.writelines(lines)

        assert_notify(project_id, 'Project saved...')

        background_tasks.add_task(paraphrase, project_id, filename,
                                  condition_transformation, loop_transformation,
                                  type_renaming, types_to_rename, file_renaming,
                                  function_transformation, variable_renaming,
                                  comment_adding, dummy_file_adding,
                                  dummy_files_number, renaming_images)

        return JSONResponse({'message': 'File uploaded successfully',
                             'project_id': project_id,
                             'user_id': user_id,
                             }, 200)

    except Exception as e:
        return JSONResponse({
            'message': 'Failed to upload the file',
            'details': e
        }, 500)


@app.get("/api/v1/download")
async def download(project_id: str = Query(...), user_id: str = Query(...)):
    if not project_id or not user_id:
        return JSONResponse({'message': 'Please, provide project_id and user_id'}, 403)

    root_dir = f'projects/{project_id}'

    if not os.path.exists(root_dir):
        return JSONResponse({'message': 'Invalid project_id or user_id'}, 403)

    try:
        with open(f'{root_dir}/info.txt', 'r') as f:
            info = f.readlines()

        info = {line.split(': ')[0]: line.split(': ')[1].strip() for line in info}

        if info['User ID'] != user_id:
            return JSONResponse({'message': 'Invalid project_id or user_id'}, 403)
        if info['Ready'] != 'True':
            return JSONResponse({'message': 'The project is not ready yet'}, 400)

        filename = info['Filename']
    except Exception as e:
        return JSONResponse({'message': 'Failed to download the file', 'details': e}, 500)

    try:
        with open(f'{root_dir}/{filename}', "rb") as f:
            result = io.BytesIO(f.read())

        print(project_id, 'Sending paraphrased project...')
        return StreamingResponse(result, media_type="application/zip", status_code=200,
                                 headers={"Content-Disposition": f"attachment; filename=paraphrased_{filename}"})
    except Exception as e:
        return JSONResponse({'message': 'Failed to download the file', 'details': e}, 500)
    finally:
        remove_notification_file(project_id)
        time.sleep(10)
        shutil.rmtree(root_dir)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, workers=multiprocessing.cpu_count(), ws="websockets")
