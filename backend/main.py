from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import questions, tests, users, packages

app = FastAPI(title="ScoreIvy API", version="1.0.0")

# CORS middleware to allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(questions.router, prefix="/api/questions", tags=["questions"])
app.include_router(tests.router, prefix="/api/tests", tags=["tests"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(packages.router, prefix="/api/packages", tags=["packages"])


@app.get("/")
async def root():
    return {"message": "ScoreIvy API"}


@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

