from routes import router

from fastapi import FastAPI

app = FastAPI()

# Include routes
app.include_router(router)

@app.get("/")
def root():
    return {"message": "Welcome to HiveMind Backend!"}

@app.get("/health")
def health_check():
    return {"status": "OK"}



