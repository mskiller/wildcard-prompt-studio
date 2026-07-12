from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import router as api_router

app = FastAPI(title="Wildcard Management Studio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
def health_check():
    return {"status": "ok"}
