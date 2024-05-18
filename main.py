from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
import hashlib
from tinydb import TinyDB, Query
from pydantic import BaseModel
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

URL = Query()

# Create a TinyDB instance without specifying the _default key
db = TinyDB('url.json', indent=4, separators=(',', ': '))

class URLInput(BaseModel):
    url: str

def generate_hash(input_string, hash_algorithm, hash_length):
    hash_object = hashlib.new(hash_algorithm)
    hash_object.update(input_string.encode('utf-8'))
    hash_digest = hash_object.hexdigest()
    return hash_digest[:hash_length]

@app.post("/shorten_url/")
async def shorten_url(request_data: URLInput):
    if not request_data.url:  # Check if the URL is an empty string
        raise HTTPException(status_code=400, detail="Empty URL")
    
    url = request_data.url
    result = db.search(URL.original_url == url)
    if result:
        original_url = result[0]["original_url"]
        short_url = result[0]["short_url"]
        return JSONResponse(status_code=302, content={"original_url": original_url, "shortened_url": short_url, "Message": "Key already exists"})

    hash_algorithm = "sha256"
    hash_length = 7  # Specify the desired length of the hash
    hash_value = generate_hash(url, hash_algorithm, hash_length)
    short_url = f"http://localhost:8000/{hash_value}"
    new_url = {"original_url": url, "short_url": short_url}
    db.insert(new_url)
    return JSONResponse(status_code=200, content={"original_url": url, "shortened_url": short_url, "Message": "Short URL generated"})

@app.get("/{short_url}/")
async def redirect(short_url: str):
    result = db.search(URL.short_url == f"http://localhost:8000/{short_url}")
    if result:
        long_url = result[0]["original_url"]
        return RedirectResponse(url=long_url)
    else:
        raise HTTPException(status_code=404, detail="Short URL not found")

@app.delete("/delete_url/")
async def delete_url(request_data: URLInput):
    url = request_data.url
    result = db.remove((URL.original_url == url) | (URL.short_url == url))
    if result:
        return {"message": "URL successfully deleted"}
    else:
        raise HTTPException(status_code=404, detail="URL Not Found")
    

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)



    