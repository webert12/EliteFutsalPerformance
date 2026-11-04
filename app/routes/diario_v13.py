"""V13: diário educativo. Sem prescrições nutricionais ou físicas automáticas."""
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario import Usuario
from app.models.diario_v13 import DiarioV13
from app.routes.rotina import atleta_proprio, verificar_treinador
from app.security.token import usuario_atual

router = APIRouter(prefix='/api/v13', tags=['V13 — Diário e histórico'])
BOOLS = ('lanche_manha','lanche_tarde','refeicao_pos_treino','agua_disponivel','pausas_agua','rotina_escolar','descanso_planejado')

class DiarioEntrada(BaseModel):
    dia: date
    lanche_manha: bool = False
    lanche_tarde: bool = False
    refeicao_pos_treino: bool = False
    agua_disponivel: bool = False
    pausas_agua: bool = False
    rotina_escolar: bool = False
    descanso_planejado: bool = False
    disposicao: str | None = None
    recuperacao: str | None = None
    observacao: str | None = Field(default=None, max_length=240)

def validar(d):
    if d.disposicao not in (None,'boa','regular','baixa') or d.recuperacao not in (None,'boa','regular','ruim'):
        raise HTTPException(422, 'Seleção de disposição ou recuperação inválida')
    if not date.today()-timedelta(days=7) <= d.dia <= date.today():
        raise HTTPException(422,'Registre somente hoje ou os últimos sete dias')

def item(x):
    return {'dia':x.dia.isoformat(),**{k:getattr(x,k) for k in BOOLS},
            'disposicao':x.disposicao,'recuperacao':x.recuperacao,'observacao':x.observacao}

@router.put('/meu-diario')
def salvar(d:DiarioEntrada, u:Usuario=Depends(usuario_atual), db:Session=Depends(get_db)):
    a=atleta_proprio(db,u)
    validar(d)
    x=db.query(DiarioV13).filter_by(atleta_id=a.id,dia=d.dia).first()
    if x is None:
        x=DiarioV13(atleta_id=a.id,dia=d.dia)
        db.add(x)
    for k,v in d.model_dump().items():
        if k!='dia':setattr(x,k,v)
    db.commit();db.refresh(x)
    return item(x)

@router.get('/meu-historico')
def meu_historico(u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    a=atleta_proprio(db,u)
    return [item(x) for x in db.query(DiarioV13).filter(DiarioV13.atleta_id==a.id,DiarioV13.dia>=date.today()-timedelta(days=29)).order_by(DiarioV13.dia.desc()).limit(30).all()]

@router.get('/atletas/{atleta_id}/semana')
def semana(atleta_id:int,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    verificar_treinador(db,u,atleta_id)
    return [item(x) for x in db.query(DiarioV13).filter(DiarioV13.atleta_id==atleta_id,DiarioV13.dia>=date.today()-timedelta(days=6)).order_by(DiarioV13.dia.desc()).limit(7).all()]
