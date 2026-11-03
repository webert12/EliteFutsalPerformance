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
      role=user.tipo_usuario;
      $("who").textContent="Olá, "+user.nome+"! Perfil: "+role+".";
      const staff=["administrador","treinador"].includes(role);
      $("adminTools").classList.toggle("hidden",role!=="administrador");
      $("staffTools").classList.toggle("hidden",!staff);
      $("roleHelp").textContent=staff?"Você pode consultar os atletas cadastrados no sistema.":"Sua conta está ativa. O acompanhamento individual será liberado quando a equipe vincular seu cadastro de atleta.";
      $("auth").classList.add("hidden");$("profile").classList.remove("hidden");
      $("password").value="";
      $("profile").scrollIntoView({behavior:"smooth"});
      if(staff)await loadAthletes();
      if(staff)await initV4();
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
  $("v4Tools").classList.add("hidden");token=null;role=null;$("adminTools").classList.add("hidden");
  $("profile").classList.add("hidden");$("athletesList").replaceChildren();
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
 $('v4TeamForm').classList.toggle('hidden',role!=='administrador');
 $('v4LinkBox').classList.toggle('hidden',role!=='administrador');
 $('v4Date').value=new Date().toLocaleDateString('en-CA');
 if(role==='administrador'){
  try{const ts=await request('/api/admin/treinadores');$('v4Trainer').replaceChildren(new Option('Selecione',''));ts.forEach(t=>$('v4Trainer').add(new Option(t.nome,String(t.id))));}catch(e){v4Msg(e.message);}
 }
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
  if(role==='administrador'){
   const all=await request('/api/atletas');const linked=new Set(athletes.map(a=>a.id));$('v4AthleteSelect').replaceChildren(new Option('Selecione',''));all.filter(a=>!linked.has(a.id)).forEach(a=>$('v4AthleteSelect').add(new Option('Ficha #'+a.id+' · '+a.posicao,String(a.id))));
  }
  await v4LoadAttendance();v4Msg(athletes.length+' atleta(s) nesta equipe.');
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
