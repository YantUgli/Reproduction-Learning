from fastapi import FastAPI, HTTPException

app = FastAPI()

ITEMS = {1: "apple", 2: "banana"}


@app.get("/items/{item_id}")
def get_item(item_id: int):
    if item_id not in ITEMS:
        raise HTTPException(status_code=404, detail="item not found")
    return {"id": item_id, "name": ITEMS[item_id]}
