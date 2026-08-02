from pydantic import BaseModel, EmailStr


class UsuarioCriacao(BaseModel):

    nome: str

    email: EmailStr

    senha: str

    tipo_usuario: str = "atleta"



class UsuarioLogin(BaseModel):

    email: EmailStr

    senha: str
