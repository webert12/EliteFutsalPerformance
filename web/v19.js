/* REAL ITA V19 — separação de contextos e navegação. Mantém os módulos e APIs existentes. */
(()=>{'use strict';
const $=id=>document.getElementById(id);
const oldShow=v8Show, oldSetup=v8Setup;
const groups={
 atleta:[['inicio','⌂','Visão geral'],['dia','☀','Meu dia'],['agenda','▦','Agendamento'],['treinos','⚽','Treinamentos'],['evolucao','↗','Minha evolução'],['mensagens','✉','Mensagens'],['avisos','◉','Avisos'],['perfil','♙','Meu perfil']],
 treinador:[['inicio','⌂','Visão geral'],['equipes','♧','Equipes'],['agenda','▦','Agendamento'],['planejamento','＋','Planejar'],['atletas','↗','Atletas e evolução'],['biblioteca','⚽','Biblioteca técnica'],['jogos','♜','Jogos e campeonatos'],['mensagens','✉','Mensagens'],['avisos','◉','Comunicados']],
 administrador:[['inicio','⌂','Visão geral'],['admin','♧','Treinadores']]
};
const names={dia:['Meu dia','Sua rotina de alimentação, hidratação, sono e recuperação.'],agenda:['Agendamento','Treinos, jogos e compromissos organizados por data.'],treinos:['Meus treinamentos','Atividades e orientações recebidas do treinador.'],evolucao:['Minha evolução','Seu histórico pessoal e seus indicadores.'],mensagens:['Mensagens','Converse com seu treinador dentro do REAL ITA.'],avisos:['Comunicados','Avisos da equipe e confirmações de leitura.'],atletas:['Atletas e evolução','Acompanhamento individual e indicadores autorizados.'],biblioteca:['Biblioteca técnica','Exercícios, sessões e prancheta tática.'],jogos:['Jogos e campeonatos','Partidas, escalações e resultados.'],planejamento:['Planejar atividades','Agende e envie atividades para sua equipe.'],equipes:['Minhas equipes','Gestão de equipes, treinos e presenças.'],perfil:['Meu perfil','Cadastro, equipe e autorização do responsável.'],admin:['Gestão de treinadores','Administração de acessos.']};
let current='inicio';
function make(tag,cls,text){const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n;}
function place(id,target){const el=$(id),host=$('v19-'+target);if(el&&host){host.append(el);el.classList.remove('hidden');el.hidden=false;}}
function setupViews(){
 const profile=$('profile');if(!profile||$('v19Workspace'))return;
 const workspace=make('div','v19-workspace');workspace.id='v19Workspace';
 const head=make('div','v19-pagehead');head.id='v19Pagehead';head.append(make('span','v19-eyebrow','REAL ITA · PERFORMANCE HUB'),make('h2','', 'Visão geral'),make('p','', 'Sua jornada esportiva em um só lugar.'));workspace.append(head);
 const ids=['home','dia','agenda-atleta','treinos','evolucao','mensagens-atleta','avisos-atleta','atletas','biblioteca','jogos','mensagens-treinador','avisos-treinador'];
 for(const id of ids){const v=make('section','v19-view');v.id='v19-'+id;workspace.append(v);}
 $('v8Navigation').after(workspace);
 const daily=$('athleteDaily');if(daily){
   // A agenda recebe somente atividades agendadas; hábitos e registro diário permanecem no Meu Dia.
   for(const id of ['v7Activities','myTasks','refreshMyTasks']){const e=$(id);if(e)$('v19-treinos').append(e);}
   place('athleteDaily','dia');
 }
 place('v10Athlete','dia');place('v12Athlete','dia');place('v18Athlete','dia');
 // Separar a conversa do assistente de rotina, sem duplicar controles nem alterar APIs.
 const aChat=$('v18AthleteChat');if(aChat){const container=$('v19-mensagens-atleta');const root=$('v18Athlete');const children=[...root.children];const marker=children.find(x=>x.tagName==='H3'&&x.textContent.includes('Perguntar ao treinador'));if(marker){for(const node of children.slice(children.indexOf(marker)))container.append(node);}}
 place('v9Athlete','evolucao');place('v13Athlete','evolucao');place('v14Athlete','evolucao');
 place('v17Athlete','avisos-atleta');
 place('v14Coach','atletas');place('v13Coach','atletas');place('v142Coach','atletas');place('v9Coach','atletas');
 place('v15Coach','biblioteca');place('v16Coach','jogos');place('v162Coach','jogos');
 place('v18Coach','mensagens-treinador');place('v17Coach','avisos-treinador');
 // A rotina do treinador (tarefas diretas) fica em Planejar, sem contaminar a Biblioteca.
 const routine=$('trainerRoutine');if(routine){routine.classList.add('v19-trainer-routine');}
 buildAgenda();buildHome();
}
function buildHome(){const h=$('v19-home');if(!h)return;h.replaceChildren();const hero=make('div','v19-hero');hero.append(make('span','v19-eyebrow','SEU ESPAÇO DE PERFORMANCE'),make('h2','', 'Cada dia é uma oportunidade de evoluir.'),make('p','','Planeje, acompanhe e converse com sua equipe — tudo organizado por assunto.'));h.append(hero);const grid=make('div','v19-shortcuts');h.append(grid);const list=role==='treinador'?[['agenda','▦','Agendamentos','Treinos e jogos da semana'],['planejamento','＋','Criar atividade','Envie para a equipe'],['atletas','↗','Acompanhar atletas','Indicadores e evolução'],['mensagens','✉','Conversas','Dúvidas dos atletas'],['jogos','♜','Competições','Resultados e escalações']]:role==='atleta'?[['dia','☀','Meu dia','Alimentação, hábitos e descanso'],['agenda','▦','Agendamento','Próximos treinos e jogos'],['treinos','⚽','Meus treinos','Atividades do treinador'],['evolucao','↗','Evolução','Acompanhe seus registros'],['mensagens','✉','Conversar','Pergunte ao treinador']]:[['admin','♧','Treinadores','Gerencie os acessos']];
 for(const [tab,icon,title,desc] of list){const b=make('button','v19-shortcut');b.type='button';b.append(make('span','v19-shortcut-icon',icon),make('strong','',title),make('small','',desc));b.onclick=()=>v8Show(role,tab);grid.append(b);}
}
function buildAgenda(){const box=$('v19-agenda-atleta');if(!box)return;box.replaceChildren();const top=make('div','v19-agenda-top');top.append(make('h3','','Próximos compromissos'));const btn=make('button','outline','Atualizar agenda');btn.type='button';btn.onclick=loadAgenda;top.append(btn);box.append(top);const status=make('p','v19-muted','Treinos e jogos enviados pelo treinador aparecerão aqui.');status.id='v19AgendaStatus';box.append(status);const list=make('div','v19-agenda-list');list.id='v19AgendaList';box.append(list);}
function isoDate(s){const [y,m,d]=s.split('-');return `${d}/${m}/${y}`;}
async function loadAgenda(){if(role!=='atleta')return;const status=$('v19AgendaStatus'),list=$('v19AgendaList');status.textContent='Carregando agendamentos...';list.replaceChildren();try{const data=await request('/api/v19/minha-agenda');if(!data.length){status.textContent='Nenhum treino ou jogo agendado neste período.';return;}status.textContent=`${data.length} compromisso(s) encontrados.`;let previous='';for(const e of data){if(e.dia!==previous){list.append(make('h3','v19-date',isoDate(e.dia)));previous=e.dia;}const c=make('article','v19-event');c.append(make('span','v19-event-type',e.tipo==='jogo'?'🏆 JOGO':e.tipo==='treino'?'⚽ TREINO':'🏃 PREPARAÇÃO'),make('strong','',e.titulo),make('p','',e.detalhes||''));list.append(c);}}catch(e){status.textContent='Não foi possível consultar: '+(e.message||'Tente novamente.');}}
function hideAll(){for(const el of document.querySelectorAll('.v19-view'))el.classList.remove('v19-active');$('v19Workspace').classList.add('hidden');$('v11Calendar')?.classList.add('hidden');}
function activate(tab){let view=tab;if(tab==='agenda'&&role==='atleta')view='agenda-atleta';if(tab==='mensagens')view='mensagens-'+role;if(tab==='avisos')view='avisos-'+role;
 hideAll();const target=$('v19-'+view);if(target){$('v19Workspace').classList.remove('hidden');target.classList.add('v19-active');}
 const info=names[tab]||['Visão geral','Seu espaço de acompanhamento esportivo.'];const header=$('v19Pagehead');header.querySelector('h2').textContent=info[0];header.querySelector('p').textContent=info[1];header.classList.toggle('hidden',tab==='inicio');
 for(const b of $('v8Navigation').querySelectorAll('button'))b.setAttribute('aria-current',b.dataset.tab===tab?'page':'false');
 if(tab==='inicio')buildHome();if(tab==='agenda'&&role==='atleta')loadAgenda();
 if(tab==='dia'&&role==='atleta'){try{v10LoadDay();}catch(_){}}
 if(tab==='evolucao'&&role==='atleta'){try{v9AthleteLoad();}catch(_){}}
 if(tab==='atletas'&&role==='treinador'){try{v9CoachLoad();}catch(_){}}
 // Alguns módulos antigos alternam .hidden ao entrar; só mostramos a seção do perfil autorizado.
 for(const id of [role==='atleta'?'v18Athlete':'v18Coach',role==='atleta'?'v17Athlete':'v17Coach']){const el=$(id);if(el)el.classList.remove('hidden');}
}
v8Show=function(tipo,tab){if(tipo!==role)return;current=tab;
 if(tipo==='administrador'){hideAll();oldShow(tipo,tab);if(tab==='inicio'){oldShow(tipo,'inicio');$('v8Overview').classList.add('hidden');activate('inicio');}return;}
 if(tipo==='treinador'&&tab==='agenda'){oldShow(tipo,'agenda');$('v19Workspace').classList.add('hidden');$('v19Pagehead').classList.add('hidden');for(const b of $('v8Navigation').querySelectorAll('button'))b.setAttribute('aria-current',b.dataset.tab==='agenda'?'page':'false');return;}
 const legacy=tab==='equipes'?'equipes':tab==='planejamento'?'planejamento':tab==='perfil'?'perfil':'inicio';oldShow(tipo,legacy);
 if(tab==='equipes'||tab==='planejamento'||tab==='perfil'){hideAll();if(tab==='planejamento'&&tipo==='treinador')$('trainerRoutine')?.classList.remove('hidden');for(const b of $('v8Navigation').querySelectorAll('button'))b.setAttribute('aria-current',b.dataset.tab===tab?'page':'false');return;}
 $('v8Overview').classList.add('hidden');$('trainerRoutine')?.classList.add('hidden');activate(tab);
};
v8Setup=function(tipo){oldSetup(tipo);setupViews();const nav=$('v8Navigation');nav.replaceChildren();for(const [id,icon,label] of groups[tipo]||[]){const b=make('button','v19-navbutton');b.type='button';b.dataset.tab=id;b.append(make('span','v19-navicon',icon),make('span','',label));b.onclick=()=>v8Show(tipo,id);nav.append(b);}v8Show(tipo,'inicio');};
function start(){setupViews();const profile=$('profile');if(profile)new MutationObserver(()=>{if(profile.classList.contains('hidden'))hideAll();}).observe(profile,{attributes:true,attributeFilter:['class']});}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start);else start();
})();
