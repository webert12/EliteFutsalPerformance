"""V10: programação da equipe/indivíduo e orientação educativa condicionada ao check-in."""
from datetime import date,timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario import Usuario
from app.models.treino import Equipe, VinculoEquipe
from app.models.atleta import RegistroDiario
from app.models.habitos import HabitosDia
from app.models.performance_v9 import CheckinV9
from app.models.rotina import Tarefa
from app.models.planejamento_v10 import EventoV10, DistribuicaoV10
from app.routes.rotina import atleta_proprio, verificar_treinador
from app.routes.acesso import exigir_consentimento
from app.security.token import usuario_atual

router=APIRouter(prefix='/api/v10',tags=['V10 — Planejamento'])
TIPOS={'treino','preparacao','alimentacao','recuperacao','orientacao','jogo'}
class PlanoEntrada(BaseModel):
    equipe_id:int
    atleta_id:int|None=None
    dia:date
    tipo:str
    titulo:str=Field(min_length=3,max_length=120)
    detalhes:str=Field(min_length=3,max_length=800)

def serializar(p):
    return {'id':p.id,'equipe_id':p.equipe_id,'dia':p.dia.isoformat(),'tipo':p.tipo,'titulo':p.titulo,'detalhes':p.detalhes}

def equipe_do_treinador(db,u,equipe_id):
    if u.tipo_usuario!='treinador':raise HTTPException(403,'Somente treinadores')
    e=db.get(Equipe,equipe_id)
    if not e or e.treinador_id!=u.id:raise HTTPException(403,'Equipe não autorizada')
    return e

@router.post('/planejar',status_code=201)
def planejar(d:PlanoEntrada,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    equipe_do_treinador(db,u,d.equipe_id)
    if d.tipo not in TIPOS:raise HTTPException(422,'Tipo inválido')
    if not date.today()-timedelta(days=7)<=d.dia<=date.today()+timedelta(days=90):raise HTTPException(422,'Data fora do período permitido')
    ids=[a for (a,) in db.query(VinculoEquipe.atleta_id).filter_by(equipe_id=d.equipe_id).all()]
    if d.atleta_id is not None:
        if d.atleta_id not in ids:raise HTTPException(403,'Atleta fora da equipe')
        ids=[d.atleta_id]
    if not ids:raise HTTPException(422,'Nenhum atleta vinculado')
    # Não incluir atletas sem autorização válida; alvo individual não autorizado é rejeitado.
    autorizados=[]
    for aid in ids:
        try:exigir_consentimento(db,aid);autorizados.append(aid)
        except HTTPException:
            if d.atleta_id is not None:raise
    ids=autorizados
    if not ids:raise HTTPException(422,'Nenhum atleta com autorização válida nesta seleção')
    p=EventoV10(equipe_id=d.equipe_id,treinador_id=u.id,dia=d.dia,tipo=d.tipo,titulo=d.titulo,detalhes=d.detalhes)
    db.add(p);db.flush()
    for aid in ids:
        db.add(DistribuicaoV10(evento_id=p.id,atleta_id=aid))
        db.add(Tarefa(treinador_id=u.id,atleta_id=aid,dia=d.dia,titulo=d.titulo,descricao=f'[{d.tipo.upper()}] {d.detalhes}'))
    db.commit();db.refresh(p)
    return {**serializar(p),'destinatarios':len(ids)}

@router.get('/equipes/{equipe_id}/agenda')
def agenda(equipe_id:int,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    equipe_do_treinador(db,u,equipe_id)
    hoje=date.today()
    rows=db.query(EventoV10).filter(EventoV10.equipe_id==equipe_id,EventoV10.dia>=hoje-timedelta(days=7),EventoV10.dia<=hoje+timedelta(days=90)).order_by(EventoV10.dia,EventoV10.id).limit(200).all()
    return [serializar(x) for x in rows]

@router.get('/meu-dia')
def meu_dia(u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    a=atleta_proprio(db,u)
    hoje=date.today()
    check=db.query(CheckinV9).filter_by(atleta_id=a.id,dia=hoje).first()
    hab=db.query(HabitosDia).filter_by(atleta_id=a.id,dia=hoje).first()
    registro=db.query(RegistroDiario).filter_by(atleta_id=a.id,dia=hoje).order_by(RegistroDiario.id.desc()).first()
    tarefas=db.query(Tarefa).filter_by(atleta_id=a.id,dia=hoje).order_by(Tarefa.id).all()
    sugestoes=[{'categoria':'alimentacao','titulo':'Refeições regulares','texto':'Faça refeições variadas e suficientes ao longo do dia, respeitando sua fome e a rotina familiar. Não substitui plano de nutricionista.'},{'categoria':'hidratacao','titulo':'Água ao longo do dia','texto':'Mantenha água acessível e beba regularmente. Não existe uma quantidade única adequada a todos.'},{'categoria':'sono','titulo':'Sono e recuperação','texto':'Reserve tempo para dormir e descansar; procure manter horários consistentes.'}]
    alerta=bool((check and (check.dor or check.cansaco>=4 or check.sono=='mal')) or (registro and registro.dor_ou_lesao))
    if alerta:sugestoes.insert(0,{'categoria':'atencao','titulo':'Converse com seu treinador e responsável','texto':'Você informou dor, cansaço elevado ou sono ruim. Não aumente a carga por conta própria; avise um adulto responsável. Se houver dor, interrompa atividades que a provoquem.'})
    return {'dia':hoje.isoformat(),'checkin_preenchido':bool(check),'habitos_preenchidos':bool(hab),'registro_preenchido':bool(registro),'alerta_para_conversa':alerta,'sugestoes':sugestoes,'tarefas':[{'id':t.id,'titulo':t.titulo,'descricao':t.descricao,'concluida':bool(t.concluida_em)} for t in tarefas]}

@router.get('/equipes/{equipe_id}/resumo')
def resumo(equipe_id:int,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    equipe_do_treinador(db,u,equipe_id)
    ids=[a for (a,) in db.query(VinculoEquipe.atleta_id).filter_by(equipe_id=equipe_id).all()]
    # Resumo agregado: não expõe observações clínicas.
    hoje=date.today()
    total=0;checkins=0;alertas=0
    for aid in ids:
        try:exigir_consentimento(db,aid)
        except HTTPException:continue
        total+=1
        c=db.query(CheckinV9).filter_by(atleta_id=aid,dia=hoje).first()
        if c:
            checkins+=1
            if c.dor or c.cansaco>=4 or c.sono=='mal':alertas+=1
    return {'atletas_autorizados':total,'checkins_hoje':checkins,'checkins_que_pedem_conversa':alertas}
