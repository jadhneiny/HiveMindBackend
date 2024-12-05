from fastapi import FastAPI
from routes import router

app = FastAPI()

# Include the router
app.include_router(router)

@app.get("/")
def root():
    return {"message": "Welcome to HiveMind Backend!"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
