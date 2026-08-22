from fastapi import FastAPI, Header

app = FastAPI()


@app.get("/whoami")
def whoami(x_token: str = Header(), x_trace: str | None = Header(default=None)):
    return {"token": x_token, "trace": x_trace}
