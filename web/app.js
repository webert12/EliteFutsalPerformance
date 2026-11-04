let currentUserId=null;
"use strict";
const $ = id => document.getElementById(id);
let mode = "login";
let token = null; // Somente memória: não gravar JWT em localStorage.
let role = null;
function message(text, error=false) { $("message").textContent = text; $("message").classList.toggle("error",error); }
function showAuth(which) {
  mode=which;
  $("auth").classList.remove("hidden");
  $("nameWrap").classList.toggle("hidden",which!=="register");
  $("name").required=which==="register";
  $("password").minLength=which==="register"?12:1;
  $("password").autocomplete=which==="register"?"new-password":"current-password";
  $("authTitle").textContent=which==="register"?"Criar conta":"Entrar";
  $("submit").textContent=$("authTitle").textContent;
  message("");
  $("auth").scrollIntoView({behavior:"smooth"});
}
$("enter").onclick=()=>showAuth("login");
$("register").onclick=()=>showAuth("register");
async function request(path, options={}) {
  const headers={"Content-Type":"application/json",...(options.headers||{})};
  if(token) headers.Authorization="Bearer "+token;
  const response=await fetch(path,{...options,headers,cache:"no-store"});
  const contentType=response.headers.get("content-type")||"";
  const data=contentType.includes("application/json")?await response.json():{};
  if(!response.ok){
    const detail=typeof data.detail==="string"?data.detail:(Array.isArray(data.detail)?data.detail.map(x=>x.msg).join("; "):"Erro HTTP "+response.status);
    if(response.status===401 && token){logout(false);throw new Error("Sua sessão expirou. Entre novamente.");}
    throw new Error(detail);
  }
  return data;
}
async function health(){
  try {const r=await fetch("/health",{cache:"no-store"});$("status").textContent=r.ok?"● Servidor online":"● Serviço indisponível";}
  catch {$("status").textContent="● Sem conexão";}
}
health();
$("form").onsubmit=async event=>{
  event.preventDefault();
  $("submit").disabled=true;
  message("Aguarde...");
  try {
    const data={email:$("email").value.trim(),senha:$("password").value};
    if(mode==="register"){
      data.nome=$("name").value.trim();
      await request("/auth/cadastro",{method:"POST",body:JSON.stringify(data)});
      showAuth("login");message("Conta criada! Entre com seu e-mail e senha.");
    } else {
      const result=await request("/auth/login",{method:"POST",body:JSON.stringify(data)});
      if(!result.access_token)throw new Error("O servidor não retornou o token de acesso.");
      token=result.access_token;
      const user=await request("/auth/me");
      role=user.tipo_usuario;currentUserId=user.id;
      $("who").textContent="Olá, "+user.nome+"! Perfil: "+role+".";
      const staff=role==="treinador";
      const titles={administrador:"Administração",treinador:"Central do treinador",atleta:"Meu Dia"};
      const descriptions={administrador:"Gerencie as contas dos treinadores.",treinador:"Organize suas equipes, treinos e atividades individuais.",atleta:"Confira suas atividades e registre seu dia."};
      $("panelTitle").textContent=titles[role]||"Meu painel";
      $("panelLabel").textContent=(role||"USUÁRIO").toUpperCase();
      $("publicHero").classList.add("hidden");$("publicCards").classList.add("hidden");
      $("adminTools").classList.add("hidden");$("staffTools").classList.add("hidden");
      $("v8Navigation").classList.add("hidden");$("v8Overview").classList.add("hidden");$("v4Tools").classList.add("hidden");$("trainerRoutine").classList.add("hidden");$("athleteTools").classList.add("hidden");
      $("adminTools").classList.toggle("hidden",role!=="administrador");
      // A listagem geral não aparece no painel do treinador; use somente as equipes vinculadas.
      $("roleHelp").textContent=descriptions[role]||"Sua conta está ativa.";
      $("auth").classList.add("hidden");$("profile").classList.remove("hidden");
      $("password").value="";
      $("profile").scrollIntoView({behavior:"smooth"});

      v8Setup(role);
      if(staff){await initV4();$("trainerRoutine").classList.remove("hidden");await v7InitCoach();}
      if(role==="atleta")await initAthleteV5(user.id);
      if(role==="administrador")await loadAdmin();
    }
  } catch(err){message(err.message||"Falha na conexão",true);}
  finally{$("submit").disabled=false;}
};
async function loadAthletes(){
  $("athletesMessage").textContent="Carregando atletas...";
  $("athletesList").replaceChildren();
  try{
    const athletes=await request("/api/atletas");
    $("athletesMessage").textContent=athletes.length?athletes.length+" atleta(s) cadastrado(s).":"Nenhum atleta cadastrado ainda.";
    for(const athlete of athletes){
      const item=document.createElement("div");item.className="athlete-item";
      const title=document.createElement("strong");title.textContent="Atleta #"+athlete.id;
      const desc=document.createElement("small");desc.textContent="Cadastro disponível para acompanhamento pela equipe.";
      item.append(title,desc);$("athletesList").append(item);
    }
  }catch(err){$("athletesMessage").textContent="Não foi possível carregar atletas: "+err.message;}
}
$("loadAthletes").onclick=loadAthletes;
function logout(showLogin=true){
  $("v4Tools").classList.add("hidden");$("trainerRoutine").classList.add("hidden");$("athleteTools").classList.add("hidden");token=null;role=null;currentUserId=null;$("adminTools").classList.add("hidden");
  $("profile").classList.add("hidden");$("publicHero").classList.remove("hidden");$("publicCards").classList.remove("hidden");$("staffTools").classList.add("hidden");$("athletesList").replaceChildren();
  $("form").reset();
  if(showLogin)showAuth("login");
}
$("logout").onclick=()=>logout();

