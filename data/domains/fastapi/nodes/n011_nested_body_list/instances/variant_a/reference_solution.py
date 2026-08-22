from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class Line(BaseModel):
    sku: str
    qty: int


class Order(BaseModel):
    customer: str
    lines: list[Line]


@app.post("/orders", status_code=201)
def create_order(order: Order):
    return {"customer": order.customer, "total_qty": sum(line.qty for line in order.lines)}
