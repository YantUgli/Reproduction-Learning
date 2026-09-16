from fastapi import FastAPI

app = FastAPI()


@app.get("/cart")
def read_cart():
    # TODO: baca cookie "cart_count" (default 0, bertipe int) lewat Cookie()
    # dan kembalikan sebagai {"cart_count": cart_count}
    ...
