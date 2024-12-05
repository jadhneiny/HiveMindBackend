from fastapi import FastAPI
from app.routes import user_routes

app = FastAPI()

# Include user-related routes
app.include_router(user_routes, prefix="/api/users")

@app.get("/")
async def root():
    return {"message": "Welcome to HiveMind Backend!"}
