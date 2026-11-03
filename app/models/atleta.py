from datetime import date
from sqlalchemy import Integer, String, Float, ForeignKey, Date, Text, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Atleta(Base):
    __tablename__ = 'atletas'
    __table_args__ = (CheckConstraint('altura_cm > 0'), CheckConstraint('peso_kg > 0'))
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey('usuarios.id'), unique=True, nullable=False, index=True)
    nascimento: Mapped[date] = mapped_column(Date, nullable=False)
    posicao: Mapped[str] = mapped_column(String(30), nullable=False)
    altura_cm: Mapped[float] = mapped_column(Float, nullable=False)
    peso_kg: Mapped[float] = mapped_column(Float, nullable=False)
    pe_dominante: Mapped[str | None] = mapped_column(String(15))
    observacoes: Mapped[str | None] = mapped_column(Text)
    usuario = relationship('Usuario', back_populates='atleta')
    registros = relationship('RegistroDiario', back_populates='atleta', cascade='all, delete-orphan')

class RegistroDiario(Base):
    __tablename__ = 'registros_diarios'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    atleta_id: Mapped[int] = mapped_column(ForeignKey('atletas.id'), index=True, nullable=False)
    dia: Mapped[date] = mapped_column(Date, nullable=False)
    sono_horas: Mapped[float | None] = mapped_column(Float)
    agua_ml: Mapped[int | None] = mapped_column(Integer)
    esforco_0_10: Mapped[int | None] = mapped_column(Integer)
    duracao_treino_min: Mapped[int | None] = mapped_column(Integer)
    bem_estar_0_10: Mapped[int | None] = mapped_column(Integer)
    alimentacao_observacoes: Mapped[str | None] = mapped_column(Text)
    dor_ou_lesao: Mapped[bool] = mapped_column(default=False)
    atleta = relationship('Atleta', back_populates='registros')