// V3: administração. Autorização real sempre validada pelo backend.
async function loadAdmin(){
  if(role!=="administrador")return;
  try{
    const [trainers,users]=await Promise.all([request('/api/admin/treinadores'),request('/api/admin/usuarios-atletas')]);
    $('trainerList').replaceChildren();
    for(const t of trainers){const item=document.createElement('div');item.className='athlete-item';item.textContent=t.nome+' — '+t.email;$('trainerList').append(item);}
    if(!trainers.length)$('trainerList').textContent='Nenhum treinador cadastrado.';
    const select=$('athleteUser');select.replaceChildren(new Option('Selecione uma conta',''));
    for(const u of users)select.add(new Option(u.nome+' ('+u.email+')',String(u.id)));
  }catch(e){$('trainerMessage').textContent='Não foi possível carregar os dados: '+e.message;}
}
$('refreshTrainers').onclick=loadAdmin;
$('trainerForm').onsubmit=async e=>{
  e.preventDefault();const button=$('trainerSubmit');button.disabled=true;
  try{
    await request('/api/admin/treinadores',{method:'POST',body:JSON.stringify({nome:$('trainerName').value.trim(),email:$('trainerEmail').value.trim(),senha:$('trainerPassword').value})});
    $('trainerForm').reset();$('trainerMessage').textContent='Treinador criado. Oriente-o a alterar a senha inicial quando houver essa funcionalidade.';await loadAdmin();
  }catch(err){$('trainerMessage').textContent=err.message;}finally{button.disabled=false;$('trainerPassword').value='';}
};
$('athleteForm').onsubmit=async e=>{
  e.preventDefault();const button=$('athleteSubmit');button.disabled=true;
  try{
    const payload={usuario_id:Number($('athleteUser').value),nascimento:$('athleteBirth').value,posicao:$('athletePosition').value,altura_cm:Number($('athleteHeight').value),peso_kg:Number($('athleteWeight').value),pe_dominante:$('athleteFoot').value||null};
    await request('/api/atletas',{method:'POST',body:JSON.stringify(payload)});
    $('athleteForm').reset();$('athleteMessage').textContent='Ficha esportiva cadastrada.';await loadAdmin();await loadAthletes();
  }catch(err){$('athleteMessage').textContent=err.message;}finally{button.disabled=false;}
};

