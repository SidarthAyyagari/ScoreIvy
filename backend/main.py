from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.routers import questions, tests, users, packages, auth, test_results

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="ScoreIvy API", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    logger.info("ScoreIvy API starting up...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("ScoreIvy API shutting down...")

# CORS middleware to allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(questions.router, prefix="/api/questions", tags=["questions"])
app.include_router(tests.router, prefix="/api/tests", tags=["tests"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(packages.router, prefix="/api/packages", tags=["packages"])
app.include_router(test_results.router, prefix="/api/test-results", tags=["test-results"])


@app.get("/")
async def root():
    return {"message": "ScoreIvy API"}


@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

