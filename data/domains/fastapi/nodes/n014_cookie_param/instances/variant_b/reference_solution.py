from fastapi import Cookie, FastAPI

app = FastAPI()


@app.get("/cart")
def read_cart(cart_count: int = Cookie(default=0)):
    return {"cart_count": cart_count}