// V4: Equipes, sessões e presença. A API valida as permissões novamente.
let v4Athletes=[];
const v4Msg=t=>{$('v4Message').textContent=t;};
async function initV4(){
 $('v4Tools').classList.remove('hidden');
 $('v4TeamForm').classList.toggle('hidden',role!=='treinador');
 $('v4LinkBox').classList.toggle('hidden',role!=='treinador');
 $('v4Date').value=new Date().toLocaleDateString('en-CA');
 if(role==='treinador'){$('v4Trainer').replaceChildren(new Option('Minha conta',String(currentUserId)));}
 await v4LoadTeams();
}
async function v4LoadTeams(){
 try{const teams=await request('/api/v4/equipes');const s=$('v4TeamSelect');const old=s.value;s.replaceChildren(new Option('Selecione uma equipe',''));teams.forEach(t=>s.add(new Option(t.nome+' · '+t.categoria,String(t.id))));if(teams.some(t=>String(t.id)===old))s.value=old;await v4LoadTeam();}
 catch(e){v4Msg(e.message);}
}
async function v4LoadTeam(){
 const id=$('v4TeamSelect').value;$('v4Roster').replaceChildren();$('v4TrainingSelect').replaceChildren(new Option('Selecione',''));v4Athletes=[];
 if(!id)return;
 try{
  const [athletes,trainings]=await Promise.all([request('/api/v4/equipes/'+id+'/atletas'),request('/api/v4/equipes/'+id+'/treinos')]);v4Athletes=athletes;
  trainings.forEach(t=>$('v4TrainingSelect').add(new Option(t.data+' · '+t.objetivo,String(t.id))));
  if(role==='treinador'){
   const all=await request('/api/atletas');const linked=new Set(athletes.map(a=>a.id));$('v4AthleteSelect').replaceChildren(new Option('Selecione',''));all.filter(a=>!linked.has(a.id)).forEach(a=>$('v4AthleteSelect').add(new Option('Ficha #'+a.id+' · '+a.posicao,String(a.id))));
  }
  if(role==='treinador'){$('taskAthlete').replaceChildren(new Option('Selecione',''));athletes.forEach(a=>$('taskAthlete').add(new Option(a.nome,String(a.id))));}
  await v6LoadRequests();await v4LoadAttendance();v4Msg(athletes.length+' atleta(s) nesta equipe.');
 }catch(e){v4Msg(e.message);}
}
async function v4LoadAttendance(){
 const tid=$('v4TrainingSelect').value;$('v4Roster').replaceChildren();if(!tid)return;
 try{
  const saved=await request('/api/v4/treinos/'+tid+'/presencas');const statuses=new Map(saved.map(p=>[p.atleta_id,p.situacao]));
  for(const a of v4Athletes){
   const div=document.createElement('div');div.className='athlete-item';const name=document.createElement('strong');name.textContent=a.nome+' · '+a.posicao;
   const sel=document.createElement('select');[['','Não marcado'],['presente','Presente'],['ausente','Ausente'],['justificado','Justificado']].forEach(([v,n])=>sel.add(new Option(n,v)));
   sel.value=statuses.get(a.id)||'';sel.onchange=async()=>{if(!sel.value)return;sel.disabled=true;try{await request('/api/v4/treinos/'+tid+'/presencas',{method:'PUT',body:JSON.stringify({atleta_id:a.id,situacao:sel.value})});v4Msg('Presença salva.');}catch(e){v4Msg(e.message);}finally{sel.disabled=false;}};
   div.append(name,sel);$('v4Roster').append(div);
  }
 }catch(e){v4Msg(e.message);}
}
$('v4Refresh').onclick=v4LoadTeams;
$('v4TeamSelect').onchange=v4LoadTeam;
$('v4TrainingSelect').onchange=v4LoadAttendance;
$('v4TeamForm').onsubmit=async e=>{e.preventDefault();try{await request('/api/v4/equipes',{method:'POST',body:JSON.stringify({nome:$('v4TeamName').value.trim(),categoria:$('v4Category').value,treinador_id:Number($('v4Trainer').value)})});$('v4TeamForm').reset();await v4LoadTeams();v4Msg('Equipe criada.');}catch(err){v4Msg(err.message);}};
$('v4Link').onclick=async()=>{const id=$('v4TeamSelect').value,athlete=$('v4AthleteSelect').value;if(!id||!athlete){v4Msg('Selecione equipe e atleta.');return;}try{await request('/api/v4/equipes/'+id+'/atletas',{method:'POST',body:JSON.stringify({atleta_id:Number(athlete)})});await v4LoadTeam();v4Msg('Atleta vinculado.');}catch(e){v4Msg(e.message);}};
$('v4TrainingForm').onsubmit=async e=>{e.preventDefault();const id=$('v4TeamSelect').value;if(!id){v4Msg('Selecione uma equipe.');return;}try{await request('/api/v4/equipes/'+id+'/treinos',{method:'POST',body:JSON.stringify({data:$('v4Date').value,objetivo:$('v4Goal').value.trim(),duracao_min:Number($('v4Duration').value)})});await v4LoadTeam();v4Msg('Treino registrado. Selecione-o para marcar presença.');}catch(err){v4Msg(err.message);}};

