from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Union
import uvicorn

app = FastAPI()

class EchoData(BaseModel):
    data: Union[str, dict, None] = None

@app.api_route("/echo", methods=["GET", "POST", "PUT", "DELETE"])
async def echo(request: Request):
    # Get the method of the request
    method = request.method

    # Get the data sent in the request (JSON or plain text)
    try:
        json_data = await request.json()
        data = json_data
    except Exception:
        data = await request.body()
        data = data.decode("utf-8") if isinstance(data, bytes) else data

    # Prepare the response
    response = {
        "method": method,
        "data": data
    }

    return response

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5000, reload=True)
