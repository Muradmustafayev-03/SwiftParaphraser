from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import StreamingResponse, HTMLResponse
import multiprocessing
from scripts import *
import asyncio
import random
import shutil
import time
import io
import os

app = FastAPI()


async def preprocess(project: dict):
    project = await apply_to_project(project, remove_comments)
    project = await apply_to_project(project, remove_empty_lines)
    return project


async def pipeline(project: dict,
                   gpt_modification=False, modification_temperature=0.6, modification_max_tries=3,
                   condition_transformation=True, loop_transformation=True,
                   type_renaming=True, types_to_rename=('struct', 'enum', 'protocol'),
                   file_renaming=False, variable_renaming=True, function_transformation=False,
                   comment_adding=True, comment_temperature=1.0, comment_max_tries=3):
    """
    Project paraphrasing pipeline.
    :param project: dict, project to paraphrase
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
    """

    if gpt_modification:
        project = await apply_to_project(project, gpt_modify, exclude=['AppDelegate.swift', 'SceneDelegate.swift'],
                                         temperature=modification_temperature, max_tries=modification_max_tries)
        print('finished gpt modifying')

    if condition_transformation:
        project = await apply_to_project(project, transform_conditions)
        print('finished transforming conditions')

    if loop_transformation:
        project = await apply_to_project(project, transform_loops)
        print('finished transforming loops')

    if type_renaming:
        type_names = parse_types_in_project(project, include_types=types_to_rename)
        if type_names:
            rename_map = generate_rename_map(type_names)
            project = rename_types(project, rename_map, rename_files=file_renaming)
        print('finished renaming types')

    if variable_renaming:
        project = await apply_to_project(project, rename_variables)
        print('finished renaming local variables')

    if function_transformation:
        project = await apply_to_project(project, transform_functions,
                                         exclude=['AppDelegate.swift', 'SceneDelegate.swift'])
        print('finished transforming functions')

    if comment_adding:
        project = await apply_to_project(project, add_comments, temperature=comment_temperature,
                                         max_tries=comment_max_tries)
        print('finished adding comments')

    return project


@app.get("/")
async def root():
    with open("../frontend/index.html") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)


@app.post("/api/v1/paraphrase")
async def paraphrase(request: Request, zip_file: UploadFile = File(...)):
    unique_id = f'{request.client.host.replace(".", "")}{time.time_ns()}{random.randint(0, 1000000)}'

    filename = zip_file.filename
    content = zip_file.file.read()

    root_dir = f'../projects/{unique_id}'
    folder = f'{root_dir}/{filename[:-4]}/'
    os.makedirs(folder, exist_ok=True)

    # unzip file and save to folder
    with open(f'{root_dir}/{filename}', 'wb') as f:
        f.write(content)

    shutil.unpack_archive(f'{root_dir}/{filename}', folder)
    os.remove(f'{root_dir}/{filename}')

    try:
        project = dir_to_dict(folder)
        project = await preprocess(project)  # Asynchronously preprocess the project
        project = await pipeline(project)
        # asynchronously save project
        dict_to_dir(project)
        print('finished saving project')

        # Create a ZIP archive asynchronously
        await asyncio.to_thread(
            lambda: shutil.make_archive(f'{root_dir}/{filename[:-4]}', 'zip', folder)
        )

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
    uvicorn.run("main:app", host="127.0.0.1", port=8000, workers=multiprocessing.cpu_count())
