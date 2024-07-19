"""
file written by : cool-dev-guy
based on ciarands vidsrc resolver's.
This is an ASGI made using fastapi as a proof of concept and for educational uses.The writer/dev is not responsible for any isues caused by this project.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware # CORS
import gzip
from models import vidsrctoget,vidsrcmeget,vidsrctogetfutoken,info,fetch,fetchserver,fetchsource,fetchstreaming,fetchripstreaming
from io import BytesIO
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
app = FastAPI()

class DataModal(BaseModel):
    url: str
    imdb_id : str


@app.get('/')
async def index():
    return await info()

@app.get('/vidsrc/{dbid}')
async def vidsrc(dbid:str,s:int=None,e:int=None):
    if dbid:
        return {
            "status":200,
            "info":"success",
            "sources":await vidsrctoget(dbid,s,e)
        }
    else:
        raise HTTPException(status_code=404, detail=f"Invalid id: {dbid}")
    
@app.get('/susflix/{dbid}')
async def susflix(dbid:str,s:int=None,e:int=None):
    if dbid:
        return {
            "status":200,
            "info":"success",
            "sources":await fetchstreaming(dbid,s,e)
        }
    else:
        raise HTTPException(status_code=404, detail=f"Invalid id: {dbid}")
    
@app.get('/ee3/{dbid}')
async def ee3(dbid:str,s:int=None,e:int=None):
    if dbid:
        return {
            "status":200,
            "info":"success",
            "sources":await fetchripstreaming(dbid,s,e)
        }
    else:
        raise HTTPException(status_code=404, detail=f"Invalid id: {dbid}")
       
@app.get('/getserver/{dbid}')
async def getserver(dbid:str,s:int=None,e:int=None):
     if dbid:
         return {
             "status":200,
             "info":"success",
             "sources":await fetchserver(dbid,s,e)
         }
     else:
         raise HTTPException(status_code=404, detail=f"Invalid imdb_id: {dbid}")
    
# @app.post('/getsource/')
# async def getsource(model: DataModal):
#     if model.url:
#         return {
#             "status":200,
#             "info":"success",
#             "sources":await fetchsource(model.url)
#         }
#     else:
#         raise HTTPException(status_code=404, detail=f"Invalid url: {model.url}")
    
@app.get('/vsrcme/{dbid}')
async def vsrcme(dbid:str = '',s:int=None,e:int=None,l:str='eng'):
    if dbid:
        return {
            "status":200,
            "info":"success",
            "sources":await vidsrcmeget(dbid,s,e)
        }
    else:
        raise HTTPException(status_code=404, detail=f"Invalid id: {dbid}")

@app.get('/streams/{dbid}')
async def streams(dbid:str = '',s:int=None,e:int=None,l:str='eng'):
    if dbid:
        return {
            "status":200,
            "info":"success",
            "sources":await vidsrcmeget(dbid,s,e) + await vidsrctoget(dbid,s,e)
        }
    else:
        raise HTTPException(status_code=404, detail=f"Invalid id: {dbid}")
    
@app.get("/subs")
async def subs(url: str):
    try:
        response = await fetch(url)
        with gzip.open(BytesIO(response.content), 'rt', encoding='utf-8') as f:
            subtitle_content = f.read()
        async def generate():
            yield subtitle_content.encode("utf-8")
        return StreamingResponse(generate(), media_type="application/octet-stream", headers={"Content-Disposition": "attachment; filename=subtitle.srt"})

    except:
        raise HTTPException(status_code=500, detail=f"Error fetching subtitle")

