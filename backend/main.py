from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from scripts import *
import uvicorn
import random
import shutil
import time
import io
import os

app = FastAPI()


def pipeline(root_dir, folder, filename, temperature=1.0):
    project = dir_to_dict(folder)

    project = apply_to_project(project, remove_comments)
    project = apply_to_project(project, remove_empty_lines)
    print('finished removing comments and empty lines')

    # project = apply_to_project(project, gpt_modify,
    #                            exclude=['AppDelegate.swift', 'SceneDelegate.swift'],
    #                            temperature=temperature)
    # print('finished gpt modifying')

    project = apply_to_project(project, transform_conditions)
    print('finished transforming conditions')

    project = apply_to_project(project, transform_loops, index='iterationIndex1')
    project = apply_to_project(project, transform_loops, index='iterationIndex2')
    project = apply_to_project(project, transform_loops, index='iterationIndex3')
    print('finished transforming loops')

    type_names = parse_in_project(project, parse_type_names)
    if type_names:
        rename_map = generate_rename_map(type_names)
        project = rename_items(project, rename_map, is_type=True, rename_files=False)
    print('finished renaming types')

    # func_names = parse_in_project(project, parse_func_names)
    # if func_names:
    #     rename_map = generate_rename_map(func_names)
    #     project = rename_items(project, rename_map)
    # print('finished renaming funcs')

    # var_names = parse_in_project(project, parse_var_names)
    # if var_names:
    #     rename_map = generate_rename_map(var_names)
    #     project = rename_items(project, rename_map)
    # print('finished renaming vars')

    project = apply_to_project(project, lambda x: x.replace('\nlet ', '\nvar '))
    print('finished replacing lets with vars')

    project = apply_to_project(project, add_comments, temperature=temperature)
    print('finished adding comments')

    # project = apply_to_project(project, fix_syntax)
    # print('finished fixing syntax')

    # save project
    dict_to_dir(project)
    print('finished saving project')

    shutil.make_archive(f'{root_dir}/{filename[:-4]}', 'zip', folder)


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
        pipeline(root_dir, folder, filename)
        print('finished paraphrasing')

        with open(f'{root_dir}/{filename}', "rb") as f:
            result = io.BytesIO(f.read())

        return StreamingResponse(result, media_type="application/zip",
                                 headers={"Content-Disposition": f"attachment; filename=paraphrased_{filename}"})
    except Exception as e:
        raise e
        return {"message": "Something went wrong. Please try again. Error: " + str(e)}
    finally:
        shutil.rmtree(root_dir)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
