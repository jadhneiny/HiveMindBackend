from fastapi import FastAPI
from .routes import router

app = FastAPI()

# Include the user routes
app.include_router(router, prefix="/api", tags=["users"])

@app.get("/")
def read_root():
    return {"message": "Welcome to HiveMind Backend"}
