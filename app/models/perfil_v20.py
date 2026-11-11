from datetime import date, datetime, timezone
from sqlalchemy import Integer, String, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class PerfilV20(Base):
    __tablename__='perfis_v20'
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    usuario_id:Mapped[int]=mapped_column(ForeignKey('usuarios.id'),unique=True,index=True,nullable=False)
    nascimento:Mapped[date]=mapped_column(Date,nullable=False)
    altura_cm:Mapped[int]=mapped_column(Integer,nullable=False)
    peso_kg:Mapped[int]=mapped_column(Integer,nullable=False)
    posicao:Mapped[str]=mapped_column(String(24),nullable=False)
    condicionamento:Mapped[str]=mapped_column(String(20),nullable=False)
    minutos_atividade:Mapped[int]=mapped_column(Integer,nullable=False)
    treinos_semanais:Mapped[int]=mapped_column(Integer,nullable=False)
    ocupacao:Mapped[str]=mapped_column(String(20),nullable=False)
    inicio_ocupacao:Mapped[str|None]=mapped_column(String(5))
    fim_ocupacao:Mapped[str|None]=mapped_column(String(5))

class SensacaoV20(Base):
    __tablename__='sensacoes_v20'
    __table_args__=(UniqueConstraint('usuario_id','dia',name='uq_sensacao_v20'),)
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    usuario_id:Mapped[int]=mapped_column(ForeignKey('usuarios.id'),index=True,nullable=False)
    dia:Mapped[date]=mapped_column(Date,nullable=False)
    cansaco:Mapped[int]=mapped_column(Integer,nullable=False)
    dor:Mapped[str]=mapped_column(String(16),nullable=False)
    sono:Mapped[int]=mapped_column(Integer,nullable=False)
    humor:Mapped[int]=mapped_column(Integer,nullable=False)
    criado_em:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
