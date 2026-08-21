from fastapi import FastAPI, HTTPException

app = FastAPI()

USERS = {10: "ada", 20: "linus"}


@app.get("/users/{user_id}")
def get_user(user_id: int):
    if user_id not in USERS:
        raise HTTPException(status_code=404, detail="user not found")
    return {"id": user_id, "name": USERS[user_id]}
