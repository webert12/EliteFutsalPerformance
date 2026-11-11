"""Agenda do atleta: somente eventos distribuídos a ele e autorizados."""
from datetime import date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario import Usuario
from app.models.planejamento_v10 import EventoV10, DistribuicaoV10
from app.routes.rotina import atleta_proprio
from app.routes.acesso import exigir_consentimento
from app.security.token import usuario_atual

router = APIRouter(prefix='/api/v19', tags=['V19 - Agenda'])

@router.get('/minha-agenda')
def minha_agenda(u: Usuario = Depends(usuario_atual), db: Session = Depends(get_db)):
    a = atleta_proprio(db, u)
    exigir_consentimento(db, a.id)
    hoje = date.today()
    rows = (db.query(EventoV10)
        .join(DistribuicaoV10, DistribuicaoV10.evento_id == EventoV10.id)
        .filter(DistribuicaoV10.atleta_id == a.id,
                EventoV10.dia >= hoje - timedelta(days=14),
                EventoV10.dia <= hoje + timedelta(days=90),
                EventoV10.tipo.in_(['treino', 'jogo', 'preparacao']))
        .order_by(EventoV10.dia, EventoV10.id).limit(200).all())
    return [{'id': e.id, 'dia': e.dia.isoformat(), 'tipo': e.tipo,
             'titulo': e.titulo, 'detalhes': e.detalhes} for e in rows]
