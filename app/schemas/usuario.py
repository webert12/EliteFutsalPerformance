from pydantic import BaseModel, EmailStr, Field, ConfigDict

class UsuarioCriacao(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    email: EmailStr
    senha: str = Field(min_length=12, max_length=128)

class UsuarioLogin(BaseModel):
    email: EmailStr
    senha: str

class UsuarioPublico(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    email: EmailStr
    tipo_usuario: str
