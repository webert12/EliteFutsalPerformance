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
      $("staffTools").classList.toggle("hidden",!staff);
      $("roleHelp").textContent=staff?"Você pode consultar os atletas cadastrados no sistema.":"Sua conta está ativa. O acompanhamento individual será liberado quando a equipe vincular seu cadastro de atleta.";
      $("auth").classList.add("hidden");$("profile").classList.remove("hidden");
      $("password").value="";
      $("profile").scrollIntoView({behavior:"smooth"});
      if(staff)await loadAthletes();
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
  token=null;role=null;
  $("profile").classList.add("hidden");$("athletesList").replaceChildren();
  $("form").reset();
  if(showLogin)showAuth("login");
}
$("logout").onclick=()=>logout();
