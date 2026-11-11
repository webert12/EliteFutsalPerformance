from sqlalchemy import Integer, String, Boolean, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class EscalacaoV162(Base):
    __tablename__ = 'escalacoes_v162'
    __table_args__ = (UniqueConstraint('jogo_id','atleta_id',name='uq_v162_jogo_atleta'), CheckConstraint('amarelos >= 0 AND amarelos <= 2'))
    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    jogo_id: Mapped[int] = mapped_column(ForeignKey('jogos_v16.id'),nullable=False,index=True)
    atleta_id: Mapped[int] = mapped_column(ForeignKey('atletas.id'),nullable=False,index=True)
    titular: Mapped[bool] = mapped_column(Boolean,nullable=False,default=False)
    posicao: Mapped[str] = mapped_column(String(20),nullable=False,default='linha')
    amarelos: Mapped[int] = mapped_column(Integer,nullable=False,default=0)
    vermelho: Mapped[bool] = mapped_column(Boolean,nullable=False,default=False)
