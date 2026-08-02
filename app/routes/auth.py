from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario

from app.schemas.usuario import (
    UsuarioCriacao,
    UsuarioLogin
)

from app.security.password import (
    criar_hash_senha,
    verificar_senha
)

from app.security.token import (
    criar_token
)


router = APIRouter(
    prefix="/auth",
    tags=["Autenticação"]
)



@router.post("/cadastro")
def cadastrar_usuario(
    dados: UsuarioCriacao,
    db: Session = Depends(get_db)
):

    usuario_existente = db.query(
        Usuario
    ).filter(
        Usuario.email == dados.email
    ).first()


    if usuario_existente:

        raise HTTPException(
            status_code=400,
            detail="Email já cadastrado"
        )


    novo_usuario = Usuario(

        nome=dados.nome,

        email=dados.email,

        senha_hash=criar_hash_senha(
            dados.senha
        ),

        tipo_usuario=dados.tipo_usuario
    )


    db.add(novo_usuario)

    db.commit()

    db.refresh(novo_usuario)


    return {
        "mensagem": "Usuário criado com sucesso",
        "usuario_id": novo_usuario.id
    }




@router.post("/login")
def login(
    dados: UsuarioLogin,
    db: Session = Depends(get_db)
):

    usuario = db.query(
        Usuario
    ).filter(
        Usuario.email == dados.email
    ).first()


    if not usuario:

        raise HTTPException(
            status_code=404,
            detail="Usuário não encontrado"
        )


    senha_ok = verificar_senha(
        dados.senha,
        usuario.senha_hash
    )


    if not senha_ok:

        raise HTTPException(
            status_code=401,
            detail="Senha incorreta"
        )


    token = criar_token(
        {
            "id": usuario.id,
            "tipo": usuario.tipo_usuario
        }
    )


    return {

        "access_token": token,

        "tipo": usuario.tipo_usuario

  }
