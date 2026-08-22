from fastapi import FastAPI, Path

app = FastAPI()


@app.get("/items/{item_id}")
def read_item(item_id: int = Path(gt=0)):
    return {"item_id": item_id}
