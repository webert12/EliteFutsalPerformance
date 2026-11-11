/* V14: gráficos SVG locais; dados vêm exclusivamente da API autenticada. */
(()=>{'use strict';
const el=id=>document.getElementById(id);
const make=(tag,txt,cls)=>{const n=document.createElement(tag);if(txt!==undefined)n.textContent=txt;if(cls)n.className=cls;return n;};
function build(){if(el('v14Athlete'))return;const athlete=el('athleteDaily'),coach=el('trainerRoutine');if(!athlete||!coach)return;
for(const [parent,id,title,desc,kind] of [[athlete,'v14Athlete','📈 Minha evolução','Acompanhe seus próprios registros dos últimos dias.','atleta'],[coach,'v14Coach','📊 Central do treinador','Consulte a evolução individual de um atleta da sua equipe.','treinador']]){
 const section=make('section',undefined,'v14-panel');section.id=id;section.dataset.v14Role=kind;section.append(make('h3',title),make('p',desc,'v14-note'));
 const tools=make('div',undefined,'v14-tools');const l=make('label','Período');const sel=make('select');sel.id=id+'Period';sel.add(new Option('7 dias','7'));sel.add(new Option('30 dias','30'));l.append(sel);tools.append(l);
 if(kind==='treinador'){const hint=make('p','Escolha um atleta no campo Atividades do Treinador antes de consultar.','v14-note');section.append(hint);}
 const btn=make('button',kind==='atleta'?'Atualizar minha evolução':'Consultar atleta');btn.type='button';btn.addEventListener('click',()=>load(kind));tools.append(btn);section.append(tools);
 const status=make('p','Selecione o período e atualize.','v14-note');status.id=id+'Status';status.setAttribute('role','status');section.append(status);
 const metrics=make('div',undefined,'v14-metrics');metrics.id=id+'Metrics';section.append(metrics);
 const charts=make('div',undefined,'v14-charts');charts.id=id+'Charts';section.append(charts);
 section.append(make('p','Registros ausentes não contam como zero. Gráficos informativos, sem diagnóstico ou comparação entre atletas.','v14-note'));parent.prepend(section);
 }
}
const NS='http://www.w3.org/2000/svg';function svgNode(tag,attrs,txt){const n=document.createElementNS(NS,tag);for(const [k,v] of Object.entries(attrs||{}))n.setAttribute(k,String(v));if(txt!==undefined)n.textContent=txt;return n;}
function graph(container,title,days,key,max,unit){const card=make('div',undefined,'v14-chart');card.append(make('h4',title));const data=days.filter(x=>typeof x[key]==='number'&&Number.isFinite(x[key]));if(!data.length){card.append(make('p','Sem registros neste período.','v14-note'));container.append(card);return;}
 const svg=svgNode('svg',{viewBox:'0 0 320 155',role:'img','aria-label':title+' — '+data.length+' registros'});svg.append(svgNode('line',{x1:28,y1:120,x2:308,y2:120,stroke:'#4c6c52'}));
 const width=280/data.length;const ceiling=Math.max(max,...data.map(x=>x[key]),1);data.forEach((x,i)=>{const h=Math.max(2,Math.min(100,(x[key]/ceiling)*96));const bw=Math.min(30,Math.max(3,width-3));const cx=28+i*width+(width-bw)/2;const bar=svgNode('rect',{x:cx,y:120-h,width:bw,height:h,rx:3,fill:'#76e598'});bar.append(svgNode('title',{},`${x.dia}: ${x[key]} ${unit}`));svg.append(bar);if(data.length<=10||i%Math.ceil(data.length/7)===0)svg.append(svgNode('text',{x:cx+bw/2,y:139,'text-anchor':'middle'},x.dia.slice(8)));});
 svg.append(svgNode('text',{x:28,y:13},`${data.length} dia(s) com registro · máximo ${ceiling} ${unit}`));card.append(svg);container.append(card);
}
function metric(parent,title,value){const c=make('div',undefined,'v14-metric');c.append(make('strong',value),make('small',title));parent.append(c);}
function render(kind,data){const id=kind==='atleta'?'v14Athlete':'v14Coach',metrics=el(id+'Metrics'),charts=el(id+'Charts');metrics.replaceChildren();charts.replaceChildren();const days=data.dias||[];metric(metrics,'Dias com algum registro',`${days.length}/${data.periodo_dias}`);const hab=days.filter(x=>typeof x.habitos==='number');metric(metrics,'Dias com diário de hábitos',String(hab.length));const sono=days.filter(x=>typeof x.sono_horas==='number');metric(metrics,'Dias com sono registrado',String(sono.length));const water=days.filter(x=>typeof x.agua_ml==='number');metric(metrics,'Dias com água registrada',String(water.length));graph(charts,'Hábitos registrados (de 7)',days,'habitos',7,'hábitos');graph(charts,'Horas de sono registradas',days,'sono_horas',12,'h');graph(charts,'Água registrada',days,'agua_ml',2000,'mL');graph(charts,'Bem-estar informado (0 a 10)',days,'bem_estar_0_10',10,'pontos');}
async function load(kind){const id=kind==='atleta'?'v14Athlete':'v14Coach',s=el(id+'Status');if(!s||typeof request!=='function'||typeof token==='undefined'||!token)return;const period=el(id+'Period').value;let url='/api/v14/minha-evolucao?periodo='+period;if(kind==='treinador'){const athlete=el('taskAthlete')?.value;if(!athlete){s.textContent='Selecione primeiro um atleta na seção Atividades.';return;}url='/api/v14/atletas/'+encodeURIComponent(athlete)+'/evolucao?periodo='+period;}s.textContent='Consultando registros...';try{const result=await request(url);render(kind,result);s.textContent='Atualizado. Dados dos últimos '+period+' dias.';}catch(err){s.textContent=err.message||'Não foi possível consultar.';}}
function start(){build();const profile=el('profile');if(profile){let last='';new MutationObserver(()=>{const active=!profile.classList.contains('hidden')&&typeof role!=='undefined'?role:'';if(active!==last){last=active;if(active==='atleta')load('atleta');}}).observe(profile,{attributes:true,attributeFilter:['class']});}}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start);else start();
})();
