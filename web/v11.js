/* REAL ITA V11: apresentação e calendário. Usa apenas APIs já presentes na V10. */
(()=>{
'use strict';
const $11=id=>document.getElementById(id);
const originalShow=v8Show;
const originalSetup=v8Setup;
let weekShift=0;
let coachTeams=[];
let coachAgenda=[];
const dateISO=d=>[d.getFullYear(),String(d.getMonth()+1).padStart(2,'0'),String(d.getDate()).padStart(2,'0')].join('-');
const today=new Date();today.setHours(12,0,0,0);
const monday=offset=>{const d=new Date(today);d.setDate(d.getDate()-((d.getDay()+6)%7)+offset*7);return d;};
const pretty=d=>d.toLocaleDateString('pt-BR',{day:'2-digit',month:'short'});
const create=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n;};
const getRole=()=>role;
const hide=()=>{$11('v11Calendar').classList.add('hidden');};
async function getTeams(){
  const select=$11('v11CalendarTeam');const previous=select.value;
  coachTeams=await request('/api/v4/equipes');select.replaceChildren(new Option('Selecione uma equipe',''));
  coachTeams.forEach(t=>select.add(new Option(`${t.nome} · ${t.categoria}`,String(t.id))));
  if(coachTeams.some(t=>String(t.id)===previous))select.value=previous;
  else if(coachTeams.length)select.value=String(coachTeams[0].id);
}
async function getAgenda(){
  const id=$11('v11CalendarTeam').value;coachAgenda=[];
  if(id)coachAgenda=await request('/api/v10/equipes/'+encodeURIComponent(id)+'/agenda');
}
async function renderCalendar(load=false){
  if(!['treinador','atleta'].includes(getRole()))return;
  const status=$11('v11CalendarStatus'),events=$11('v11CalendarEvents'),week=$11('v11WeekDays');
  const start=monday(weekShift),end=new Date(start);end.setDate(start.getDate()+6);
  $11('v11WeekLabel').textContent=`${pretty(start)} – ${pretty(end)}`;
  $11('v11TeamWrap').classList.toggle('hidden',getRole()!=='treinador');
  $11('v11GoPlan').classList.toggle('hidden',getRole()!=='treinador');
  $11('v11CalendarHelp').textContent=getRole()==='treinador'?'Agenda real de planejamentos da equipe selecionada.':'O Meu Dia mostra suas orientações e tarefas atuais. A consulta de tarefas futuras ainda será adicionada.';
  status.textContent='';events.replaceChildren();week.replaceChildren();
  if(getRole()==='treinador' && load){
    status.textContent='Carregando agenda...';
    try{await getTeams();await getAgenda();status.textContent='';}
    catch(err){status.textContent='Não foi possível carregar a agenda: '+err.message;}
  }
  const matching=coachAgenda.filter(e=>e.dia>=dateISO(start)&&e.dia<=dateISO(end));
  for(let i=0;i<7;i++){
    const d=new Date(start);d.setDate(start.getDate()+i);const iso=dateISO(d);
    const item=create('div','v11-day'+(iso===dateISO(today)?' is-today':'')+(matching.some(e=>e.dia===iso)?' has-event':''));
    item.append(create('span','',d.toLocaleDateString('pt-BR',{weekday:'short'}).replace('.','')),create('strong','',String(d.getDate())));
    week.append(item);
  }
  if(getRole()==='atleta'){
    const note=create('div','v11-empty','Para consultar suas atividades disponíveis, abra “Meu Dia”. A V10 fornece tarefas do dia atual; esta agenda não inventa tarefas para outras datas.');
    events.append(note);
    const b=create('button','','Abrir Meu Dia');b.type='button';b.onclick=()=>v8Show('atleta','meudia');events.append(b);
    return;
  }
  if(!matching.length){events.append(create('div','v11-empty',coachTeams.length?'Nenhum planejamento nesta semana para a equipe selecionada.':'Nenhuma equipe disponível. Crie uma equipe em “Equipes”.'));return;}
  matching.sort((a,b)=>a.dia.localeCompare(b.dia));
  for(const e of matching){const item=create('article','v11-event');item.append(create('small','',`${e.dia.split('-').reverse().join('/')} · ${e.tipo||'Atividade'}`),create('strong','',e.titulo||'Atividade'),create('p','',e.detalhes||''));events.append(item);}
}
function activateCalendar(){
  if(!['treinador','atleta'].includes(getRole()))return;
  originalShow(getRole(),'inicio');
  $11('v8Overview').classList.add('hidden');
  $11('v11Calendar').classList.remove('hidden');
  $11('v8Navigation').querySelectorAll('button').forEach(b=>b.setAttribute('aria-current',b.dataset.tab==='agenda'?'page':'false'));
  renderCalendar(true);
}
v8Show=function(tipo,tab){
  if(tab==='agenda'){activateCalendar();return;}
  hide();originalShow(tipo,tab);
};
v8Setup=function(tipo){
  hide();weekShift=0;coachTeams=[];coachAgenda=[];
  originalSetup(tipo);
  if(tipo==='treinador'||tipo==='atleta'){
    const nav=$11('v8Navigation');const b=create('button','','📆 Agenda');b.type='button';b.dataset.tab='agenda';b.onclick=activateCalendar;
    nav.insertBefore(b,nav.children[1]||null);
  }
  $11('v11Date').textContent=new Date().toLocaleDateString('pt-BR',{weekday:'long',day:'2-digit',month:'long'});
};
$11('v11PrevWeek').addEventListener('click',()=>{weekShift--;renderCalendar();});
$11('v11NextWeek').addEventListener('click',()=>{weekShift++;renderCalendar();});
$11('v11CalendarTeam').addEventListener('change',async()=>{try{await getAgenda();renderCalendar();}catch(e){$11('v11CalendarStatus').textContent=e.message;}});
$11('v11GoPlan').addEventListener('click',()=>v8Show('treinador','planejamento'));
})();
