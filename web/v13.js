/* REAL ITA V13: formulários separados, sem dependências externas. */
(()=>{'use strict';
const $=id=>document.getElementById(id);
const fields=[['lanche_manha','Lanche da manhã'],['lanche_tarde','Lanche da tarde'],['refeicao_pos_treino','Refeição ou lanche após atividade (quando houver)'],['agua_disponivel','Tive água disponível'],['pausas_agua','Fiz pausas para beber água'],['rotina_escolar','Organizei minha rotina escolar'],['descanso_planejado','Respeitei meu descanso programado']];
const make=(tag,txt,cls)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(txt!==undefined)n.textContent=txt;return n;};
function dateLocal(){const d=new Date();return [d.getFullYear(),String(d.getMonth()+1).padStart(2,'0'),String(d.getDate()).padStart(2,'0')].join('-');}
function build(){
 const athlete=$('athleteDaily'),coach=$('trainerRoutine');if(!athlete||!coach||$('v13Athlete'))return;
 const a=make('section',undefined,'v13-panel');a.id='v13Athlete';
 a.append(make('h3','📋 Meu diário completo · V13'),make('p','Registre sua rotina sem metas de peso ou calorias. Você pode atualizar um dia já registrado.','v13-muted'));
 const form=make('form');form.id='v13Form';
 const dateLabel=make('label','Data');const dateInput=make('input');dateInput.type='date';dateInput.id='v13Date';dateInput.required=true;dateInput.max=dateLocal();dateInput.value=dateLocal();dateLabel.append(dateInput);form.append(dateLabel);
 const checks=make('div',undefined,'v13-checks');for(const [key,label] of fields){const l=make('label');const input=make('input');input.type='checkbox';input.id='v13_'+key;l.append(input,document.createTextNode(' '+label));checks.append(l);}form.append(checks);
 for(const [id,label,options] of [['disposicao','Minha disposição',[['','Não informar'],['boa','Boa'],['regular','Regular'],['baixa','Baixa']]],['recuperacao','Como me sinto após as atividades',[['','Não informar'],['boa','Bem recuperado'],['regular','Regular'],['ruim','Preciso de descanso']]]]){const l=make('label',label),sel=make('select');sel.id='v13_'+id;options.forEach(([v,t])=>sel.add(new Option(t,v)));l.append(sel);form.append(l);}
 const obsLabel=make('label','Observação opcional (não inclua informações íntimas)');const obs=make('textarea');obs.id='v13_observacao';obs.maxLength=240;obs.rows=2;obsLabel.append(obs);form.append(obsLabel);
 const submit=make('button','Salvar meu diário');submit.type='submit';form.append(submit);a.append(form);
 const status=make('p','', 'v13-muted');status.id='v13Status';status.setAttribute('role','status');a.append(status,make('h4','Histórico dos últimos 30 dias'));
 const history=make('div',undefined,'v13-history');history.id='v13History';a.append(history);
 const refresh=make('button','Atualizar histórico');refresh.type='button';refresh.className='outline';refresh.onclick=loadMine;a.append(refresh);athlete.prepend(a);
 const c=make('section',undefined,'v13-panel');c.id='v13Coach';c.append(make('h3','📊 Acompanhamento de hábitos · V13'),make('p','Selecione um atleta na seção Atividades. Só é possível consultar atletas vinculados à sua equipe.','v13-muted'));
 const b=make('button','Consultar semana do atleta');b.type='button';b.onclick=loadCoach;c.append(b);const coachStatus=make('p','', 'v13-muted');coachStatus.id='v13CoachStatus';coachStatus.setAttribute('role','status');c.append(coachStatus);const report=make('div',undefined,'v13-history');report.id='v13CoachHistory';c.append(report);coach.prepend(c);
 form.addEventListener('submit',save);
 dateInput.addEventListener('change',()=>{const found=cache.find(x=>x.dia===dateInput.value);fill(found);});
}
let cache=[];
function fill(data){for(const [k] of fields)$('v13_'+k).checked=Boolean(data?.[k]);for(const k of ['disposicao','recuperacao','observacao'])$('v13_'+k).value=data?.[k]||'';}
function draw(list,target){target.replaceChildren();if(!list.length){target.append(make('p','Nenhum registro encontrado.','v13-muted'));return;}for(const x of list){const card=make('article',undefined,'v13-card');card.append(make('strong',x.dia.split('-').reverse().join('/')));const count=fields.filter(([k])=>x[k]).length;card.append(make('p',`${count} de ${fields.length} hábitos marcados · Disposição: ${x.disposicao||'não informada'} · Recuperação: ${x.recuperacao||'não informada'}`));if(x.observacao)card.append(make('small',x.observacao));target.append(card);}}
async function loadMine(){if(typeof role==='undefined'||role!=='atleta'||!token)return;const s=$('v13Status');s.textContent='Carregando...';try{cache=await request('/api/v13/meu-historico');draw(cache,$('v13History'));fill(cache.find(x=>x.dia===$('v13Date').value));s.textContent='Histórico atualizado.';}catch(e){s.textContent=e.message;}}
async function save(e){e.preventDefault();const s=$('v13Status');s.textContent='Salvando...';const data={dia:$('v13Date').value};for(const [k] of fields)data[k]=$('v13_'+k).checked;for(const k of ['disposicao','recuperacao','observacao'])data[k]=$('v13_'+k).value||null;try{await request('/api/v13/meu-diario',{method:'PUT',body:JSON.stringify(data)});s.textContent='Diário salvo com sucesso.';await loadMine();}catch(err){s.textContent=err.message;}}
async function loadCoach(){const s=$('v13CoachStatus'),id=$('taskAthlete')?.value;s.textContent='';if(!id){s.textContent='Selecione um atleta na seção Atividades.';return;}s.textContent='Consultando...';try{const data=await request('/api/v13/atletas/'+encodeURIComponent(id)+'/semana');draw(data,$('v13CoachHistory'));s.textContent='Registros da última semana.';}catch(e){s.textContent=e.message;}}
function start(){build();const profile=$('profile');if(profile){new MutationObserver(()=>{if(!profile.classList.contains('hidden')&&typeof role!=='undefined'&&role==='atleta')loadMine();}).observe(profile,{attributes:true,attributeFilter:['class']});}}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start);else start();
})();
