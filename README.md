# Elite Futsal Performance — versão inicial 0.2

Sistema inicial em **FastAPI + SQLAlchemy + PostgreSQL**, preparado para GitHub e Render.

## O que já funciona
- Página inicial em `/`
- Documentação interativa em `/docs`
- Saúde do servidor e banco em `/health`
- Cadastro público **somente de atleta** em `POST /auth/cadastro`
- Login com JWT em `POST /auth/login`
- Usuário autenticado em `GET /auth/me`
- Cadastro/listagem de atletas por treinador/admin em `/api/atletas`
- Registros de sono, água, esforço, bem-estar e alimentação em `/api/atletas/{id}/registros`
- Orientações gerais em `GET /api/orientacoes/rotina`

## Configuração Render
1. No Render, mantenha o serviço **Web Service / Python** conectado ao repositório.
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Em **Environment**, configure `DATABASE_URL` (PostgreSQL persistente) e `SECRET_KEY` (string aleatória de 32+ caracteres). Defina `ENVIRONMENT=production`.
5. Faça deploy e abra `/health` e `/docs`.

**Não use SQLite em disco no Render**: arquivos locais podem desaparecer nos deploys/restarts. Use PostgreSQL persistente.

## Criar o primeiro administrador
Use um terminal seguro com as variáveis `DATABASE_URL`, `SECRET_KEY`, `ADMIN_EMAIL`, `ADMIN_PASSWORD` e `ADMIN_NAME` configuradas, e execute `python bootstrap_admin.py` **uma vez**. Não execute esse script como endpoint público nem registre a senha no GitHub. Não existe cadastro público de administrador/treinador. Novos treinadores precisarão de fluxo administrativo com auditoria, a ser implementado.

## Teste da API
1. `POST /auth/cadastro` com `{ "nome": "Atleta Teste", "email": "atleta@example.com", "senha": "uma-senha-longa-e-unica" }`.
2. `POST /auth/login` com email/senha. Copie `access_token`.
3. Na página `/docs`, clique **Authorize** e cole o token (sem a palavra Bearer, conforme solicitado pelo formulário).
4. `GET /auth/me` confirma seu login; `GET /api/orientacoes/rotina` mostra recomendações gerais.
5. Um administrador/treinador poderá cadastrar o perfil do atleta depois que o administrador for criado.

## Segurança e limitações
- A autenticação usa Argon2 e tokens JWT com expiração. Tokens não devem ser compartilhados.
- A versão ainda **não possui** consentimento dos responsáveis, verificação de e-mail, recuperação de senha, rate limiting, política de retenção de dados, trilha de auditoria nem migrações Alembic. **Não cadastre dados reais de menores antes de implementar esses controles e revisar a LGPD.**
- O cadastro público é somente para ambiente de demonstração. Antes de uso real, restringir a convites autorizados e aprovação do responsável.
- A criação automática de tabelas serve ao primeiro deploy, não altera tabelas existentes. Futuras alterações de esquema precisam de migrações.
- Orientações de nutrição e treino são educativas, não prescrições. Não calcula peso ideal, metas de emagrecimento, calorias individuais ou prontidão clínica para adolescentes.
- Se um `.env` com credenciais reais foi enviado ao GitHub, remova-o do repositório, **revogue/rotacione os segredos** e avalie limpeza do histórico Git. Adicionar `.gitignore` não apaga o histórico.
