from pydantic import BaseModel
from typing import Optional

class PermissionCreate(BaseModel):
    name: str          # ឧ. "student:create" ឬ "Create Student"
    description: Optional[str] = None

class PermissionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class PermissionResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True