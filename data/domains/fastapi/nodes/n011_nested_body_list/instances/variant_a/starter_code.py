from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# TODO: model anak (elemen list) + model induk yang memuat list[<anak>].

# TODO: route POST status_code=201 yang menjumlahkan field numerik tiap elemen.
