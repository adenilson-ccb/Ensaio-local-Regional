# Ensaio Local

App novo, separado do original, usado só para Ensaio (sem vínculo com Culto
de Jovens). Mesmo conceito de contagem (irmandade, cordas/madeiras/metais/
harmônico, organistas, hinos ensaiados, histórico e relatório mensal por
músico) — mas com repositório, banco e link próprios.

## Estrutura
- `app.py` — telas do app (Novo Registro, Histórico, Relatório Mensal, Cadastro)
- `db.py` — funções de acesso ao banco Turso
- `schema.sql` — criação das tabelas
- `requirements.txt` — dependências Python
- `.streamlit/secrets.toml.example` — modelo das credenciais (não subir o real)

## Passo a passo para colocar no ar

1. **Criar repositório novo no GitHub** e subir esses arquivos.
2. **Criar um banco novo no Turso** (`turso db create ensaio-novo` ou pelo painel).
   Pegue a URL (`turso db show ensaio-novo --url`) e o token
   (`turso db tokens create ensaio-novo`).
3. **Deploy no Streamlit Community Cloud**: New app → selecione o repositório
   novo → arquivo principal `app.py`.
4. Em **Manage app > Settings > Secrets**, cole o conteúdo de
   `secrets.toml.example` já preenchido com a URL/token do Turso e a senha
   escolhida para as 6 pessoas.
5. Ao abrir o app pela primeira vez, ele mesmo cria as tabelas no banco
   (`db.init_db()`).
6. Cadastre os músicos/organistas na aba **Cadastro** — isso é o que permite
   o Relatório Mensal mostrar presença por nome.

## O que ainda falta ajustar (avisar quais campos quer mudar)
- Campos de "Recitativos" (Irmãs/Irmãos, 1ª/2ª/3ª Fileira) e distinção
  Músicos/Organistas RJM vs Casados(as) ainda não estão nessa versão —
  dá pra adicionar depois.
- Login é com senha única (sem usuário individual), como decidido antes.
