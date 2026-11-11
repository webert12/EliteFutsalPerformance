from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database import get_db
from app.security.token import usuario_atual
from app.models.usuario import Usuario
from app.models.atleta import Atleta, RegistroDiario
from app.models.treino import Equipe, VinculoEquipe, Presenca, Treino
from app.models.acesso import Consentimento
from app.models.acompanhamento_v18 import PlanoDiaV18, ConversaV18

router=APIRouter(prefix='/api/v18',tags=['V18 Acompanhamento'])

class PlanoInput(BaseModel):
    dia:date
    tipo:str=Field(pattern='^(comum|treino|jogo)$')
    horario_atividade:str|None=Field(default=None,pattern=r'^([01]\d|2[0-3]):[0-5]\d$')
    escola_inicio:str|None=Field(default=None,pattern=r'^([01]\d|2[0-3]):[0-5]\d$')
    escola_fim:str|None=Field(default=None,pattern=r'^([01]\d|2[0-3]):[0-5]\d$')
    observacao:str|None=Field(default=None,max_length=400)
class MensagemInput(BaseModel):
    equipe_id:int=Field(gt=0)
    atleta_id:int|None=None
    mensagem:str=Field(min_length=2,max_length=1200)

def atleta_atual(db,u):
    if u.tipo_usuario!='atleta':raise HTTPException(403,'Somente atletas')
    a=db.query(Atleta).filter_by(usuario_id=u.id).first()
    if not a:raise HTTPException(404,'Perfil do atleta não encontrado')
    c=db.query(Consentimento).filter(Consentimento.atleta_id==a.id,Consentimento.aceito_em.is_not(None),Consentimento.revogado_em.is_(None)).first()
    if not c:raise HTTPException(403,'Autorização do responsável necessária')
    return a

def vinculo(db,eid,aid):
    e=db.get(Equipe,eid)
    ok=bool(db.query(VinculoEquipe).join(Consentimento,Consentimento.atleta_id==VinculoEquipe.atleta_id).filter(VinculoEquipe.equipe_id==eid,VinculoEquipe.atleta_id==aid,Consentimento.aceito_em.is_not(None),Consentimento.revogado_em.is_(None)).first())
    if not e or not ok:raise HTTPException(403,'Equipe ou vínculo não autorizado')
    return e

def hh(s):
    return int(s[:2])*60+int(s[3:])
def clock(minutes):
    minutes=max(0,min(1439,minutes))
    return f'{minutes//60:02d}:{minutes%60:02d}'
def montar(p):
    # Conteúdo geral educativo: não prescreve porções, energia, suplementos ou cargas.
    itens=[{'hora':'07:00','titulo':'Café da manhã','texto':'Escolha alimentos habituais que incluam fontes de energia e nutrientes, como pão ou aveia, fruta e uma fonte de proteína.'},
      {'hora':'10:00','titulo':'Lanche','texto':'Se houver fome, leve uma opção prática, como fruta ou sanduíche, respeitando sua rotina escolar.'},
      {'hora':'12:30','titulo':'Almoço','texto':'Uma refeição variada pode combinar arroz, feijão, legumes ou verduras e uma fonte de proteína.'},
      {'hora':'20:00','titulo':'Jantar e recuperação','texto':'Faça uma refeição regular, hidrate-se conforme sede e condições do treino, e reserve tempo para relaxar.'},
      {'hora':'21:30','titulo':'Preparar o sono','texto':'Diminua telas e organize um horário de descanso consistente. Adolescentes geralmente precisam de 8 a 10 horas de sono.'}]
    if p.tipo!='comum' and p.horario_atividade:
        t=hh(p.horario_atividade)
        itens.extend([
          {'hora':clock(t-120),'titulo':'Antes do '+('jogo' if p.tipo=='jogo' else 'treino'),'texto':'Considere um lanche familiar e bem tolerado, com alimentos ricos em carboidratos. Evite experimentar alimentos novos antes da atividade.'},
          {'hora':clock(t-30),'titulo':'Preparação','texto':'Confira uniforme, material e orientações do treinador. Beba água conforme sede, calor e duração da atividade.'},
          {'hora':clock(t+90),'titulo':'Depois da atividade','texto':'Retome a hidratação e faça uma refeição ou lanche habitual com carboidratos e proteínas. Se houver dor ou mal-estar, avise um adulto.'}])
    else:
        itens.append({'hora':'16:00','titulo':'Movimento e lazer','texto':'Reserve tempo para brincar, caminhar ou atividades leves de que você goste, sem obrigação de treino intenso.'})
    if p.escola_inicio and p.escola_fim:
        itens.append({'hora':p.escola_inicio,'titulo':'Escola','texto':'Leve água e, se necessário, um lanche acessível. Organize refeições em torno do período escolar.'})
    return sorted(itens,key=lambda x:x['hora'])
def plano_dict(p):
    return {'id':p.id,'dia':p.dia.isoformat(),'tipo':p.tipo,'horario_atividade':p.horario_atividade,'escola_inicio':p.escola_inicio,'escola_fim':p.escola_fim,'observacao':p.observacao,'agenda':montar(p),'aviso':'Orientações educativas gerais, não são dieta ou prescrição individual. Consulte nutricionista habilitado para necessidades específicas.'}

