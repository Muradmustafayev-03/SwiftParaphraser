import io
import multiprocessing
import os
import shutil
import time

from fastapi import FastAPI, UploadFile, File, Request, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from .pipeline import *

app = FastAPI()


# # Define your CORS configuration
# origins = [
#     "http://127.0.0.1",
#     "http://127.0.0.1:8000",
#     "https://swiftparaphraser-production.up.railway.app",
# ]

# Add CORS middleware to the FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,  # Set this to True if you want to allow credentials (e.g., cookies)
    allow_methods=["*"],  # You can specify HTTP methods here (e.g., ["GET", "POST"])
    allow_headers=["*"],  # You can specify HTTP headers here
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/api/v1/paraphrase")
async def paraphrase(
        request: Request,
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
    "http://localhost:8000/api/v1/paraphrase?gpt_modification=true&modification_temperature=0.8&variable_renaming=false"

    :param request: request object
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

    # check if zip file is provided
    if not zip_file.filename.endswith('.zip'):
        return {"message": "Please provide a zip file."}

    unique_id = f'{request.client.host.replace(".", "")}{time.time_ns()}{random.randint(0, 1000000)}'

    filename = zip_file.filename
    content = zip_file.file.read()

    root_dir = f'projects/{unique_id}'
    folder = f'{root_dir}/{filename[:-4]}/'
    os.makedirs(folder, exist_ok=True)

    # unzip file and save to folder
    with open(f'{root_dir}/{filename}', 'wb') as f:
        f.write(content)

    shutil.unpack_archive(f'{root_dir}/{filename}', folder)
    os.remove(f'{root_dir}/{filename}')

    try:
        project = dir_to_dict(folder)
        project = await preprocess(project)
        project = await pipeline(
            project,
            condition_transformation=condition_transformation,
            loop_transformation=loop_transformation,
            type_renaming=type_renaming,
            types_to_rename=types_to_rename.split(','),  # Convert comma-separated string to a list
            file_renaming=file_renaming,
            variable_renaming=variable_renaming,
            comment_adding=comment_adding,
        )

        dict_to_dir(project)
        print('finished saving project')

        shutil.make_archive(f'{root_dir}/{filename[:-4]}', 'zip', folder)

        with open(f'{root_dir}/{filename}', "rb") as f:
            result = io.BytesIO(f.read())

        return StreamingResponse(result, media_type="application/zip",
                                 headers={"Content-Disposition": f"attachment; filename=paraphrased_{filename}"})
    except Exception as e:
        return {"message": "Something went wrong. Please try again. Error: " + str(e)}
    finally:
        shutil.rmtree(root_dir)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, workers=multiprocessing.cpu_count())
