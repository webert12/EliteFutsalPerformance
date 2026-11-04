"""V6: consentimento do responsável e solicitação de entrada em equipe.
O termo exige confirmação fora do aplicativo: código NÃO comprova identidade.
"""
from datetime import datetime, timezone, timedelta, date
import secrets
import hashlib
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models.usuario import Usuario
from app.models.atleta import Atleta, RegistroDiario
from app.models.treino import Equipe, VinculoEquipe
from app.models.rotina import Tarefa
from app.models.acesso import Consentimento, ConviteEquipe, SolicitacaoEquipe
from app.security.token import usuario_atual

router = APIRouter(prefix='/api/v6', tags=['V6 — Proteção e Meu Dia'])
TERMO = 'v6-2026-11'

def agora(): return datetime.now(timezone.utc)
def digest(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()
def consciente(db, aid):
    c=db.query(Consentimento).filter_by(atleta_id=aid).first()
    return bool(c and c.aceito_em and not c.revogado_em)
def exigir_consentimento(db, aid):
    if not consciente(db,aid): raise HTTPException(403,'Aguardando autorização do responsável')
def proprio(db,u):
    if u.tipo_usuario!='atleta': raise HTTPException(403,'Somente atletas')
    a=db.query(Atleta).filter_by(usuario_id=u.id).first()
    if not a: raise HTTPException(404,'Cadastre sua ficha esportiva primeiro')
    return a

def treinador_equipe(db,u,eid):
    if u.tipo_usuario!='treinador':raise HTTPException(403,'Somente treinadores')
    e=db.get(Equipe,eid)
    if not e or e.treinador_id!=u.id:raise HTTPException(404,'Equipe não encontrada')
    return e

class Aceite(BaseModel):
    codigo: str = Field(min_length=24,max_length=128)
    nome: str = Field(min_length=3,max_length=120)
    vinculo: str = Field(pattern='^(mae|pai|responsavel_legal)$')
    concordo: bool
class Entrada(BaseModel):
    codigo: str = Field(min_length=12,max_length=128)

@router.get('/meu-acesso')
def meu_acesso(u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    a=proprio(db,u)
    s=db.query(SolicitacaoEquipe).filter_by(atleta_id=a.id).order_by(SolicitacaoEquipe.id.desc()).limit(10).all()
    return {'consentimento':consciente(db,a.id),'solicitacoes':[{'id':x.id,'equipe_id':x.equipe_id,'status':x.status} for x in s]}

@router.post('/codigo-responsavel')
def gerar_codigo(u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    a=proprio(db,u)
    if consciente(db,a.id):raise HTTPException(409,'Autorização já registrada')
    c=db.query(Consentimento).filter_by(atleta_id=a.id).first()
    if not c: c=Consentimento(atleta_id=a.id);db.add(c)
    raw=secrets.token_urlsafe(32)
    c.token_hash=digest(raw);c.token_expira_em=agora()+timedelta(hours=48)
    db.commit()
    return {'codigo':raw,'expira_em':c.token_expira_em,'orientacao':'Entregue diretamente ao responsável legal. O código não verifica identidade.'}

@router.post('/responsavel/aceitar')
def aceitar(d:Aceite,db:Session=Depends(get_db)):
    if not d.concordo:raise HTTPException(422,'É necessário concordar expressamente')
    c=db.query(Consentimento).filter_by(token_hash=digest(d.codigo)).first()
    if not c or not c.token_expira_em or c.token_expira_em.replace(tzinfo=timezone.utc)<agora():
        raise HTTPException(400,'Código inválido ou expirado')
    if c.aceito_em and not c.revogado_em:raise HTTPException(409,'Autorização já registrada')
    c.responsavel_nome=d.nome.strip();c.responsavel_vinculo=d.vinculo
    c.aceito_em=agora();c.revogado_em=None;c.versao_termo=TERMO
    c.token_hash=None;c.token_expira_em=None
    codigo_revogacao=secrets.token_urlsafe(32)
    c.revogacao_hash=digest(codigo_revogacao)
    db.commit()
    return {'mensagem':'Declaração registrada. Identidade ainda requer verificação fora do aplicativo.', 'codigo_revogacao':codigo_revogacao}

@router.post('/responsavel/revogar')
def revogar(d:Entrada,db:Session=Depends(get_db)):
    c=db.query(Consentimento).filter_by(revogacao_hash=digest(d.codigo)).first()
    if not c:raise HTTPException(400,'Código inválido')
    c.revogado_em=agora();c.revogacao_hash=None
    db.commit()
    return {'mensagem':'Autorização revogada; os acessos aos registros e tarefas foram bloqueados.'}

@router.post('/equipes/{equipe_id}/convites')
def criar_convite(equipe_id:int,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    treinador_equipe(db,u,equipe_id)
    raw=secrets.token_urlsafe(24)
    c=ConviteEquipe(equipe_id=equipe_id,codigo_hash=digest(raw),expira_em=agora()+timedelta(days=3))
    db.add(c);db.commit()
    return {'codigo':raw,'expira_em':c.expira_em,'aviso':'Compartilhe individualmente, fora de grupos públicos. Uso único.'}

@router.post('/solicitar-equipe')
def solicitar(d:Entrada,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    a=proprio(db,u);exigir_consentimento(db,a.id)
    c=db.query(ConviteEquipe).filter_by(codigo_hash=digest(d.codigo)).first()
    if not c or c.usado_em or c.expira_em.replace(tzinfo=timezone.utc)<agora():raise HTTPException(400,'Convite inválido, expirado ou utilizado')
    if db.query(VinculoEquipe).filter_by(equipe_id=c.equipe_id,atleta_id=a.id).first():raise HTTPException(409,'Você já participa da equipe')
    s=db.query(SolicitacaoEquipe).filter_by(equipe_id=c.equipe_id,atleta_id=a.id).first()
    if s and s.status=='pendente':raise HTTPException(409,'Solicitação já enviada')
    if s:s.status='pendente'
    else:db.add(SolicitacaoEquipe(equipe_id=c.equipe_id,atleta_id=a.id))
    c.usado_em=agora();db.commit()
    return {'status':'pendente','equipe_id':c.equipe_id}

@router.get('/equipes/{equipe_id}/solicitacoes')
def solicitacoes(equipe_id:int,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    treinador_equipe(db,u,equipe_id)
    rows=(db.query(SolicitacaoEquipe,Usuario).join(Atleta,Atleta.id==SolicitacaoEquipe.atleta_id)
          .join(Usuario,Usuario.id==Atleta.usuario_id)
          .filter(SolicitacaoEquipe.equipe_id==equipe_id,SolicitacaoEquipe.status=='pendente').all())
    return [{'id':s.id,'atleta_id':s.atleta_id,'nome':p.nome,'consentimento':consciente(db,s.atleta_id)} for s,p in rows]

@router.post('/solicitacoes/{sid}/aprovar')
def aprovar(sid:int,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    s=db.get(SolicitacaoEquipe,sid)
    if not s:raise HTTPException(404,'Solicitação não encontrada')
    treinador_equipe(db,u,s.equipe_id)
    if s.status!='pendente':raise HTTPException(409,'Solicitação já analisada')
    exigir_consentimento(db,s.atleta_id)
    if not db.query(VinculoEquipe).filter_by(equipe_id=s.equipe_id,atleta_id=s.atleta_id).first():
        db.add(VinculoEquipe(equipe_id=s.equipe_id,atleta_id=s.atleta_id))
    s.status='aprovado'
    try:db.commit()
    except IntegrityError:db.rollback();raise HTTPException(409,'Vínculo já existente')
    return {'status':'aprovado'}

@router.post('/solicitacoes/{sid}/recusar')
def recusar(sid:int,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    s=db.get(SolicitacaoEquipe,sid)
    if not s:raise HTTPException(404,'Solicitação não encontrada')
    treinador_equipe(db,u,s.equipe_id)
    if s.status!='pendente':raise HTTPException(409,'Solicitação já analisada')
    s.status='recusado';db.commit();return {'status':'recusado'}

@router.get('/meu-dia')
def meu_dia(u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    a=proprio(db,u);exigir_consentimento(db,a.id)
    hoje=date.today()
    registro=db.query(RegistroDiario).filter_by(atleta_id=a.id,dia=hoje).order_by(RegistroDiario.id.desc()).first()
    tarefas=db.query(Tarefa).filter_by(atleta_id=a.id,dia=hoje).order_by(Tarefa.id).all()
    return {'data':hoje.isoformat(),'registro_feito':bool(registro),
            'tarefas':[{'id':t.id,'titulo':t.titulo,'descricao':t.descricao,'concluida':bool(t.concluida_em)} for t in tarefas],
            'orientacoes':['Registre como foi seu dia, mesmo sem treino na quadra.',
                            'Siga apenas as atividades orientadas pelo seu treinador.',
                            'Em caso de dor ou mal-estar, avise seu responsável e treinador.']}
