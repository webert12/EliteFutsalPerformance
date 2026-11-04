"""V9: registros e avaliações por perfil; conteúdo educativo não é prescrição."""
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario import Usuario
from app.models.atleta import RegistroDiario
from app.models.habitos import HabitosDia
from app.models.rotina import Tarefa
from app.models.performance_v9 import CheckinV9, AvaliacaoV9
from app.routes.rotina import atleta_proprio, verificar_treinador
from app.security.token import usuario_atual

router=APIRouter(prefix='/api/v9',tags=['V9 — Performance'])
EXERCICIOS=[
 {'id':'passe','nome':'Passe e recepção','objetivo':'Controle e precisão','material':'Bola e parede ou parceiro','instrucoes':'Treinador define séries, duração e local seguro. Priorize técnica, não velocidade.','video_url':None},
 {'id':'conducao','nome':'Condução de bola','objetivo':'Domínio próximo','material':'Bola e cones','instrucoes':'Conduza a bola em percurso definido pelo treinador, sem aumentar a carga por conta própria.','video_url':None},
 {'id':'finalizacao','nome':'Finalização','objetivo':'Precisão e tomada de decisão','material':'Bola e gol','instrucoes':'Realize somente em espaço apropriado e com orientação do treinador.','video_url':None},
 {'id':'mobilidade','nome':'Mobilidade orientada','objetivo':'Qualidade do movimento','material':'Espaço livre','instrucoes':'Movimentos confortáveis definidos pelo treinador; interrompa se houver dor.','video_url':None},
 {'id':'recuperacao','nome':'Recuperação e descanso','objetivo':'Respeitar a recuperação','material':'Nenhum','instrucoes':'Siga o descanso planejado. Não substitua por treinamento adicional.','video_url':None}
]
ORIENTACOES={
 'alimentacao':['Faça refeições regulares e variadas, respeitando fome, saciedade e cultura alimentar.','Arroz, feijão, frutas, verduras e fontes de proteína podem compor refeições equilibradas.','Planos individuais e suplementos dependem de nutricionista habilitado.'],
 'hidratacao':['Tenha água disponível durante o dia e as atividades.','Necessidades de líquidos variam com calor, duração, intensidade e características individuais; evite metas universais.'],
 'sono':['Organize uma rotina de sono consistente e reserve tempo para descanso.','Avise seu responsável e treinador se cansaço, dor ou dificuldades persistirem.']
}
class CheckinEntrada(BaseModel):
 dia:date
 sono:str
 cansaco:int=Field(ge=1,le=5)
 dor:bool=False
 observacao:str|None=Field(default=None,max_length=300)
class AvaliacaoEntrada(BaseModel):
 atleta_id:int
 dia:date
 fundamento:str
 nota:int=Field(ge=1,le=5)
 observacao:str|None=Field(default=None,max_length=300)
FUNDAMENTOS={'passe','dominio','finalizacao','posicionamento','decisao','participacao'}
def checkin_json(c):return {'dia':c.dia.isoformat(),'sono':c.sono,'cansaco':c.cansaco,'dor':c.dor,'observacao':c.observacao}
def avaliacao_json(a):return {'id':a.id,'dia':a.dia.isoformat(),'fundamento':a.fundamento,'nota':a.nota,'observacao':a.observacao}
@router.get('/biblioteca')
def biblioteca(u:Usuario=Depends(usuario_atual)):
 if u.tipo_usuario not in ('atleta','treinador'):raise HTTPException(403,'Acesso restrito')
 return EXERCICIOS
@router.get('/orientacoes')
def orientacoes(u:Usuario=Depends(usuario_atual)):
 if u.tipo_usuario not in ('atleta','treinador'):raise HTTPException(403,'Acesso restrito')
 return ORIENTACOES
@router.put('/meu-checkin')
def salvar_checkin(d:CheckinEntrada,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
 a=atleta_proprio(db,u)
 if d.sono not in {'bem','regular','mal'}:raise HTTPException(422,'Sono inválido')
 if not date.today()-timedelta(days=7)<=d.dia<=date.today():raise HTTPException(422,'Data fora dos últimos 7 dias')
 c=db.query(CheckinV9).filter_by(atleta_id=a.id,dia=d.dia).first()
 if c is None:c=CheckinV9(atleta_id=a.id,dia=d.dia);db.add(c)
 for k,v in d.model_dump().items():setattr(c,k,v)
 db.commit();return checkin_json(c)
@router.get('/meus-checkins')
def meus_checkins(u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
 a=atleta_proprio(db,u)
 return [checkin_json(c) for c in db.query(CheckinV9).filter_by(atleta_id=a.id).order_by(CheckinV9.dia.desc()).limit(30)]
@router.get('/atletas/{atleta_id}/checkins')
def checkins_treinador(atleta_id:int,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
 verificar_treinador(db,u,atleta_id)
 return [checkin_json(c) for c in db.query(CheckinV9).filter_by(atleta_id=atleta_id).order_by(CheckinV9.dia.desc()).limit(30)]
@router.post('/avaliacoes',status_code=201)
def criar_avaliacao(d:AvaliacaoEntrada,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
 verificar_treinador(db,u,d.atleta_id)
 if d.fundamento not in FUNDAMENTOS:raise HTTPException(422,'Fundamento inválido')
 if d.dia>date.today() or d.dia<date.today()-timedelta(days=365):raise HTTPException(422,'Data inválida')
 a=AvaliacaoV9(treinador_id=u.id,**d.model_dump());db.add(a);db.commit();db.refresh(a);return avaliacao_json(a)
@router.get('/minhas-avaliacoes')
def minhas_avaliacoes(u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
 a=atleta_proprio(db,u)
 return [avaliacao_json(x) for x in db.query(AvaliacaoV9).filter_by(atleta_id=a.id).order_by(AvaliacaoV9.dia.desc(),AvaliacaoV9.id.desc()).limit(60)]
@router.get('/atletas/{atleta_id}/relatorio')
def relatorio(atleta_id:int,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
 verificar_treinador(db,u,atleta_id)
 inicio=date.today()-timedelta(days=6)
 ts=db.query(Tarefa).filter(Tarefa.atleta_id==atleta_id,Tarefa.dia>=inicio,Tarefa.dia<=date.today()).all()
 hs=db.query(HabitosDia).filter(HabitosDia.atleta_id==atleta_id,HabitosDia.dia>=inicio).all()
 cs=db.query(CheckinV9).filter(CheckinV9.atleta_id==atleta_id,CheckinV9.dia>=inicio).order_by(CheckinV9.dia.desc()).all()
 rs=db.query(RegistroDiario).filter(RegistroDiario.atleta_id==atleta_id,RegistroDiario.dia>=inicio).order_by(RegistroDiario.dia.desc()).all()
 av=db.query(AvaliacaoV9).filter_by(atleta_id=atleta_id).order_by(AvaliacaoV9.dia.desc(),AvaliacaoV9.id.desc()).limit(30).all()
 return {'periodo_dias':7,'tarefas_total':len(ts),'tarefas_concluidas':sum(bool(t.concluida_em) for t in ts), 'dias_habitos':len(hs),'checkins':[checkin_json(c) for c in cs], 'registros':[{'dia':r.dia.isoformat(),'sono_horas':r.sono_horas,'bem_estar':r.bem_estar_0_10,'dor':r.dor_ou_lesao} for r in rs], 'avaliacoes':[avaliacao_json(x) for x in av]}