// V5: rotina individual, com autorização de acesso no servidor.
async function initAthleteV5(uid){
 $('athleteTools').classList.remove('hidden');$('dailyDate').value=new Date().toLocaleDateString('en-CA');
 try{await request('/api/atletas/me');$('selfProfileForm').classList.add('hidden');await v6LoadAccess();}
 catch(e){$('selfProfileForm').classList.remove('hidden');$('athleteDaily').classList.add('hidden');$('athleteDailyMessage').textContent=e.message;}
}
$('selfProfileForm').onsubmit=async e=>{e.preventDefault();try{
 await request('/api/atletas',{method:'POST',body:JSON.stringify({usuario_id:currentUserId,nascimento:$('selfBirth').value,posicao:$('selfPosition').value,altura_cm:Number($('selfHeight').value),peso_kg:Number($('selfWeight').value)})});
 $('athleteDailyMessage').textContent='Ficha salva.';await initAthleteV5(currentUserId);
}catch(err){$('athleteDailyMessage').textContent=err.message;}};
$('dailyForm').onsubmit=async e=>{e.preventDefault();const num=id=>$(id).value===''?null:Number($(id).value);try{
 await request('/api/v5/meu-registro',{method:'POST',body:JSON.stringify({dia:$('dailyDate').value,sono_horas:num('dailySleep'),agua_ml:num('dailyWater'),bem_estar_0_10:num('dailyWell'),esforco_0_10:num('dailyEffort'),duracao_treino_min:num('dailyMinutes'),dor_ou_lesao:$('dailyPain').checked})});
 $('athleteDailyMessage').textContent='Registro salvo. Em caso de dor, avise seu responsável e treinador.';await v6LoadToday();
}catch(err){$('athleteDailyMessage').textContent=err.message;}};
async function refreshMyTasks(){try{const tasks=await request('/api/v5/minhas-tarefas');$('myTasks').replaceChildren();if(!tasks.length)$('myTasks').textContent='Nenhuma atividade atribuída neste período.';
 for(const t of tasks){const d=document.createElement('div');d.className='athlete-item';const title=document.createElement('strong');title.textContent=t.dia+' · '+t.titulo;const desc=document.createElement('p');desc.textContent=t.descricao;const b=document.createElement('button');b.textContent=t.concluida?'Marcar como pendente':'Concluir';b.onclick=async()=>{try{await request('/api/v5/minhas-tarefas/'+t.id,{method:'PUT',body:JSON.stringify({concluida:!t.concluida})});await refreshMyTasks();}catch(e){$('athleteDailyMessage').textContent=e.message;}};d.append(title,desc,b);$('myTasks').append(d);}
}catch(e){$('athleteDailyMessage').textContent=e.message;}}
$('refreshMyTasks').onclick=refreshMyTasks;
$('taskForm').onsubmit=async e=>{e.preventDefault();try{const id=Number($('taskAthlete').value);if(!id)throw Error('Selecione um atleta');await request('/api/v5/tarefas',{method:'POST',body:JSON.stringify({atleta_id:id,dia:$('taskDate').value,titulo:$('taskTitle').value.trim(),descricao:$('taskDescription').value.trim()})});$('taskMessage').textContent='Atividade enviada.';await loadTaskHistory();}catch(err){$('taskMessage').textContent=err.message;}};
async function loadTaskHistory(){const id=$('taskAthlete').value;$('taskHistory').replaceChildren();if(!id)return;try{const [tasks,records]=await Promise.all([request('/api/v5/atletas/'+id+'/tarefas'),request('/api/v5/atletas/'+id+'/registros')]);for(const t of tasks){const d=document.createElement('div');d.className='athlete-item';d.textContent=t.dia+' · '+t.titulo+' — '+(t.concluida?'Concluída':'Pendente');$('taskHistory').append(d);}for(const r of records.slice(0,7)){const d=document.createElement('div');d.className='athlete-item';d.textContent=r.dia+' · Sono: '+(r.sono_horas??'—')+'h · Bem-estar: '+(r.bem_estar_0_10??'—')+' · Dor: '+(r.dor_ou_lesao?'Sim':'Não');$('taskHistory').append(d);}}catch(e){$('taskMessage').textContent=e.message;}}
$('taskAthlete').onchange=loadTaskHistory;
$('taskDate').value=new Date().toLocaleDateString('en-CA');

// V6 — convites, declaração do responsável e Meu Dia
async function v6LoadAccess(){
 try{const d=await request('/api/v6/meu-acesso');
 $('v6AccessStatus').textContent=d.consentimento?'Autorização registrada. '+d.solicitacoes.map(x=>'Equipe #'+x.equipe_id+': '+x.status).join(' · '):'Aguardando autorização do responsável. A rotina permanece bloqueada.';
 $('v6ConsentCode').classList.toggle('hidden',d.consentimento);
 $('v6JoinForm').classList.toggle('hidden',!d.consentimento);
 $('athleteDaily').classList.toggle('hidden',!d.consentimento);
 if(d.consentimento){await refreshMyTasks();await v6LoadToday();await v7LoadDay();}
 }catch(e){$('v6AccessStatus').textContent=e.message;}
}
$('v6ConsentCode').onclick=async()=>{try{const d=await request('/api/v6/codigo-responsavel',{method:'POST'});
 const link=location.origin+'/responsavel?codigo='+encodeURIComponent(d.codigo);
 $('v6ConsentResult').replaceChildren();const p=document.createElement('p');p.textContent='Entregue este endereço diretamente ao responsável (válido por 48 horas). Não compartilhe em grupos:';
 const a=document.createElement('a');a.href=link;a.textContent=link;a.target='_blank';a.rel='noopener noreferrer';$('v6ConsentResult').append(p,a);
 }catch(e){$('v6ConsentResult').textContent=e.message;}};
$('v6JoinForm').onsubmit=async e=>{e.preventDefault();try{await request('/api/v6/solicitar-equipe',{method:'POST',body:JSON.stringify({codigo:$('v6JoinCode').value.trim()})});$('v6JoinCode').value='';$('v6JoinResult').textContent='Solicitação enviada. Aguarde aprovação do treinador.';await v6LoadAccess();}catch(err){$('v6JoinResult').textContent=err.message;}};
$('v6Invite').onclick=async()=>{const eid=$('v4TeamSelect').value;if(!eid){v4Msg('Selecione uma equipe.');return;}try{const d=await request('/api/v6/equipes/'+eid+'/convites',{method:'POST'});$('v6InviteResult').textContent='Convite de uso único (3 dias): '+d.codigo+' — compartilhe individualmente com o atleta.';}catch(e){v4Msg(e.message);}};
async function v6LoadRequests(){const eid=$('v4TeamSelect').value;$('v6Requests').replaceChildren();if(!eid)return;
 try{const rows=await request('/api/v6/equipes/'+eid+'/solicitacoes');if(!rows.length)$('v6Requests').textContent='Nenhuma solicitação pendente.';
 for(const r of rows){const div=document.createElement('div');div.className='athlete-item';const t=document.createElement('p');t.textContent=r.nome+' · Autorização registrada: '+(r.consentimento?'sim':'não');const btn=document.createElement('button');btn.textContent='Aprovar';btn.disabled=!r.consentimento;btn.onclick=async()=>{try{await request('/api/v6/solicitacoes/'+r.id+'/aprovar',{method:'POST'});await v4LoadTeam();}catch(e){v4Msg(e.message);}};const no=document.createElement('button');no.textContent='Recusar';no.className='outline';no.onclick=async()=>{try{await request('/api/v6/solicitacoes/'+r.id+'/recusar',{method:'POST'});await v6LoadRequests();}catch(e){v4Msg(e.message);}};div.append(t,btn,no);$('v6Requests').append(div);}
 }catch(e){v4Msg(e.message);}}
