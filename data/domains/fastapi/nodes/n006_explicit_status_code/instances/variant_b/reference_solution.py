from fastapi import FastAPI

app = FastAPI()


@app.post("/emails", status_code=202)
def accept_email():
    return {"accepted": True}


@app.delete("/emails/{email_id}", status_code=204)
def delete_email(email_id: int):
    return None
