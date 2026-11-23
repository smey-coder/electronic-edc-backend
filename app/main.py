from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import all API routers
from app.api.v1.auth import router as auth_router
from app.api.v1.user import router as user_router
from app.api.v1.role import router as role_router
from app.api.v1.permission import router as permission_router
from app.api.v1.license_key import router as license_router
from app.api.v1.student_auth import router as student_auth_router
# from app.api.v1.rbac import router as rbac_router
# from app.api.v1.calculation import router as calc_router
from app.api.v1.students import router as student_router

# Initialize FastAPI application
app = FastAPI(
    title="Electronic EDC Platform API",
    description="Backend API for ICT University Electrical Engineering Calculation and Learning System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS Middleware (Allows React/Vite or other frontend clients to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific frontend origins (e.g., ["http://localhost:5173"])
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers under the /api/v1 prefix
app.include_router(auth_router, prefix="/api/v1") #auth pulish
app.include_router(user_router, prefix="/api/v1") #user 
app.include_router(role_router, prefix="/api/v1") #role
app.include_router(permission_router, prefix="/api/v1") #permission
app.include_router(license_router, prefix="/api/v1")  #License key
app.include_router(student_auth_router, prefix="/api/v1") # Student auth 



# app.include_router(rbac_router, prefix="/api/v1")
# app.include_router(calc_router, prefix="/api/v1")
app.include_router(student_router, prefix="/api/v1")


@app.get("/", tags=["Health Check"])
def root():
    """Root health check endpoint to verify API status."""
    return {
        "status": "online",
        "system": "Electronic EDC Platform API",
        "version": "1.0.0",
        "documentation": "http://127.0.0.1:8000/docs"
    }