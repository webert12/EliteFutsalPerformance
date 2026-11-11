"""V14: visualização histórica autorizada, sem interpretação clínica."""
from datetime import date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario import Usuario
from app.models.atleta import RegistroDiario
from app.models.diario_v13 import DiarioV13
from app.routes.rotina import atleta_proprio, verificar_treinador
from app.security.token import usuario_atual

router = APIRouter(prefix='/api/v14', tags=['V14 — Evolução'])
CAMPOS = ('lanche_manha', 'lanche_tarde', 'refeicao_pos_treino', 'agua_disponivel', 'pausas_agua', 'rotina_escolar', 'descanso_planejado')

def dados(db: Session, atleta_id: int, dias: int):
    inicio = date.today() - timedelta(days=dias - 1)
    habitos = db.query(DiarioV13).filter(DiarioV13.atleta_id == atleta_id, DiarioV13.dia >= inicio, DiarioV13.dia <= date.today()).order_by(DiarioV13.dia).all()
    registros = db.query(RegistroDiario).filter(RegistroDiario.atleta_id == atleta_id, RegistroDiario.dia >= inicio, RegistroDiario.dia <= date.today()).order_by(RegistroDiario.dia, RegistroDiario.id).all()
    por_dia = {}
    for x in habitos:
        por_dia[x.dia.isoformat()] = {'dia': x.dia.isoformat(), 'habitos': sum(bool(getattr(x, c)) for c in CAMPOS), 'habitos_total': len(CAMPOS), 'disposicao': x.disposicao, 'recuperacao': x.recuperacao}
    for x in registros:
        item = por_dia.setdefault(x.dia.isoformat(), {'dia': x.dia.isoformat(), 'habitos': None, 'habitos_total': len(CAMPOS), 'disposicao': None, 'recuperacao': None})
        item.update({'sono_horas': x.sono_horas, 'agua_ml': x.agua_ml, 'bem_estar_0_10': x.bem_estar_0_10, 'esforco_0_10': x.esforco_0_10, 'duracao_treino_min': x.duracao_treino_min})
    return {'periodo_dias': dias, 'dias': [por_dia[k] for k in sorted(por_dia)]}

@router.get('/minha-evolucao')
def minha_evolucao(periodo: int = 7, u: Usuario = Depends(usuario_atual), db: Session = Depends(get_db)):
    from fastapi import HTTPException
    if periodo not in (7, 30): raise HTTPException(422, 'Período deve ser 7 ou 30 dias')
    atleta = atleta_proprio(db, u)
    return dados(db, atleta.id, periodo)

@router.get('/atletas/{atleta_id}/evolucao')
def evolucao_atleta(atleta_id: int, periodo: int = 7, u: Usuario = Depends(usuario_atual), db: Session = Depends(get_db)):
    from fastapi import HTTPException
    if periodo not in (7, 30): raise HTTPException(422, 'Período deve ser 7 ou 30 dias')
    verificar_treinador(db, u, atleta_id)
    return dados(db, atleta_id, periodo)
