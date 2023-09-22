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


@app.get("api/v1/get_id")
async def get_id(request: Request):
    return f'{request.client.host.replace(".", "")}{time.time_ns()}{random.randint(0, 1000000)}'


# WebSocket route for notifications
@app.websocket("/ws/notifications/{unique_id}")
async def websocket_endpoint(websocket: WebSocket, unique_id=0):
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
            await asyncio.sleep(1)  # Add a delay to control the update frequency
    except WebSocketDisconnect:
        pass
    except ConnectionClosedOK:
        pass


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

    notify(unique_id, 'Received project...')

    # check if zip file is provided
    if not zip_file.filename.endswith('.zip'):
        return {'message': 'Please provide a zip file.'}

    filename = zip_file.filename
    content = zip_file.file.read()

    root_dir = f'projects/{unique_id}'
    folder = f'{root_dir}/{filename[:-4]}/'
    os.makedirs(folder, exist_ok=True)

    # save the zip file
    with open(f'{root_dir}/{filename}', 'wb') as f:
        f.write(content)

    # extract the zip file
    shutil.unpack_archive(f'{root_dir}/{filename}', folder)

    # remove the zip file
    os.remove(f'{root_dir}/{filename}')

    notify(unique_id, 'Project extracted...')

    try:
        project = dir_to_dict(folder)
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

        dict_to_dir(project)

        notify(unique_id, 'Saving paraphrased project...')
        shutil.make_archive(f'{root_dir}/{filename[:-4]}', 'zip', folder)

        with open(f'{root_dir}/{filename}', "rb") as f:
            result = io.BytesIO(f.read())

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
    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, workers=multiprocessing.cpu_count())
