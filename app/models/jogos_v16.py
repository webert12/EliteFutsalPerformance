from sqlalchemy import Integer, String, Date, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from datetime import date

class JogoV16(Base):
    __tablename__ = 'jogos_v16'
    __table_args__ = (CheckConstraint('gols_pro >= 0 AND gols_contra >= 0'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    equipe_id: Mapped[int] = mapped_column(ForeignKey('equipes.id'), nullable=False, index=True)
    treinador_id: Mapped[int] = mapped_column(ForeignKey('usuarios.id'), nullable=False)
    dia: Mapped[date] = mapped_column(Date, nullable=False)
    adversario: Mapped[str] = mapped_column(String(120), nullable=False)
    competicao: Mapped[str] = mapped_column(String(120), nullable=False)
    local: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default='agendado')
    gols_pro: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    gols_contra: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

class EstatisticaV16(Base):
    __tablename__ = 'estatisticas_jogo_v16'
    __table_args__ = (UniqueConstraint('jogo_id','atleta_id',name='uq_v16_jogo_atleta'),CheckConstraint('gols >= 0 AND assistencias >= 0 AND minutos >= 0 AND minutos <= 120'))
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    jogo_id: Mapped[int] = mapped_column(ForeignKey('jogos_v16.id'), nullable=False, index=True)
    atleta_id: Mapped[int] = mapped_column(ForeignKey('atletas.id'), nullable=False, index=True)
    gols: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    assistencias: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    minutos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
