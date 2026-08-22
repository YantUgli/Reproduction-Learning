from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class UserIn(BaseModel):
    username: str
    password: str
    email: str


class UserOut(BaseModel):
    username: str
    email: str


@app.post("/users", response_model=UserOut, status_code=201)
def create_user(user: UserIn):
    return user
