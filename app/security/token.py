from datetime import datetime, timedelta

from jose import jwt

from app.config import settings


ALGORITMO = "HS256"


def criar_token(dados: dict):

    dados_token = dados.copy()

    validade = datetime.utcnow() + timedelta(
        hours=24
    )

    dados_token.update(
        {
            "exp": validade
        }
    )


    token = jwt.encode(
        dados_token,
        settings.SECRET_KEY,
        algorithm=ALGORITMO
    )


    return token
