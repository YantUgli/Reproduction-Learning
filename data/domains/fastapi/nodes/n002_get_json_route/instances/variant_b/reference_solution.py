from fastapi import FastAPI

app = FastAPI()


@app.get("/info")
def read_info():
    return {"service": "users", "version": 2}
