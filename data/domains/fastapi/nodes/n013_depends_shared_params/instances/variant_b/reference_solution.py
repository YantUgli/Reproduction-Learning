from fastapi import Depends, FastAPI

app = FastAPI()


def listing(sort: str = "asc", limit: int = 5) -> dict:
    return {"sort": sort, "limit": limit, "reverse": sort == "desc"}


@app.get("/books")
def list_books(options: dict = Depends(listing)):
    return options


@app.get("/films")
def list_films(options: dict = Depends(listing)):
    return options
