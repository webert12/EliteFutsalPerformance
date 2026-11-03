from datetime import date, datetime, timezone
from sqlalchemy import Integer, String, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Tarefa(Base):
    __tablename__ = 'tarefas_v5'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    treinador_id: Mapped[int] = mapped_column(ForeignKey('usuarios.id'), nullable=False, index=True)
    atleta_id: Mapped[int] = mapped_column(ForeignKey('atletas.id'), nullable=False, index=True)
    dia: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    titulo: Mapped[str] = mapped_column(String(120), nullable=False)
    descricao: Mapped[str] = mapped_column(String(800), nullable=False)
    concluida_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
