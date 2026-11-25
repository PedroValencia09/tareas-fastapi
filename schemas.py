# schemas.py
from pydantic import BaseModel
from typing import Optional

# --- ESQUEMAS DE USUARIO Y AUTH ---
class UsuarioCreate(BaseModel):
    username: str
    password: str

class UsuarioResponse(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

# --- ESQUEMAS DE TAREAS ---
class TareaBase(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    completada: Optional[bool] = False

class TareaCreate(TareaBase):
    pass

class TareaUpdate(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    completada: Optional[bool] = None

class TareaResponse(TareaBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True