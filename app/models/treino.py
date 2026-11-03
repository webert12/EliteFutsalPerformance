from sqlalchemy import Integer, String, Date, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date
from app.database import Base

class Equipe(Base):
    __tablename__ = 'equipes'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    categoria: Mapped[str] = mapped_column(String(20), nullable=False)
    treinador_id: Mapped[int] = mapped_column(ForeignKey('usuarios.id'), nullable=False, index=True)

class VinculoEquipe(Base):
    __tablename__ = 'vinculos_equipe'
    __table_args__ = (UniqueConstraint('equipe_id','atleta_id',name='uq_equipe_atleta'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    equipe_id: Mapped[int] = mapped_column(ForeignKey('equipes.id'), nullable=False, index=True)
    atleta_id: Mapped[int] = mapped_column(ForeignKey('atletas.id'), nullable=False, index=True)

class Treino(Base):
    __tablename__ = 'treinos_v4'
    __table_args__ = (CheckConstraint('duracao_min > 0 AND duracao_min <= 240'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    equipe_id: Mapped[int] = mapped_column(ForeignKey('equipes.id'), nullable=False, index=True)
    data: Mapped[date] = mapped_column(Date, nullable=False)
    objetivo: Mapped[str] = mapped_column(String(240), nullable=False)
    duracao_min: Mapped[int] = mapped_column(Integer, nullable=False)

class Presenca(Base):
    __tablename__ = 'presencas_v4'
    __table_args__ = (UniqueConstraint('treino_id','atleta_id',name='uq_treino_atleta'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    treino_id: Mapped[int] = mapped_column(ForeignKey('treinos_v4.id'), nullable=False, index=True)
    atleta_id: Mapped[int] = mapped_column(ForeignKey('atletas.id'), nullable=False)
    situacao: Mapped[str] = mapped_column(String(20), nullable=False)
