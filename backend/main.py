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


def pipeline(source_path, result_path, temperature=1.0):
    project = read_project_from_zip(source_path)
    project = apply_to_project(project, remove_comments)
    project = apply_to_project(project, remove_empty_lines)

    names = find_all_names(project)
    rename_map = generate_rename_map(names)
    project = rename_items(project, rename_map)

    project = apply_to_project(project, add_comments, temperature=temperature)

    project.update(read_project_from_zip(source_path, STATIC_FILE_TYPES))
    save_zip(result_path, project)


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
    result_path = f'{root_dir}/{filename[:-4]}/result'

    try:
        os.makedirs(source_path)
        os.makedirs(result_path)
    except FileExistsError:
        return {"message": "Too many requests. Please try again later."}

    with open(f'{source_path}/{filename}', 'wb') as f:
        f.write(content)

    try:
        pipeline(f'{source_path}/{filename}', f'{result_path}/{filename}', 1.0)

        with open(f'{result_path}/{filename}', "rb") as f:
            result = io.BytesIO(f.read())

        return StreamingResponse(result, media_type="application/zip",
                                 headers={"Content-Disposition": f"attachment; filename=paraphrased_{filename}"})
    except Exception as e:
        print(e)
        return {"message": "Something went wrong. Please try again."}
    finally:
        shutil.rmtree(root_dir)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
