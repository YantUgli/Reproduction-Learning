from fastapi import FastAPI, Path

app = FastAPI()


@app.get("/pages/{page_no}")
def read_page(page_no: int = Path(gt=0)):
    return {"page_no": page_no}
