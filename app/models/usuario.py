from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime

from app.database import Base


class Usuario(Base):

    __tablename__ = "usuarios"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    nome = Column(
        String(100),
        nullable=False
    )


    email = Column(
        String(150),
        unique=True,
        nullable=False,
        index=True
    )


    senha_hash = Column(
        String(255),
        nullable=False
    )


    tipo_usuario = Column(
        String(30),
        default="atleta"
    )


    ativo = Column(
        Boolean,
        default=True
    )


    data_criacao = Column(
        DateTime,
        default=datetime.utcnow
  )
