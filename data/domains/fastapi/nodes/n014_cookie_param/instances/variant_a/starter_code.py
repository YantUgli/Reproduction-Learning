from fastapi import FastAPI

app = FastAPI()


@app.get("/profile")
def read_profile():
    # TODO: baca cookie "session_id" (default "guest") lewat Cookie() dan
    # kembalikan sebagai {"session_id": session_id}
    ...
