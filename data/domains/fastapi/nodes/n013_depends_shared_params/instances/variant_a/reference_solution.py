from fastapi import Depends, FastAPI

app = FastAPI()


def pagination(page: int = 1, size: int = 20) -> dict:
    return {"page": page, "size": size, "offset": (page - 1) * size}


@app.get("/posts")
def list_posts(pager: dict = Depends(pagination)):
    return pager


@app.get("/comments")
def list_comments(pager: dict = Depends(pagination)):
    return pager