$('v6RefreshRequests').onclick=v6LoadRequests;
async function v6LoadToday(){try{const d=await request('/api/v6/meu-dia');$('v6TodayStatus').textContent=d.data+' · Registro diário: '+(d.registro_feito?'feito':'pendente')+' · '+d.tarefas.filter(x=>x.concluida).length+'/'+d.tarefas.length+' tarefas concluídas';$('v6TodayTasks').replaceChildren();
 for(const t of d.tarefas){const div=document.createElement('div');div.className='athlete-item';const title=document.createElement('strong');title.textContent=t.titulo;const desc=document.createElement('p');desc.textContent=t.descricao;const button=document.createElement('button');button.textContent=t.concluida?'Concluída ✓':'Concluir atividade';button.disabled=t.concluida;button.onclick=async()=>{try{await request('/api/v5/minhas-tarefas/'+t.id,{method:'PUT',body:JSON.stringify({concluida:true})});await v6LoadToday();await refreshMyTasks();}catch(e){$('athleteDailyMessage').textContent=e.message;}};div.append(title,desc,button);$('v6TodayTasks').append(div);}
 if(!d.tarefas.length)$('v6TodayTasks').textContent='Nenhuma tarefa orientada para hoje.';$('v6TodayTips').textContent=d.orientacoes.join(' ');
 }catch(e){$('v6TodayStatus').textContent=e.message;}}
$('v6TodayRefresh').onclick=async()=>{await v6LoadAccess();};

$('v6AccessRefresh').onclick=v6LoadAccess;


// V7 — módulos independentes para atleta e treinador. O servidor valida o perfil.
async function v7LoadDay(){
 if(role!=='atleta')return;
 try{
  const d=await request('/api/v7/meu-dia');
  const h=d.habitos||{};
  for(const [id,key] of [['v7Cafe','cafe'],['v7Almoco','almoco'],['v7Jantar','jantar'],['v7Agua','agua'],['v7Descanso','descanso']])$(id).checked=Boolean(h[key]);
  $('v7Obs').value=h.observacao||'';
  $('v7Tips').replaceChildren();
  for(const tip of d.orientacoes){const item=document.createElement('div');item.className='athlete-item';item.textContent=tip;$('v7Tips').append(item);}
  $('v7Activities').replaceChildren();
  if(!d.tarefas.length)$('v7Activities').textContent='Nenhuma atividade prescrita para hoje. Não acrescente exercícios por conta própria.';
  for(const t of d.tarefas){const item=document.createElement('div');item.className='athlete-item';const title=document.createElement('strong');title.textContent=t.titulo;const desc=document.createElement('p');desc.textContent=t.descricao;const b=document.createElement('button');b.textContent=t.concluida?'Concluída ✓':'Marcar concluída';b.disabled=t.concluida;b.onclick=async()=>{try{await request('/api/v5/minhas-tarefas/'+t.id,{method:'PUT',body:JSON.stringify({concluida:true})});await v7LoadDay();await v6LoadToday();}catch(e){$('v7HabitsStatus').textContent=e.message;}};item.append(title,desc,b);$('v7Activities').append(item);}
 }catch(e){$('v7HabitsStatus').textContent=e.message;}
}
$('v7HabitsForm').onsubmit=async e=>{
 e.preventDefault();
 try{
  const payload={dia:new Date().toLocaleDateString('en-CA'),cafe:$('v7Cafe').checked,almoco:$('v7Almoco').checked,jantar:$('v7Jantar').checked,agua:$('v7Agua').checked,descanso:$('v7Descanso').checked,observacao:$('v7Obs').value.trim()||null};
  await request('/api/v7/meus-habitos',{method:'PUT',body:JSON.stringify(payload)});
  $('v7HabitsStatus').textContent='Hábitos registrados para hoje.';
 }catch(err){$('v7HabitsStatus').textContent=err.message;}
};
async function v7InitCoach(){
 if(role!=='treinador')return;
 try{const catalog=await request('/api/v7/biblioteca');$('v7Exercise').replaceChildren(new Option('Escolha um exercício',''));for(const x of catalog)$('v7Exercise').add(new Option(x.titulo,x.codigo));window.v7Catalog=catalog;}
 catch(e){$('v7CoachStatus').textContent=e.message;}
}
$('v7ApplyExercise').onclick=()=>{
 const x=(window.v7Catalog||[]).find(item=>item.codigo===$('v7Exercise').value);
 if(!x){$('v7CoachStatus').textContent='Selecione um modelo.';return;}
 $('taskTitle').value=x.titulo;$('taskDescription').value=x.descricao;
 $('taskTitle').scrollIntoView({behavior:'smooth',block:'center'});
};
$('v7CoachRefresh').onclick=async()=>{
 const id=Number($('taskAthlete').value);$('v7CoachHabits').replaceChildren();
 if(!id){$('v7CoachStatus').textContent='Selecione um atleta da sua equipe.';return;}
 try{const rows=await request('/api/v7/atletas/'+id+'/semana');if(!rows.length)$('v7CoachHabits').textContent='Sem registros nesta semana.';
  for(const h of rows){const div=document.createElement('div');div.className='athlete-item';div.textContent=h.dia+' · Refeições: '+[h.cafe,h.almoco,h.jantar].filter(Boolean).length+'/3 · Água: '+(h.agua?'sim':'não registrado')+' · Descanso: '+(h.descanso?'sim':'não registrado');$('v7CoachHabits').append(div);}
  $('v7CoachStatus').textContent='Registros atualizados.';
 }catch(e){$('v7CoachStatus').textContent=e.message;}
};


