from datetime import datetime, timezone
from sqlalchemy import Integer, String, DateTime, ForeignKey, UniqueConstraint, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Consentimento(Base):
    __tablename__ = 'consentimentos_v6'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    atleta_id: Mapped[int] = mapped_column(ForeignKey('atletas.id'), unique=True, nullable=False)
    token_hash: Mapped[str | None] = mapped_column(String(64), unique=True)
    token_expira_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    responsavel_nome: Mapped[str | None] = mapped_column(String(120))
    responsavel_vinculo: Mapped[str | None] = mapped_column(String(30))
    versao_termo: Mapped[str | None] = mapped_column(String(20))
    aceito_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revogacao_hash: Mapped[str | None] = mapped_column(String(64), unique=True)
    revogado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

class ConviteEquipe(Base):
    __tablename__ = 'convites_v6'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    equipe_id: Mapped[int] = mapped_column(ForeignKey('equipes.id'), nullable=False, index=True)
    codigo_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    usado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

class SolicitacaoEquipe(Base):
    __tablename__ = 'solicitacoes_v6'
    __table_args__ = (UniqueConstraint('equipe_id', 'atleta_id', name='uq_solicitacao_v6'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    equipe_id: Mapped[int] = mapped_column(ForeignKey('equipes.id'), nullable=False, index=True)
    atleta_id: Mapped[int] = mapped_column(ForeignKey('atletas.id'), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default='pendente', nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
