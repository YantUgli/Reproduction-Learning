from fastapi import FastAPI, HTTPException

app = FastAPI()


@app.post("/rooms/{code}")
def book_room(code: str):
    if code == "r101":
        raise HTTPException(status_code=409, detail="room already booked")
    if len(code) < 4:
        raise HTTPException(status_code=400, detail="code too short")
    return {"code": code}
