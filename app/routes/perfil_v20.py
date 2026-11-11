from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario import Usuario
from app.models.perfil_v20 import PerfilV20, SensacaoV20
from app.models.acesso import Consentimento
from app.models.atleta import Atleta
from app.security.token import usuario_atual

router=APIRouter(prefix='/api/v20',tags=['V20 Perfil e rotina adaptativa'])
class PerfilIn(BaseModel):
    nascimento:date
    altura_cm:int=Field(ge=110,le=230)
    peso_kg:int=Field(ge=25,le=180)
    posicao:str=Field(pattern='^(goleiro|fixo|ala|pivo|universal)$')
    condicionamento:str=Field(pattern='^(iniciante|intermediario|avancado)$')
    minutos_atividade:int=Field(ge=0,le=240)
    treinos_semanais:int=Field(ge=0,le=7)
    ocupacao:str=Field(pattern='^(estuda|trabalha|ambos|nenhum)$')
    inicio_ocupacao:str|None=Field(default=None,pattern=r'^([01]\d|2[0-3]):[0-5]\d$')
    fim_ocupacao:str|None=Field(default=None,pattern=r'^([01]\d|2[0-3]):[0-5]\d$')
class SensacaoIn(BaseModel):
    dia:date
    cansaco:int=Field(ge=0,le=10)
    dor:str=Field(pattern='^(nenhuma|leve|moderada|forte)$')
    sono:int=Field(ge=0,le=10)
    humor:int=Field(ge=0,le=10)
class RotinaIn(BaseModel):
    dia:date
    tipo:str=Field(pattern='^(comum|treino|jogo)$')
    horario:str|None=Field(default=None,pattern=r'^([01]\d|2[0-3]):[0-5]\d$')

def atleta(u):
    if u.tipo_usuario!='atleta':raise HTTPException(403,'Somente atletas')
def perfil_dict(p):
    return {k:getattr(p,k).isoformat() if k=='nascimento' else getattr(p,k) for k in ('nascimento','altura_cm','peso_kg','posicao','condicionamento','minutos_atividade','treinos_semanais','ocupacao','inicio_ocupacao','fim_ocupacao')}
def consentido(db,u):
    a=db.query(Atleta).filter_by(usuario_id=u.id).first()
    if not a:return False
    return bool(db.query(Consentimento).filter(Consentimento.atleta_id==a.id,Consentimento.aceito_em.is_not(None),Consentimento.revogado_em.is_(None)).first())
