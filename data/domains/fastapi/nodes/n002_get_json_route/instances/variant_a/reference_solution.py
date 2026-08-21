from fastapi import FastAPI

app = FastAPI()


@app.get("/status")
def read_status():
    return {"service": "orders", "ok": True}
