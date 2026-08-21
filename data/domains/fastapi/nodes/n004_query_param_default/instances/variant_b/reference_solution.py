from fastapi import FastAPI

app = FastAPI()


@app.get("/products")
def products(sort: str = "asc", page: int = 1):
    return {"sort": sort, "page": page}