@router.post('/meu-dia')
def salvar(d:PlanoInput,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    a=atleta_atual(db,u)
    if abs((d.dia-date.today()).days)>31:raise HTTPException(422,'Escolha uma data próxima')
    if d.tipo!='comum' and not d.horario_atividade:raise HTTPException(422,'Informe o horário do treino ou jogo')
    if d.escola_inicio and d.escola_fim and hh(d.escola_fim)<=hh(d.escola_inicio):raise HTTPException(422,'Confira o horário escolar')
    p=db.query(PlanoDiaV18).filter_by(atleta_id=a.id,dia=d.dia).first()
    if not p:p=PlanoDiaV18(atleta_id=a.id,dia=d.dia);db.add(p)
    for key in ('tipo','horario_atividade','escola_inicio','escola_fim','observacao'):setattr(p,key,getattr(d,key))
    db.commit();db.refresh(p)
    return plano_dict(p)

@router.get('/meu-dia')
def meu_dia(u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    a=atleta_atual(db,u)
    ps=db.query(PlanoDiaV18).filter_by(atleta_id=a.id).order_by(PlanoDiaV18.dia.desc()).limit(14).all()
    return [plano_dict(p) for p in ps]

@router.get('/minhas-equipes')
def minhas_equipes(u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    a=atleta_atual(db,u)
    rows=db.query(Equipe).join(VinculoEquipe,VinculoEquipe.equipe_id==Equipe.id).filter(VinculoEquipe.atleta_id==a.id).all()
    return [{'id':e.id,'nome':e.nome} for e in rows]

@router.get('/equipe/{equipe_id}/atletas')
def equipe_atletas(equipe_id:int,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    e=db.get(Equipe,equipe_id)
    if u.tipo_usuario!='treinador' or not e or e.treinador_id!=u.id:raise HTTPException(403,'Equipe não autorizada')
    rows=db.query(Atleta,Usuario).join(VinculoEquipe,VinculoEquipe.atleta_id==Atleta.id).join(Usuario,Usuario.id==Atleta.usuario_id).join(Consentimento,Consentimento.atleta_id==Atleta.id).filter(VinculoEquipe.equipe_id==equipe_id,Consentimento.aceito_em.is_not(None),Consentimento.revogado_em.is_(None)).order_by(Usuario.nome).all()
    return [{'id':a.id,'nome':person.nome} for a,person in rows]

@router.get('/atleta/{atleta_id}/resumo')
def resumo(atleta_id:int,equipe_id:int,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    if u.tipo_usuario!='treinador':raise HTTPException(403,'Somente treinador')
    e=vinculo(db,equipe_id,atleta_id)
    if e.treinador_id!=u.id:raise HTTPException(403,'Equipe não autorizada')
    inicio=date.today()-timedelta(days=29)
    ps=db.query(PlanoDiaV18).filter(PlanoDiaV18.atleta_id==atleta_id,PlanoDiaV18.dia>=inicio).order_by(PlanoDiaV18.dia.desc()).all()
    ds=db.query(RegistroDiario).filter(RegistroDiario.atleta_id==atleta_id,RegistroDiario.dia>=inicio).order_by(RegistroDiario.dia.desc()).limit(30).all()
    return {'planos':[{'dia':p.dia.isoformat(),'tipo':p.tipo} for p in ps],'registros':[{'dia':r.dia.isoformat(),'sono':r.sono_horas,'agua_ml':r.agua_ml,'bem_estar':r.bem_estar_0_10,'dor':r.dor_ou_lesao} for r in ds],'observacao':'Dados de acompanhamento, não diagnóstico. Converse com o atleta e responsáveis quando necessário.'}

@router.post('/mensagens',status_code=201)
def enviar(d:MensagemInput,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    if u.tipo_usuario=='atleta':
        a=atleta_atual(db,u)
        if d.atleta_id is not None and d.atleta_id!=a.id:raise HTTPException(403,'Atleta não autorizado')
        aid=a.id;e=vinculo(db,d.equipe_id,aid)
    elif u.tipo_usuario=='treinador':
        if not d.atleta_id:raise HTTPException(422,'Selecione o atleta')
        aid=d.atleta_id;e=vinculo(db,d.equipe_id,aid)
        if e.treinador_id!=u.id:raise HTTPException(403,'Equipe não autorizada')
    else:raise HTTPException(403,'Acesso restrito')
    m=ConversaV18(equipe_id=e.id,atleta_id=aid,treinador_id=e.treinador_id,autor_id=u.id,mensagem=d.mensagem.strip())
    if not m.mensagem:raise HTTPException(422,'Mensagem vazia')
    db.add(m);db.commit();db.refresh(m)
    return {'id':m.id,'criado_em':m.criado_em.isoformat()}

@router.get('/mensagens')
def mensagens(equipe_id:int,atleta_id:int|None=None,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    if u.tipo_usuario=='atleta':
        a=atleta_atual(db,u)
        if atleta_id is not None and atleta_id!=a.id:raise HTTPException(403,'Atleta não autorizado')
        aid=a.id;e=vinculo(db,equipe_id,aid)
    elif u.tipo_usuario=='treinador':
        if not atleta_id:raise HTTPException(422,'Selecione o atleta')
        aid=atleta_id;e=vinculo(db,equipe_id,aid)
        if e.treinador_id!=u.id:raise HTTPException(403,'Equipe não autorizada')
    else:raise HTTPException(403,'Acesso restrito')
    rows=db.query(ConversaV18).filter_by(equipe_id=equipe_id,atleta_id=aid,treinador_id=e.treinador_id).order_by(ConversaV18.id.desc()).limit(100).all()
    return [{'id':m.id,'autor':'Você' if m.autor_id==u.id else ('Treinador' if m.autor_id==e.treinador_id else 'Atleta'),'mensagem':m.mensagem,'criado_em':m.criado_em.isoformat()} for m in reversed(rows)]