// V8: painel visual, sem conceder novas permissões. O servidor continua sendo a autoridade.
const v8Tabs={
  administrador:[['inicio','🏠 Início'],['admin','👥 Treinadores']],
  treinador:[['inicio','🏠 Início'],['equipes','👥 Equipes e treinos'],['atividades','📋 Atividades'],['performance','📈 Performance'],['planejamento','📅 Planejamento']],
  atleta:[['inicio','🏠 Meu Dia'],['rotina','🌿 Rotina e hábitos'],['performance','💚 Performance'],['perfil','🛡️ Meu cadastro'],['meudia','🌞 Meu Dia V10']]
};
function v8Setup(tipo){
  const nav=$('v8Navigation');nav.replaceChildren();
  if(!v8Tabs[tipo])return;
  nav.classList.remove('hidden');$('v8Overview').classList.remove('hidden');
  for(const [id,label] of v8Tabs[tipo]){
    const b=document.createElement('button');b.type='button';b.textContent=label;
    b.dataset.tab=id;b.onclick=()=>v8Show(tipo,id);nav.append(b);
  }
  v8Show(tipo,'inicio');
}
function v8Card(icon,title,description,target){
  const item=document.createElement('article');item.className='v8-tile';
  const emoji=document.createElement('div');emoji.className='v8-icon';emoji.textContent=icon;
  const h=document.createElement('strong');h.textContent=title;
  const p=document.createElement('p');p.textContent=description;
  item.append(emoji,h,p);
  if(target){const b=document.createElement('button');b.type='button';b.textContent='Abrir';b.onclick=()=>v8Show(role,target);item.append(b);}
  return item;
}
function v8Show(tipo,tab){
  if(role!==tipo)return;
  const overview=$('v8Overview');overview.replaceChildren();
  const nav=$('v8Navigation');for(const b of nav.querySelectorAll('button'))b.setAttribute('aria-current',b.dataset.tab===tab?'page':'false');
  const sections=['adminTools','v4Tools','trainerRoutine','athleteTools','v9Athlete','v9Coach','v10Athlete','v10Coach'];
  sections.forEach(id=>$(id).classList.add('hidden'));
  const add=(...cards)=>cards.forEach(c=>overview.append(c));
  if(tipo==='administrador'){
    if(tab==='admin')$('adminTools').classList.remove('hidden');
    else add(v8Card('👥','Treinadores','Cadastre e gerencie os acessos dos treinadores.','admin'),v8Card('🛡️','Acesso protegido','A administração não realiza treinos nem registros de atletas.'));
  }else if(tipo==='treinador'){
    if(tab==='equipes')$('v4Tools').classList.remove('hidden');
    else if(tab==='atividades')$('trainerRoutine').classList.remove('hidden');
    else if(tab==='performance'){$('v9Coach').classList.remove('hidden');v9CoachLoad();}
    else if(tab==='planejamento'){$('v10Coach').classList.remove('hidden');v10LoadCoach();}
    else add(v8Card('👥','Minhas equipes','Convites, presenças, calendário e treinos.','equipes'),v8Card('🏃','Exercícios e tarefas','Planeje atividades técnicas e acompanhe os atletas.','atividades'),v8Card('📈','Performance','Check-ins, biblioteca técnica, avaliações e relatório semanal.','performance'),v8Card('📅','Planejamento semanal','Envie orientações para equipe inteira ou atleta individual.','planejamento'));
  }else if(tipo==='atleta'){
    if(tab==='rotina'){$('athleteTools').classList.remove('hidden');$('v6Access').classList.add('hidden');}
    else if(tab==='performance'){$('v9Athlete').classList.remove('hidden');v9AthleteLoad();}
    else if(tab==='meudia'){$('v10Athlete').classList.remove('hidden');v10LoadDay();}
    else if(tab==='perfil'){$('athleteTools').classList.remove('hidden');$('v6Access').classList.remove('hidden');$('athleteDaily').classList.add('hidden');}
    else {
      $('v6Access').classList.remove('hidden');
      add(v8Card('🌞','Meu Dia V10','Veja orientações e tarefas organizadas para hoje.','meudia'),v8Card('🏃','Exercícios do dia','Veja e conclua as tarefas enviadas pelo treinador.','rotina'),v8Card('🥗','Alimentação','Registre refeições; orientações educativas, sem dieta prescrita.','rotina'),v8Card('💧','Hidratação','Registre seus hábitos e consumo de água.','rotina'),v8Card('🌙','Sono e recuperação','Registre o sono e o descanso diário.','rotina'),v8Card('💚','Bem-estar e evolução','Check-in e avaliações individuais.','performance'),v8Card('🛡️','Minha equipe','Autorização do responsável e solicitação de entrada.','perfil'));
      v8LoadProgress();
    }
    if(tab!=='perfil' && $('v6AccessStatus').textContent) { /* a rotina mantém as regras de autorização do V6 */ }
    if(tab==='rotina')$('athleteDaily').classList.remove('hidden');
  }
  overview.classList.toggle('hidden',tab!=='inicio');
  if(tab!=='inicio')setTimeout(()=>nav.scrollIntoView({behavior:'smooth',block:'start'}),0);
}
async function v8LoadProgress(){
  if(role!=='atleta'||!token)return;
  try{
    const data=await request('/api/v7/meu-dia');
    if(role!=='atleta'||!$('v8Overview').children.length)return;
    const total=(data.tarefas||[]).length;
    const done=(data.tarefas||[]).filter(x=>x.concluida).length;
    const h=data.habitos||{};const habits=['cafe','almoco','jantar','agua','descanso'];
    const doneHabits=habits.filter(x=>h[x]).length;
    const progress=document.createElement('article');progress.className='v8-tile v8-heading';
    const heading=document.createElement('strong');heading.textContent='📅 Resumo de hoje';
    const info=document.createElement('p');info.textContent=`${done} de ${total} atividades do treinador concluídas · ${doneHabits} de 5 hábitos registrados`;
    const bar=document.createElement('div');bar.className='v8-progress';
    const fill=document.createElement('span');fill.style.width=((done+doneHabits)/(total+5)*100)+'%';bar.append(fill);
    progress.append(heading,info,bar);$('v8Overview').prepend(progress);
  }catch(_){/* Sem ficha ou autorização: não revelar detalhes privados. */}
}

