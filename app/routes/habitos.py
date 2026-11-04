"""V7: hábitos educativos e rotina. Sem dietas, prescrição hídrica ou carga automática."""
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario import Usuario
from app.models.atleta import Atleta, RegistroDiario
from app.models.habitos import HabitosDia
from app.models.rotina import Tarefa
from app.routes.rotina import atleta_proprio, verificar_treinador
from app.security.token import usuario_atual

router = APIRouter(prefix='/api/v7', tags=['V7 — Hábitos e planejamento'])

CATALOGO = [
    {'codigo':'passe','titulo':'Passe e domínio','descricao':'Atividade técnica de passe e domínio. Realize apenas conforme orientação e supervisão do treinador.'},
    {'codigo':'conducao','titulo':'Condução de bola','descricao':'Exercício técnico de condução. Espaço, duração e intensidade definidos pelo treinador.'},
    {'codigo':'mobilidade','titulo':'Mobilidade leve','descricao':'Movimentos leves orientados pelo treinador, sem forçar amplitude ou trabalhar com dor.'},
    {'codigo':'descanso','titulo':'Dia de recuperação','descricao':'Respeite o descanso programado pelo treinador. Não acrescente treinos por conta própria.'},
]

class HabitosEntrada(BaseModel):
    dia: date
    cafe: bool = False
    almoco: bool = False
    jantar: bool = False
    agua: bool = False
    descanso: bool = False
    observacao: str | None = Field(default=None, max_length=300)

def serializar(h):
    return {'dia':h.dia.isoformat(),'cafe':h.cafe,'almoco':h.almoco,'jantar':h.jantar,
            'agua':h.agua,'descanso':h.descanso,'observacao':h.observacao}

@router.get('/biblioteca')
def biblioteca(u:Usuario=Depends(usuario_atual)):
    if u.tipo_usuario not in ('treinador','atleta'): raise HTTPException(403,'Acesso restrito')
    return CATALOGO

@router.get('/meu-dia')
def meu_dia(u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    a=atleta_proprio(db,u)
    hoje=date.today()
    h=db.query(HabitosDia).filter_by(atleta_id=a.id,dia=hoje).first()
    r=db.query(RegistroDiario).filter_by(atleta_id=a.id,dia=hoje).order_by(RegistroDiario.id.desc()).first()
    ts=db.query(Tarefa).filter_by(atleta_id=a.id,dia=hoje).order_by(Tarefa.id).all()
    return {'dia':hoje.isoformat(),'habitos':serializar(h) if h else None,
            'sono_horas':r.sono_horas if r else None,'agua_ml':r.agua_ml if r else None,
            'tarefas':[{'id':t.id,'titulo':t.titulo,'descricao':t.descricao,'concluida':bool(t.concluida_em)} for t in ts],
            'orientacoes':['Alimente-se regularmente e com variedade; não pule refeições para melhorar desempenho.',
                           'Tenha água disponível e beba regularmente; necessidades individuais variam.',
                           'Respeite seu sono e descanso. Em caso de dor, avise um responsável e seu treinador.',
                           'Não realize exercícios adicionais sem orientação do treinador.']}

@router.put('/meus-habitos')
def salvar_habitos(d:HabitosEntrada,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    a=atleta_proprio(db,u)
    if not date.today()-timedelta(days=7)<=d.dia<=date.today():
        raise HTTPException(422,'Registre apenas hoje ou os últimos 7 dias')
    h=db.query(HabitosDia).filter_by(atleta_id=a.id,dia=d.dia).first()
    if h is None:
        h=HabitosDia(atleta_id=a.id,dia=d.dia)
        db.add(h)
    for campo in ('cafe','almoco','jantar','agua','descanso','observacao'):
        setattr(h,campo,getattr(d,campo))
    db.commit();db.refresh(h)
    return serializar(h)

@router.get('/atletas/{atleta_id}/semana')
def semana(atleta_id:int,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    verificar_treinador(db,u,atleta_id)
    inicio=date.today()-timedelta(days=6)
    hs=db.query(HabitosDia).filter(HabitosDia.atleta_id==atleta_id,HabitosDia.dia>=inicio).order_by(HabitosDia.dia.desc()).all()
    return [serializar(h) for h in hs]
