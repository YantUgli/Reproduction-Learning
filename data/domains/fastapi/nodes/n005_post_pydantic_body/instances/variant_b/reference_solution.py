from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class User(BaseModel):
    name: str
    age: int


@app.post("/users", status_code=201)
def create_user(user: User):
    return {"name": user.name, "age": user.age}
