from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from api.routers import summarize, recommend

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


