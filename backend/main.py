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


def pipeline(source_path, result_path, filename, temperature=1.0):
    project = read_project(source_path)

    project = apply_to_project(project, remove_comments)
    project = apply_to_project(project, remove_empty_lines)
    print('finished removing comments and empty lines')

    project = apply_to_project(project, transform_conditions)
    project = apply_to_project(project, transform_loops, index='iterationIndex1')
    project = apply_to_project(project, transform_loops, index='iterationIndex2')
    project = apply_to_project(project, transform_loops, index='iterationIndex3')
    print('finished transforming conditions and loops')

    names = find_all_names(project)
    rename_map = generate_rename_map(names)
    project = rename_items(project, rename_map)
    print('finished renaming')

    project = apply_to_project(project, add_comments, temperature=temperature)
    print('finished adding comments')

    save_project(project)
    print('finished saving project')

    copy_files(source_path, result_path)
    print('finished adding static files')

    zip_dir(result_path, filename)
    print('finished zipping project')


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
    source_path = f'{root_dir}/{filename[:-4]}/source'
    unzipped_path = f'{root_dir}/{filename[:-4]}/unzipped'
    result_path = f'{root_dir}/{filename[:-4]}/result'

    try:
        os.makedirs(source_path)
        os.makedirs(unzipped_path)
        os.makedirs(result_path)
    except FileExistsError:
        return {"message": "Too many requests. Please try again later."}

    with open(f'{source_path}/{filename}', 'wb') as f:
        f.write(content)

    # unzip file
    unzip(f'{source_path}/{filename}', f'{unzipped_path}/{filename[:-4]}')

    try:
        pipeline(unzipped_path, result_path, filename, 1.0)
        print('finished paraphrasing')

        with open(f'{result_path}/{filename}', "rb") as f:
            result = io.BytesIO(f.read())

        return StreamingResponse(result, media_type="application/zip",
                                 headers={"Content-Disposition": f"attachment; filename=paraphrased_{filename}"})
    except Exception as e:
        return {"message": "Something went wrong. Please try again. Error: " + str(e)}
    finally:
        shutil.rmtree(root_dir)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
