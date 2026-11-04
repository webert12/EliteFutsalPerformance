"""V9: check-in de bem-estar e avaliações técnicas individuais."""
from datetime import date
from sqlalchemy import Integer, String, Date, ForeignKey, UniqueConstraint, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class CheckinV9(Base):
    __tablename__='checkins_v9'
    __table_args__=(UniqueConstraint('atleta_id','dia',name='uq_checkin_v9_dia'),)
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    atleta_id:Mapped[int]=mapped_column(ForeignKey('atletas.id'),nullable=False,index=True)
    dia:Mapped[date]=mapped_column(Date,nullable=False,index=True)
    sono:Mapped[str]=mapped_column(String(12),nullable=False)
    cansaco:Mapped[int]=mapped_column(Integer,nullable=False)
    dor:Mapped[bool]=mapped_column(Boolean,nullable=False,default=False)
    observacao:Mapped[str|None]=mapped_column(String(300))

class AvaliacaoV9(Base):
    __tablename__='avaliacoes_v9'
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    atleta_id:Mapped[int]=mapped_column(ForeignKey('atletas.id'),nullable=False,index=True)
    treinador_id:Mapped[int]=mapped_column(ForeignKey('usuarios.id'),nullable=False)
    dia:Mapped[date]=mapped_column(Date,nullable=False,index=True)
    fundamento:Mapped[str]=mapped_column(String(30),nullable=False)
    nota:Mapped[int]=mapped_column(Integer,nullable=False)
    observacao:Mapped[str|None]=mapped_column(String(300))
