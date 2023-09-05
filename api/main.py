import asyncio
import io
import multiprocessing
import os
import shutil
import time

from fastapi import FastAPI, UploadFile, File, Request, Query
from fastapi.responses import StreamingResponse

from .pipeline import *

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/api/v1/paraphrase")
async def paraphrase(
        request: Request,
        zip_file: UploadFile = File(...),
        gpt_modification: bool = Query(False),
        modification_temperature: float = Query(0.6),
        modification_max_tries: int = Query(3),
        condition_transformation: bool = Query(True),
        loop_transformation: bool = Query(True),
        type_renaming: bool = Query(True),
        types_to_rename: str = Query("struct,enum,protocol"),
        file_renaming: bool = Query(False),
        variable_renaming: bool = Query(True),
        function_transformation: bool = Query(False),
        comment_adding: bool = Query(True),
        comment_temperature: float = Query(1.0),
        comment_max_tries: int = Query(3),
):
    """
    Endpoint for paraphrasing a zip file containing a swift project.

    Request format example:
    curl -X POST -F "zip_file=@/path/to/your/zipfile.zip" \
    "http://localhost:8000/api/v1/paraphrase?gpt_modification=true&modification_temperature=0.8&variable_renaming=false"

    :param request: request object
    :param zip_file: zip file containing a swift project

    :param gpt_modification: bool, whether to use GPT-3.5 Turbo to modify the project, recommended being False for stability
    :param modification_temperature: float between 0 qnd 2, temperature for GPT-3.5 Turbo, recommended to set lower for stability
    :param modification_max_tries: maximum number of tries to modify the project (in case of failure)
    :param condition_transformation: bool, whether to transform conditions, stable, recommended being True
    :param loop_transformation: bool, whether to transform loops, stable, recommended being True
    :param type_renaming: bool, whether to rename types, semi-stable, recommended being True for smaller projects
    :param types_to_rename: tuple of strings, types to rename, recommended being ('struct', 'enum', 'protocol')
    :param file_renaming: bool, whether to rename files, causes `Name` not found in Storyboard error, recommended being False
    :param variable_renaming: bool, whether to rename variables, stable, recommended being True
    :param function_transformation: bool, whether to transform functions, not stable, recommended being False
    :param comment_adding: bool, whether to add comments, stable, recommended being True (takes a long time)
    :param comment_temperature: float between 0 and 2, temperature for GPT-3.5 Turbo, lower values to save time and avoid fails, higher values for more diversity
    :param comment_max_tries: maximum number of tries to add comments (in case of failure), lower no save time, higher to ensure comments are added

    :return: zip file containing the paraphrased swift project or json with error message
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
            gpt_modification=gpt_modification,
            modification_temperature=modification_temperature,
            modification_max_tries=modification_max_tries,
            condition_transformation=condition_transformation,
            loop_transformation=loop_transformation,
            type_renaming=type_renaming,
            types_to_rename=types_to_rename.split(','),  # Convert comma-separated string to a list
            file_renaming=file_renaming,
            variable_renaming=variable_renaming,
            function_transformation=function_transformation,
            comment_adding=comment_adding,
            comment_temperature=comment_temperature,
            comment_max_tries=comment_max_tries,
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
