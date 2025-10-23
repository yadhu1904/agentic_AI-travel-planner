from fastapi import FastAPI
from backend.api import note
app = FastAPI()

app.include_router(note)