@router.get('/perfil')
def get_perfil(u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    atleta(u);p=db.query(PerfilV20).filter_by(usuario_id=u.id).first()
    return {'completo':bool(p),'perfil':perfil_dict(p) if p else None,'consentimento_registrado':consentido(db,u)}
@router.put('/perfil')
def salvar_perfil(d:PerfilIn,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    atleta(u);hoje=date.today();idade=hoje.year-d.nascimento.year-((hoje.month,hoje.day)<(d.nascimento.month,d.nascimento.day))
    if not 14<=idade<=17:raise HTTPException(422,'Este sistema atende atletas de 14 a 17 anos')
    if d.inicio_ocupacao and d.fim_ocupacao and d.inicio_ocupacao>=d.fim_ocupacao:raise HTTPException(422,'Confira o período de estudo/trabalho')
    p=db.query(PerfilV20).filter_by(usuario_id=u.id).first()
    if not p:p=PerfilV20(usuario_id=u.id);db.add(p)
    for k,v in d.model_dump().items():setattr(p,k,v)
    # Reutiliza a ficha esportiva do sistema para novos cadastros, sem criar vínculos ou consentimento automaticamente.
    ficha=db.query(Atleta).filter_by(usuario_id=u.id).first()
    if not ficha:
        ficha=Atleta(usuario_id=u.id,nascimento=d.nascimento,posicao=d.posicao,altura_cm=d.altura_cm,peso_kg=d.peso_kg)
        db.add(ficha)
    db.commit();return {'completo':True,'perfil':perfil_dict(p),'consentimento_registrado':consentido(db,u)}
@router.put('/sensacao')
def salvar_sensacao(d:SensacaoIn,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    atleta(u)
    if not db.query(PerfilV20).filter_by(usuario_id=u.id).first():raise HTTPException(409,'Complete seu perfil primeiro')
    if not consentido(db,u):raise HTTPException(403,'Autorização do responsável necessária para registrar informações de bem-estar')
    if d.dia>date.today() or d.dia<date.today()-timedelta(days=7):raise HTTPException(422,'Registre uma data recente')
    r=db.query(SensacaoV20).filter_by(usuario_id=u.id,dia=d.dia).first()
    if not r:r=SensacaoV20(usuario_id=u.id,dia=d.dia);db.add(r)
    for k,v in d.model_dump().items():setattr(r,k,v)
    db.commit();return {'ok':True}
def clock(t):return f'{max(0,min(1439,t))//60:02d}:{max(0,min(1439,t))%60:02d}'
def mins(t):return int(t[:2])*60+int(t[3:])
@router.post('/roteiro')
def roteiro(d:RotinaIn,u:Usuario=Depends(usuario_atual),db:Session=Depends(get_db)):
    atleta(u);p=db.query(PerfilV20).filter_by(usuario_id=u.id).first()
    if not p:raise HTTPException(409,'Complete seu perfil primeiro')
    if not consentido(db,u):raise HTTPException(403,'Autorização do responsável necessária para o acompanhamento')
    if d.dia<date.today()-timedelta(days=7) or d.dia>date.today()+timedelta(days=7):raise HTTPException(422,'Escolha um dia próximo')
    if d.tipo!='comum' and not d.horario:raise HTTPException(422,'Informe o horário do treino ou jogo')
    # Utiliza somente o check-in do dia anterior; sem score clínico, prescrição ou dose de alimento.
    anterior=db.query(SensacaoV20).filter_by(usuario_id=u.id,dia=d.dia-timedelta(days=1)).first()
    alerta=bool(anterior and (anterior.dor in ('moderada','forte') or anterior.cansaco>=8 or anterior.sono<=3))
    itens=[(420,'Café da manhã','Faça uma refeição habitual variada, por exemplo fruta, pão ou aveia e uma fonte de proteína.'),(600,'Lanche','Se sentir fome, escolha um lanche acessível e familiar; leve água para o período de estudos.'),(750,'Almoço','Inclua alimentos variados, como arroz, feijão, legumes e proteína, conforme disponibilidade.'),(1140,'Jantar','Faça sua refeição habitual e reserve tempo para relaxar.'),(1290,'Preparar o sono','Mantenha uma rotina de sono consistente. Adolescentes geralmente precisam de 8 a 10 horas de sono.')]
    if p.ocupacao!='nenhum' and p.inicio_ocupacao:itens.append((mins(p.inicio_ocupacao),'Escola ou trabalho','Organize transporte, água, pausas e alimentação durante esse período.'))
    if d.tipo=='comum':itens.append((960,'Movimento e lazer','Priorize escola, lazer, convivência e movimento confortável, sem treino extra obrigatório.'))
    else:
        t=mins(d.horario);label='jogo' if d.tipo=='jogo' else 'treino'
        itens.extend([(t-150,'Organizar o pré-'+label,'Considere uma refeição ou lanche familiar, de boa tolerância. Não experimente alimentos novos antes da atividade.'),(t-35,'Preparação','Confira material, uniforme e água. Siga as orientações do treinador.'),(t,label.capitalize(),'Participe conforme o planejamento do treinador e comunique qualquer desconforto.'),(t+90,'Recuperação','Retome a hidratação e faça uma refeição habitual com fontes de carboidratos e proteínas.')])
    if alerta:
        itens=[(h,t,('Não inicie esforço intenso; converse com o treinador e um responsável antes da atividade. '+msg) if t in ('Treino','Jogo') else msg) for h,t,msg in itens]
    aviso=('Seu registro anterior indica cansaço elevado, sono muito ruim ou dor relevante. Avise um responsável e o treinador. Se a dor for forte ou persistente, procure avaliação de saúde. Não há liberação automática para treinar.' if alerta else 'Orientações educativas gerais, sem prescrição de dieta, quantidade de água ou carga física.')
    return {'dia':d.dia.isoformat(),'tipo':d.tipo,'perfil_posicao':p.posicao,'ajuste_recuperacao':alerta,'aviso':aviso,'agenda':[{'hora':clock(h),'titulo':titulo,'texto':msg} for h,titulo,msg in sorted(itens,key=lambda x:x[0])],'registro_anterior':{'cansaco':anterior.cansaco,'dor':anterior.dor,'sono':anterior.sono} if anterior else None}
