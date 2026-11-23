from pydantic import BaseModel
from typing import Optional, List


class PermissionBase(BaseModel):
    name: str
    description: Optional[str] = None


class PermissionResponse(PermissionBase):
    id: int

    class Config:
        from_attributes = True


class RoleBase(BaseModel):
    name: str
    status: str = "active"
    description: Optional[str] = None


class RoleCreate(RoleBase):
    permission_ids: List[int] = []


class RoleResponse(RoleBase):
    id: int
    permissions: List[PermissionResponse] = []

    class Config:
        from_attributes = True


class UserRoleAssign(BaseModel):
    user_id: int
    role_id: int