// V9 — funcionalidades independentes; as autorizações são verificadas pelo servidor.
const v9Today=()=>new Date(Date.now()-new Date().getTimezoneOffset()*60000).toISOString().slice(0,10);
$('v9CheckinDate').value=v9Today();$('v9AssessmentDate').value=v9Today();
function v9Line(target,value){const d=document.createElement('div');d.className='athlete-item';d.textContent=value;$(target).append(d);}
async function v9AthleteLoad(){
 if(role!=='atleta')return;
 $('v9Tips').replaceChildren();$('v9MyAssessments').replaceChildren();
 try{const [tips,assessments,checkins]=await Promise.all([request('/api/v9/orientacoes'),request('/api/v9/minhas-avaliacoes'),request('/api/v9/meus-checkins')]);
 for(const [key,values] of Object.entries(tips)){v9Line('v9Tips',key.toUpperCase());values.forEach(t=>v9Line('v9Tips','• '+t));}
 for(const a of assessments)v9Line('v9MyAssessments',`${a.dia} · ${a.fundamento}: ${a.nota}/5${a.observacao?' · '+a.observacao:''}`);
 if(!assessments.length)v9Line('v9MyAssessments','Nenhuma avaliação registrada pelo treinador.');
 if(checkins.length)$('v9CheckinStatus').textContent='Último check-in: '+checkins[0].dia;
 }catch(e){$('v9CheckinStatus').textContent=e.message;}
}
$('v9CheckinForm').onsubmit=async e=>{e.preventDefault();try{await request('/api/v9/meu-checkin',{method:'PUT',body:JSON.stringify({dia:$('v9CheckinDate').value,sono:$('v9Sleep').value,cansaco:Number($('v9Fatigue').value),dor:$('v9Pain').checked,observacao:$('v9CheckinNote').value.trim()||null})});$('v9CheckinStatus').textContent='Check-in salvo. Se estiver com dor, avise seu responsável e treinador.';}catch(err){$('v9CheckinStatus').textContent=err.message;}};
async function v9CoachLoad(){
 if(role!=='treinador')return; $('v9Library').replaceChildren();
 try{const exercises=await request('/api/v9/biblioteca');for(const x of exercises)v9Line('v9Library',`${x.nome} — ${x.objetivo}. ${x.instrucoes}`);await v9ReportLoad();}catch(e){$('v9CoachStatus').textContent=e.message;}
}
async function v9ReportLoad(){
 const id=Number($('taskAthlete').value);$('v9Report').replaceChildren();
 if(!id){$('v9CoachStatus').textContent='Selecione um atleta na aba Atividades, depois volte aqui.';return;}
 try{const r=await request('/api/v9/atletas/'+id+'/relatorio');v9Line('v9Report',`Últimos 7 dias: ${r.tarefas_concluidas}/${r.tarefas_total} tarefas concluídas; ${r.dias_habitos} dias com hábitos registrados.`);
 for(const c of r.checkins)v9Line('v9Report',`${c.dia} · Sono: ${c.sono} · Cansaço: ${c.cansaco}/5 · Dor: ${c.dor?'SIM — conversar com o atleta':'não informada'}`);
 for(const a of r.avaliacoes)v9Line('v9Report',`${a.dia} · ${a.fundamento}: ${a.nota}/5`);
 $('v9CoachStatus').textContent='Relatório atualizado.';}catch(e){$('v9CoachStatus').textContent=e.message;}
}
$('v9RefreshReport').onclick=v9ReportLoad;
$('v9AssessmentForm').onsubmit=async e=>{e.preventDefault();const atleta_id=Number($('taskAthlete').value);if(!atleta_id){$('v9CoachStatus').textContent='Selecione um atleta na aba Atividades.';return;}try{await request('/api/v9/avaliacoes',{method:'POST',body:JSON.stringify({atleta_id,dia:$('v9AssessmentDate').value,fundamento:$('v9Skill').value,nota:Number($('v9Score').value),observacao:$('v9AssessmentNote').value.trim()||null})});$('v9CoachStatus').textContent='Avaliação registrada.';await v9ReportLoad();}catch(e){$('v9CoachStatus').textContent=e.message;}};

