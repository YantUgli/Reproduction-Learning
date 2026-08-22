from fastapi import FastAPI, HTTPException

app = FastAPI()


@app.post("/accounts/{name}")
def create_account(name: str):
    if name == "admin":
        raise HTTPException(status_code=409, detail="account already exists")
    if len(name) < 3:
        raise HTTPException(status_code=400, detail="name too short")
    return {"name": name}
