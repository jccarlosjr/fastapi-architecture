# 🚀 FastAPI Minimal Architecture (fast-api-min)

Uma arquitetura de backend extremamente robusta, altamente abstrata e orientada a objetos desenvolvida em cima do **FastAPI**, **SQLAlchemy (Async)**, **PostgreSQL** e **Redis**.

O projeto elimina o boilerplate comum do FastAPI através de uma camada genérica e flexível para CRUDs, tratamento automatizado de exceções, esquemas dinâmicos no Pydantic, controle granular de acessos (RBAC) e segurança a nível corporativo.

---

## 🛠️ Tecnologias Principais

- **Core**: Python 3.11, FastAPI.
- **Banco de Dados**: PostgreSQL (Engine assíncrona do SQLAlchemy 2.0) & Alembic para migrações.
- **Cache & Rate-Limit**: Redis.
- **Segurança**: JWT Auth com rotação de tokens opacos salvos no Redis, Progressive Backoff contra ataques de força bruta, e Headers de Segurança OWASP.
- **Ambiente**: Docker & Docker Compose.

---

## 📁 Estrutura de Diretórios

```bash
├── app/
│   ├── api/                  # Roteador principal e gerenciador de versões
│   ├── core/
│   │   ├── generics/         # Abstrações base: Modelos, Repositórios, Serviços e Views
│   │   ├── config.py         # Configurações globais (Pydantic Settings)
│   │   ├── exceptions.py     # Gerenciamento orientado a objetos de exceções
│   │   ├── middlewares.py    # Log de requisições, headers OWASP e rate limiters
│   │   ├── mixins.py         # Mixins de segurança (LoginRequired, StaffRequired, etc)
│   │   └── security.py       # Utilidades criptográficas e geração de tokens
│   ├── db/                   # Inicialização de sessão e pool assíncrono (SQLAlchemy / Redis)
│   └── modules/              # Módulos de domínio (Regras de negócio isoladas)
│       ├── accounts/         # Cadastro e edição de usuários
│       ├── auth/             # Login, logout e rotação de tokens
│       ├── groups/           # Perfis/Grupos de acesso
│       └── permissions/      # Permissões do sistema (RBAC)
```

---

## 🚀 Como Iniciar o Projeto

### Pré-requisitos
- Docker & Docker Compose instalados.

### Passos para execução:

1. **Clonar o Repositório e Configurar Variáveis**:
   Crie o arquivo `.env` com base nas variáveis do projeto:
   ```env
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   POSTGRES_DB=app_db
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/app_db
   REDIS_URL=redis://redis:6379/0
   SECRET_KEY=sua_secret_key_super_segura
   ```

2. **Subir os Containers**:
   Execute o Docker Compose para baixar as imagens, criar os bancos e iniciar o servidor Uvicorn:
   ```bash
   docker compose up -d --build
   ```

3. **Inicializar o Banco de Dados (CLI de Gerenciamento)**:
   Como o banco é iniciado vazio e as permissões de acesso são protegidas por RBAC, você deve semear as permissões básicas e criar o primeiro usuário administrador interativamente:
   ```bash
   # Cadastrar as permissões CRUD padrão para os modelos
   docker compose exec web python cli.py seed-permissions

   # Criar o primeiro superusuário interativamente
   docker compose exec web python cli.py createsuperuser
   ```

4. **Verificar os Logs**:
   ```bash
   docker compose logs -f web
   ```

5. **Acessar a API**:
   - API Docs (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)
   - Diagnostic Health Check: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
   - ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🧪 Rodando os Testes Automatizados

Você pode executar a suíte de testes com o `pytest` diretamente dentro do container web:
```bash
docker compose exec web env PYTHONPATH=. pytest
```

---

## 📖 Documentação Completa

Para uma análise detalhada da arquitetura do projeto, padrões de design orientados a objetos adotados, funcionamento da camada genérica de views, controle de acesso e segurança, acesse o arquivo:

👉 **[DOCUMENTATION.md](DOCUMENTATION.md)**
