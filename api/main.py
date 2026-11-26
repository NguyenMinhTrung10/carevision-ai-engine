from fastapi import FastAPI

app = FastAPI(title="CareVision AI Engine", version="0.1.0")


@app.get("/health")
def health():
    return {"service": "carevision-ai-engine", "status": "healthy", "version": "0.1.0"}
