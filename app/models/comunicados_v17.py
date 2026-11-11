from datetime import datetime, timezone
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class ComunicadoV17(Base):
    __tablename__ = 'comunicados_v17'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    equipe_id: Mapped[int] = mapped_column(ForeignKey('equipes.id'), index=True, nullable=False)
    treinador_id: Mapped[int] = mapped_column(ForeignKey('usuarios.id'), nullable=False)
    titulo: Mapped[str] = mapped_column(String(120), nullable=False)
    mensagem: Mapped[str] = mapped_column(Text, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

class CienciaV17(Base):
    __tablename__ = 'ciencias_v17'
    __table_args__ = (UniqueConstraint('comunicado_id','atleta_id',name='uq_ciencia_v17'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    comunicado_id: Mapped[int] = mapped_column(ForeignKey('comunicados_v17.id'), nullable=False)
    atleta_id: Mapped[int] = mapped_column(ForeignKey('atletas.id'), nullable=False)
    lido_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
