from fastapi import FastAPI, Query

app = FastAPI()


@app.get("/users")
def list_users(name: str = Query(min_length=2), page: int = Query(default=1, ge=1, le=20)):
    return {"name": name, "page": page}
