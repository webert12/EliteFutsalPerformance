from datetime import date
from sqlalchemy import Integer, Date, ForeignKey, Boolean, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class HabitosDia(Base):
    __tablename__ = 'habitos_dia_v7'
    __table_args__ = (UniqueConstraint('atleta_id', 'dia', name='uq_habitos_v7_atleta_dia'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    atleta_id: Mapped[int] = mapped_column(ForeignKey('atletas.id'), nullable=False, index=True)
    dia: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    cafe: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    almoco: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    jantar: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    agua: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    descanso: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    observacao: Mapped[str | None] = mapped_column(String(300))
