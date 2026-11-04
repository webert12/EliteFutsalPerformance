from datetime import date
from sqlalchemy import Date, ForeignKey, Integer, String, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class DiarioV13(Base):
    __tablename__ = 'diario_v13'
    __table_args__ = (UniqueConstraint('atleta_id', 'dia', name='uq_diario_v13_atleta_dia'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    atleta_id: Mapped[int] = mapped_column(ForeignKey('atletas.id'), nullable=False, index=True)
    dia: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    lanche_manha: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    lanche_tarde: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    refeicao_pos_treino: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    agua_disponivel: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    pausas_agua: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rotina_escolar: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    descanso_planejado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    disposicao: Mapped[str | None] = mapped_column(String(12))
    recuperacao: Mapped[str | None] = mapped_column(String(12))
    observacao: Mapped[str | None] = mapped_column(String(240))
