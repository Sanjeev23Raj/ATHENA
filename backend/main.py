from fastapi import FastAPI
from .routes import router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Athena AI API",
    description="Multimodal AI-Agent powered by Gemini",
    version="1.0.0"
)

# Allow CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
def root():
    return {"message": "Welcome to Athena AI API"}
