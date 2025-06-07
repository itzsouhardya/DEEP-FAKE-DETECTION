from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from Preprocessor import Authentication, customException, Responce, TaskMaster, Tools, sum, Middleware, single_img_bin
from fastapi.responses import HTMLResponse
import asyncio
import numpy as np

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

all_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]

@app.get("/", response_class=HTMLResponse)
def read_root():
    html_content = Responce.initial_responce()
    # return {"Ahoy hoy": "Universe"}
    return HTMLResponse(content=html_content)

@app.get("/api/")
def read_root():
    return {"result": "List of service is not loaded..", "time": Tools.timeStamp()}

class SingleImgLoader(BaseModel):
    img: str
    limit: int
    index: int
    key: str

@app.api_route("/load/single", methods=all_methods)
def read_root(data: SingleImgLoader, request: Request):
    if request.method not in ["GET", "POST", "SET"]:
        return customException.methodException(request.url.path, request.method)
    if(data.index <= data.limit and data.index > 0):
        single_img_bin.append(data.img)
        return {"ack": data.index, "time": Tools.timeStamp()}
    else:
        print("image index out of range")


class DfdDetector(BaseModel):
    ext: str
    media: str
    load: str
    key: str
    heatmap: str

@app.api_route("/api/dfdScanner", methods=all_methods)
def read_root(data: DfdDetector, request: Request):
    if request.method not in ["GET", "POST"]:
        return customException.methodException(request.url.path, request.method)
    if(data.load=='true' and single_img_bin!=[]):
        if Tools.base64_type(single_img_bin[0]) == 'image':
            src = TaskMaster.dfd_img(['load', data.ext], data.key, data.heatmap)
        else:
            src = TaskMaster.dfd_vdo(['load', data.ext], data.key, data.heatmap)
    else:
        media = data.media
        if Tools.base64_type(media) == 'image':
            src = TaskMaster.dfd_img([media, data.ext], data.key, data.heatmap)
        else:
            src = TaskMaster.dfd_vdo([media, data.ext], data.key, data.heatmap)
    if src == None or src == 1:
        return customException.unsupportException(request.url.path, data.ext)
    if src == 19:
        return customException.convertationException(request.url.path, data.ext)
    single_img_bin.clear()
    responce = Responce.model(data.key).update("result", src)
    return responce


@app.get("/test")
def read_root(a, b):
    result = sum(int(a), int(b))
    return {"sum": result, "time": Tools.timeStamp()}

@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"], include_in_schema=False)
async def catch_all(request: Request, full_path: str):
    return customException.notFoundException(full_path, request.method)