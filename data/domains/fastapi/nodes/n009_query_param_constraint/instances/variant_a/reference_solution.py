from fastapi import FastAPI, Query

app = FastAPI()


@app.get("/search")
def search(q: str = Query(min_length=3), limit: int = Query(default=10, ge=1, le=50)):
    return {"q": q, "limit": limit}
