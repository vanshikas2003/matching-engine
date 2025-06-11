from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "Matching engine is ready!"}
