/* REAL ITA V12: conteúdo educativo e modelos, sem APIs novas ou coleta adicional. */
(()=>{'use strict';
const el=id=>document.getElementById(id);
const categories=[
 {id:'rotina',name:'📅 Minha rotina',cards:[
  ['Começo do dia','Faça seu registro de sono e bem-estar no Meu Dia. Veja o calendário e as tarefas enviadas pelo treinador.','Sono e rotina escolar também contam para a recuperação.'],
  ['Antes da atividade','Confira local, horário, material e orientações do treinador. Comunique dor, tontura ou mal-estar antes de começar.','Não acrescente exercícios extras sem orientação.'],
  ['Depois da atividade','Registre a conclusão, conte como se sentiu e reserve tempo para descanso, refeição habitual e água.','Nos dias sem quadra, respeite o descanso planejado.']]},
 {id:'alimentacao',name:'🥗 Alimentação',cards:[
  ['Refeições do cotidiano','Procure variedade: arroz, feijão, legumes, frutas e fontes de proteína como ovos, leite, carnes ou alternativas adequadas.','Exemplos educativos, não cardápio individual.'],
  ['Antes do treino','Não chegue ao treino sem se alimentar por longos períodos. Refeições e lanches devem respeitar horário, tolerância e acesso aos alimentos.','Evite experimentar alimentos novos imediatamente antes de jogos.'],
  ['Depois do treino','Retome sua alimentação habitual com uma refeição ou lanche que contenha alimentos energéticos e fontes de proteína.','Suplementos e dietas especiais exigem orientação profissional.'],
  ['Relação saudável com comida','Não pule refeições para mudar peso ou aparência. Seu corpo está crescendo; alimentação é cuidado, não punição.','O aplicativo não estabelece metas de calorias ou emagrecimento.']]},
 {id:'agua',name:'💧 Hidratação',cards:[
  ['Água ao longo do dia','Tenha água disponível, faça pausas para beber e observe sede, clima e duração das atividades.','Não há volume obrigatório igual para todos.'],
  ['Treino e calor','Leve uma garrafa e combine pausas com o treinador. Em calor intenso, o treino pode precisar de ajustes.','Tontura, confusão ou fraqueza exigem parar e buscar ajuda.']]},
 {id:'sono',name:'🌙 Sono',cards:[
  ['Descanso consistente','Adolescentes geralmente precisam de 8 a 10 horas de sono por noite. Tente manter horários regulares.','Sono ruim recorrente merece conversa com responsável e profissional de saúde.'],
  ['Recuperação','Evite acumular atividades extras em dias de descanso. O corpo se adapta ao treinamento quando há recuperação adequada.','Dor persistente não deve ser tratada com mais treino.']]},
 {id:'preparacao',name:'🏃 Preparação',cards:[
  ['Aquecimento orientado','Siga o aquecimento programado pelo treinador, com movimentos progressivos e adequados à sessão.','O app não define séries, cargas ou intensidade sozinho.'],
  ['Técnica e coordenação','Passe, domínio, condução e tomada de decisão podem ser trabalhados com tarefas específicas da sua equipe.','Execute apenas as tarefas recebidas e em ambiente seguro.'],
  ['Sinais de alerta','Dor, mal-estar, falta de ar fora do esperado ou tontura são motivos para interromper a atividade e procurar ajuda.','Avise o treinador e um responsável imediatamente.']]},
 {id:'escola',name:'🎒 Vida e bem-estar',cards:[
  ['Escola e esporte','Organize compromissos escolares, alimentação, deslocamento e horários de treino.','A rotina deve ser sustentável, não exaustiva.'],
  ['Saúde emocional','Cansaço mental, ansiedade ou desmotivação também merecem escuta e apoio.','Converse com um adulto de confiança.']]}];
const templates=[
 {name:'Orientação alimentar — dia de treino',type:'alimentacao',title:'Organização das refeições no dia de treino',details:'Mantenha suas refeições habituais e procure variedade alimentar ao longo do dia. Planeje um lanche conforme o horário do treino e sua tolerância. Leve água. Esta é uma orientação educativa; não substitui plano de nutricionista.'},
 {name:'Orientação alimentar — recuperação',type:'alimentacao',title:'Alimentação e recuperação',details:'Após a atividade, retome sua alimentação habitual e inclua alimentos variados que forneçam energia e proteína. Evite restrições alimentares. Em caso de necessidade individual, procure nutricionista.'},
 {name:'Hidratação e calor',type:'orientacao',title:'Cuidados com hidratação e calor',details:'Leve sua garrafa de água, faça pausas combinadas e avise se sentir tontura, fraqueza ou mal-estar. O treinador ajustará a sessão às condições do ambiente.'},
 {name:'Rotina de sono e descanso',type:'recuperacao',title:'Sono e recuperação',details:'Registre seu sono e organize horários regulares de descanso. Não acrescente treinos extras em dias de recuperação. Avise o treinador se estiver muito cansado.'},
 {name:'Aquecimento supervisionado',type:'preparacao',title:'Aquecimento antes do treino',details:'Realize apenas o aquecimento demonstrado e supervisionado pelo treinador, com progressão apropriada. Informe dor ou desconforto antes de iniciar.'},
 {name:'Fundamentos técnicos — passe e domínio',type:'treino',title:'Passe e domínio de bola',details:'Objetivo: melhorar passe, recepção e tomada de decisão. O treinador definirá exercícios, espaço, duração, pausas e progressões adequadas à equipe.'},
 {name:'Dia sem quadra',type:'recuperacao',title:'Dia de recuperação',details:'Hoje não há treino de quadra. Priorize alimentação habitual, água, descanso e rotina escolar. Faça atividade complementar somente se tiver sido orientada pelo treinador.'},
 {name:'Preparação para jogo',type:'jogo',title:'Organização para o dia do jogo',details:'Confira horário e local, organize equipamento e deslocamento, faça suas refeições habituais e leve água. Informe ao treinador qualquer dor ou mal-estar.'}];
function make(tag,txt,cls){const x=document.createElement(tag);if(cls)x.className=cls;if(txt!==undefined)x.textContent=txt;return x;}
function showCategory(id){const data=categories.find(x=>x.id===id)||categories[0],out=el('v12AthleteContent');out.replaceChildren();categories.forEach(c=>{const b=el('v12Tab_'+c.id);if(b)b.setAttribute('aria-pressed',String(c.id===data.id));});data.cards.forEach(([title,body,tip])=>{const card=make('article',undefined,'v12-card');card.append(make('h4',title),make('p',body),make('small',tip));out.append(card);});}
function setup(){const tabs=el('v12AthleteTabs');if(!tabs||tabs.children.length)return;categories.forEach(c=>{const b=make('button',c.name);b.id='v12Tab_'+c.id;b.type='button';b.className='outline';b.addEventListener('click',()=>showCategory(c.id));tabs.append(b);});showCategory('rotina');const s=el('v12CoachTemplate');templates.forEach((t,i)=>s.add(new Option(t.name,String(i))));s.addEventListener('change',preview);preview();el('v12ApplyCoach').addEventListener('click',()=>{const t=templates[Number(s.value)];if(!t)return;const ids=[['v10Type',t.type],['v10Title',t.title],['v10Details',t.details]];for(const [id,val] of ids){const field=el(id);if(field){field.value=val;field.dispatchEvent(new Event('change',{bubbles:true}));}}el('v12CoachMessage').textContent='Modelo preenchido no formulário Planejamento V10. Selecione a equipe, o destinatário e a data; revise antes de enviar.';el('v10Coach')?.scrollIntoView({behavior:'smooth',block:'start'});});}
function preview(){const t=templates[Number(el('v12CoachTemplate').value)]||templates[0],out=el('v12CoachPreview');out.replaceChildren();const c=make('article',undefined,'v12-card');c.append(make('span',t.name,'v12-tag'),make('h4',t.title),make('p',t.details));out.append(c);}
function sync(){const logged=el('profile')&&!el('profile').classList.contains('hidden');const r=typeof role!=='undefined'?role:'';el('v12Athlete')?.classList.toggle('hidden',!(logged&&r==='atleta'));el('v12Coach')?.classList.toggle('hidden',!(logged&&r==='treinador'));}
function start(){setup();sync();const target=el('profile');if(target){const obs=new MutationObserver(sync);obs.observe(target,{attributes:true,attributeFilter:['class']});}document.addEventListener('click',()=>queueMicrotask(sync));}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start);else start();
})();
