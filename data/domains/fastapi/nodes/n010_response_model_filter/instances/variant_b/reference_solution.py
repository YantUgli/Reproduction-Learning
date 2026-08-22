from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class EmployeeIn(BaseModel):
    name: str
    salary: int
    department: str


class EmployeeOut(BaseModel):
    name: str
    department: str


@app.post("/employees", response_model=EmployeeOut, status_code=201)
def create_employee(employee: EmployeeIn):
    return employee
