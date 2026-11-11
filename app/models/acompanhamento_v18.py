from datetime import datetime, timezone, date
from sqlalchemy import Integer, String, Date, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class PlanoDiaV18(Base):
    __tablename__='planos_dia_v18'
    __table_args__=(UniqueConstraint('atleta_id','dia',name='uq_plano_dia_v18'),)
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    atleta_id:Mapped[int]=mapped_column(ForeignKey('atletas.id'),index=True,nullable=False)
    dia:Mapped[date]=mapped_column(Date,nullable=False)
    tipo:Mapped[str]=mapped_column(String(12),nullable=False)
    horario_atividade:Mapped[str|None]=mapped_column(String(5))
    escola_inicio:Mapped[str|None]=mapped_column(String(5))
    escola_fim:Mapped[str|None]=mapped_column(String(5))
    observacao:Mapped[str|None]=mapped_column(String(400))
    criado_em:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

class ConversaV18(Base):
    __tablename__='conversas_v18'
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    equipe_id:Mapped[int]=mapped_column(ForeignKey('equipes.id'),index=True,nullable=False)
    atleta_id:Mapped[int]=mapped_column(ForeignKey('atletas.id'),index=True,nullable=False)
    treinador_id:Mapped[int]=mapped_column(ForeignKey('usuarios.id'),index=True,nullable=False)
    autor_id:Mapped[int]=mapped_column(ForeignKey('usuarios.id'),nullable=False)
    mensagem:Mapped[str]=mapped_column(Text,nullable=False)
    criado_em:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
