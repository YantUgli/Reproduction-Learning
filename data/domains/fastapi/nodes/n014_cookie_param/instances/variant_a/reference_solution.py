from fastapi import Cookie, FastAPI

app = FastAPI()


@app.get("/profile")
def read_profile(session_id: str = Cookie(default="guest")):
    return {"session_id": session_id}
