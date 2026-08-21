from fastapi import FastAPI

app = FastAPI()


@app.get("/search")
def search(q: str = "", limit: int = 10):
    return {"q": q, "limit": limit}
