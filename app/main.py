from fastapi import FastAPI
from api.routes import user_routes
from api.database import init_db

app = FastAPI()

# Include the user routes
app.include_router(user_routes, prefix="/api/users", tags=["Users"])

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.get("/")
async def root():
    return {"message": "Welcome to HiveMind Backend!"}
