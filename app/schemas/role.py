from pydantic import BaseModel
from typing import Optional, List

class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    permission_ids: Optional[List[int]] = []  # 📌 បញ្ជី ID របស់ Permissions ដែលបានជ្រើសរើស (Checkboxes)

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permission_ids: Optional[List[int]] = None  # 📌 បញ្ជី ID ថ្មីសម្រាប់ Update

class RoleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    permissions: List[int] = []  # Return ជា List នៃ Permission IDs សម្រាប់ Checkbox នៅ Frontend

    class Config:
        from_attributes = True