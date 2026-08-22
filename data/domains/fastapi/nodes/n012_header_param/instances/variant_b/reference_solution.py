from fastapi import FastAPI, Header

app = FastAPI()


@app.get("/ping")
def ping(x_api_key: str = Header(), x_client: str = Header(default="unknown")):
    return {"key": x_api_key, "client": x_client}
