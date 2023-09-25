import io
import multiprocessing
import shutil
import time
import asyncio

from fastapi import FastAPI, UploadFile, File, Request, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from websockets.exceptions import ConnectionClosedOK

from .pipeline import *

app = FastAPI()

# Add CORS middleware to the FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,  # Set this to True if you want to allow credentials (e.g., cookies)
    allow_methods=["*"],  # You can specify HTTP methods here (e.g., ["GET", "POST"])
    allow_headers=["*"],  # You can specify HTTP headers here
)


@app.get("/api/v1/get_id")
async def get_id(request: Request):
    """
    Get a unique id for the project.

    :param request: Request
    :return: str, unique id
    """
    return f'{request.client.host.replace(".", "")}{time.time_ns()}{random.randint(0, 1000000)}'


# WebSocket route for notifications
@app.websocket("/ws/notifications/{unique_id}")
async def websocket_endpoint(websocket: WebSocket, unique_id=0):
    """
    WebSocket endpoint for notifications.

    Request format example:
    ws://localhost:8000/ws/notifications/1234567890
    Use your domain name instead of localhost when the backend is deployed.

    :param websocket: WebSocket
    :param unique_id: str, unique id of the project to listen for notifications
    """
    await websocket.accept()
    last_notification = None
    await websocket.send_text('Listening for notifications...')
    try:
        while True:  # continuously check for new notifications
            notification = receive_notification(unique_id)
            if notification != last_notification:  # only send notification if it is new
                if notification is None:
                    # if the notification file is removed, close the connection
                    await websocket.send_text('Finished listening for notifications.')
                    await websocket.close()
                    break
                await websocket.send_text(notification)  # send the notification
                last_notification = notification
            await asyncio.sleep(.1)  # Add a delay to control the update frequency
    except WebSocketDisconnect:
        remove_notification_file(unique_id)
    except ConnectionClosedOK:
        remove_notification_file(unique_id)


@app.post("/api/v1/paraphrase")
async def paraphrase(
        unique_id: str = Query("0"),
        zip_file: UploadFile = File(...),
        condition_transformation: bool = Query(True),
        loop_transformation: bool = Query(True),
        type_renaming: bool = Query(True),
        types_to_rename: str = Query("struct,enum,protocol"),
        file_renaming: bool = Query(False),
        variable_renaming: bool = Query(True),
        comment_adding: bool = Query(True),
):
    """
        Endpoint for paraphrasing a zip file containing a swift project.

        Request format example:
        curl -X POST -F "zip_file=@/path/to/your/zipfile.zip" \
        "http://localhost:8000/api/v1/paraphrase?unique_id=5235431&condition_transformation=False"
        Use your domain name instead of localhost when the backend is deployed.

        :param unique_id: str, unique id of the project. Required. Use the same id to get notifications about the project.
        :param zip_file: zip file containing a swift project. Required.

        :param condition_transformation: bool, whether to transform conditions, stable, recommended being True. Default: True.
        :param loop_transformation: bool, whether to transform loops, stable, recommended being True. Default: True.
        :param type_renaming: bool, whether to rename types, semi-stable, recommended being True for smaller projects. Default: True.
        :param types_to_rename: tuple of strings, types to rename, recommended being ('struct', 'enum', 'protocol').
        Possible types are: 'class', 'struct', 'enum', 'protocol'. Applies only if type_renaming is True. Default: ('struct', 'enum', 'protocol').
        :param file_renaming: bool, whether to rename files, causes `Name` not found in Storyboard error, recommended being False. Default: False.
        :param variable_renaming: bool, whether to rename variables, stable, recommended being True. Default: True.
        :param comment_adding: bool, whether to add comments, stable, recommended being True (takes a long time). Default: True.

        :return: zip file containing the paraphrased swift project or json with error message.
        """
    # check if id is not in use (if there is no notification file or project folder)
    if receive_notification(unique_id) is not None or os.path.exists(f'projects/{unique_id}'):
        return {'message': 'Please provide a unique id.'}

    notify(unique_id, 'Received project...')

    # check if zip file is provided
    if not zip_file.filename.endswith('.zip'):
        return {'message': 'Please provide a zip file.'}

    filename = zip_file.filename
    content = zip_file.file.read()

    root_dir = f'projects/{unique_id}'
    folder = f'{root_dir}/{filename[:-4]}/'

    try:
        assert receive_notification(unique_id) is not None, 'Connection interrupted.'
        notify(unique_id, 'Saving project...')
        os.makedirs(folder, exist_ok=True)

        # save the zip file
        with open(f'{root_dir}/{filename}', 'wb') as f:
            f.write(content)

        notify(unique_id, 'Project saved...')
        assert receive_notification(unique_id) is not None, 'Connection interrupted.'
        notify(unique_id, 'Extracting project...')

        # extract the zip file
        shutil.unpack_archive(f'{root_dir}/{filename}', folder)

        # remove the zip file
        os.remove(f'{root_dir}/{filename}')

        notify(unique_id, 'Project extracted...')

        assert receive_notification(unique_id) is not None, 'Connection interrupted.'
        notify(unique_id, 'Reading the project...')
        project = dir_to_dict(folder)

        assert receive_notification(unique_id) is not None, 'Connection interrupted.'
        notify(unique_id, 'Starting paraphrasing...')
        project = preprocess(unique_id, project)
        project = pipeline(
            unique_id, project,
            condition_transformation=condition_transformation,
            loop_transformation=loop_transformation,
            type_renaming=type_renaming,
            types_to_rename=types_to_rename.split(','),  # Convert comma-separated string to a list
            file_renaming=file_renaming,
            variable_renaming=variable_renaming,
            comment_adding=comment_adding,
        )

        assert receive_notification(unique_id) is not None, 'Connection interrupted.'
        dict_to_dir(project)

        assert receive_notification(unique_id) is not None, 'Connection interrupted.'
        notify(unique_id, 'Saving paraphrased project...')
        shutil.make_archive(f'{root_dir}/{filename[:-4]}', 'zip', folder)

        with open(f'{root_dir}/{filename}', "rb") as f:
            result = io.BytesIO(f.read())

        assert receive_notification(unique_id) is not None, 'Connection interrupted.'
        notify(unique_id, 'Sending paraphrased project...')
        return StreamingResponse(result, media_type="application/zip",
                                 headers={"Content-Disposition": f"attachment; filename=paraphrased_{filename}"})
    except Exception as e:
        return {"message": "Something went wrong. Please try again. Error: " + str(e)}
    finally:
        shutil.rmtree(root_dir)
        remove_notification_file(unique_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="127.0.0.1", port=8080, workers=multiprocessing.cpu_count())