// V10: interface por perfil; o backend verifica vínculos e autorização.
function v10Item(target,title,desc){const d=document.createElement('article');d.className='v10-card';const h=document.createElement('strong');h.textContent=title;const p=document.createElement('p');p.textContent=desc;d.append(h,p);$(target).append(d);}
async function v10LoadDay(){if(role!=='atleta')return;$('v10DayCards').replaceChildren();try{const d=await request('/api/v10/meu-dia');$('v10AthleteStatus').textContent='Hoje: '+d.dia+' · Check-in: '+(d.checkin_preenchido?'registrado':'pendente')+' · Hábitos: '+(d.habitos_preenchidos?'registrados':'pendentes');for(const x of d.sugestoes)v10Item('v10DayCards',x.titulo,x.texto);for(const t of d.tarefas)v10Item('v10DayCards',(t.concluida?'✅ ':'📋 ')+t.titulo,t.descricao);if(!d.tarefas.length)v10Item('v10DayCards','Sem tarefas extras','O treinador ainda não programou atividades para hoje. Não acrescente treinos por conta própria.');}catch(e){$('v10AthleteStatus').textContent=e.message;}}
$('v10RefreshDay').onclick=v10LoadDay;
async function v10LoadCoach(){if(role!=='treinador')return;try{const es=await request('/api/v4/equipes');const el=$('v10Team'),selected=el.value;el.replaceChildren(new Option('Selecione a equipe',''));es.forEach(e=>el.add(new Option(e.nome+' · '+e.categoria,e.id)));if(es.some(e=>String(e.id)===selected))el.value=selected;else if(es.length)el.value=String(es[0].id);await v10TeamChanged();}catch(e){$('v10CoachStatus').textContent=e.message;}}
async function v10TeamChanged(){const id=$('v10Team').value;const t=$('v10Target');t.replaceChildren(new Option('Equipe inteira',''));$('v10Agenda').replaceChildren();if(!id)return;try{const athletes=await request('/api/v4/equipes/'+id+'/atletas');athletes.forEach(a=>t.add(new Option(a.nome,a.id)));await v10Agenda();}catch(e){$('v10CoachStatus').textContent=e.message;}}
$('v10Team').onchange=v10TeamChanged;
async function v10Agenda(){const id=$('v10Team').value;if(!id)return;$('v10Agenda').replaceChildren();try{const [rows,r]=await Promise.all([request('/api/v10/equipes/'+id+'/agenda'),request('/api/v10/equipes/'+id+'/resumo')]);v10Item('v10Agenda','Resumo de hoje',`${r.checkins_hoje}/${r.atletas_autorizados} check-ins; ${r.checkins_que_pedem_conversa} registros pedem conversa.`);for(const e of rows)v10Item('v10Agenda',e.dia+' · '+e.titulo,e.tipo.toUpperCase()+' — '+e.detalhes);if(!rows.length)v10Item('v10Agenda','Agenda vazia','Cadastre o primeiro planejamento.');}catch(e){$('v10CoachStatus').textContent=e.message;}}
$('v10RefreshAgenda').onclick=v10Agenda;
$('v10Date').value=v9Today();
$('v10PlanForm').onsubmit=async e=>{e.preventDefault();const b=e.submitter;if(b)b.disabled=true;try{const body={equipe_id:Number($('v10Team').value),atleta_id:$('v10Target').value?Number($('v10Target').value):null,dia:$('v10Date').value,tipo:$('v10Type').value,titulo:$('v10Title').value.trim(),detalhes:$('v10Details').value.trim()};const result=await request('/api/v10/planejar',{method:'POST',body:JSON.stringify(body)});$('v10CoachStatus').textContent='Planejamento enviado para '+result.destinatarios+' atleta(s).';await v10Agenda();}catch(err){$('v10CoachStatus').textContent=err.message;}finally{if(b)b.disabled=false;}};
