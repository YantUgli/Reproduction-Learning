from fastapi import FastAPI

app = FastAPI()


@app.post("/jobs", status_code=202)
def enqueue_job():
    return {"queued": True}


@app.delete("/jobs/{job_id}", status_code=204)
def delete_job(job_id: int):
    return None
