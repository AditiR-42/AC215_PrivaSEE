import os
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from api.routers import summarize, recommend

# Dynamically set GOOGLE_APPLICATION_CREDENTIALS to the secrets folder
current_dir = os.path.dirname(os.path.abspath(__file__))
secrets_path = os.path.abspath(os.path.join(current_dir, "../../secrets/model-containerization.json"))
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = secrets_path

# Setup FastAPI app
app = FastAPI(title="API Server", description="API Server", version="v1")

# Enable CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=False,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def list_routes():
    for route in app.routes:
        print(f"{route.path} -> {route.name}")

# Routes
@app.get("/")
async def get_index():
    return {"message": "Welcome to PrivaSee"}

# Additional routers here
app.include_router(recommend.router)
app.include_router(summarize.router)


