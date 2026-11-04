from datetime import date
from sqlalchemy import Integer, String, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class EventoV10(Base):
    __tablename__='eventos_v10'
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    equipe_id:Mapped[int]=mapped_column(ForeignKey('equipes.id'),nullable=False,index=True)
    treinador_id:Mapped[int]=mapped_column(ForeignKey('usuarios.id'),nullable=False)
    dia:Mapped[date]=mapped_column(Date,nullable=False,index=True)
    tipo:Mapped[str]=mapped_column(String(24),nullable=False)
    titulo:Mapped[str]=mapped_column(String(120),nullable=False)
    detalhes:Mapped[str]=mapped_column(String(800),nullable=False)

class DistribuicaoV10(Base):
    __tablename__='distribuicoes_v10'
    __table_args__=(UniqueConstraint('evento_id','atleta_id',name='uq_evento_v10_atleta'),)
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    evento_id:Mapped[int]=mapped_column(ForeignKey('eventos_v10.id'),nullable=False,index=True)
    atleta_id:Mapped[int]=mapped_column(ForeignKey('atletas.id'),nullable=False,index=True)
