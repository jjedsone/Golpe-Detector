# 🚀 Guia Completo para Rodar o Projeto

## 📋 Pré-requisitos

1. **Docker Desktop** instalado e rodando
2. **Node.js** (para o painel admin - opcional)
3. **Python 3.11+** (para desenvolvimento local - opcional)

## 🔧 Passo 1: Iniciar Docker Desktop

Certifique-se de que o Docker Desktop está rodando:
- Windows: Abra o Docker Desktop
- Verifique se o ícone do Docker está na bandeja do sistema

## 🐳 Passo 2: Subir os Serviços

### Opção A: Usando Docker Compose (Recomendado)

```bash
# Subir todos os serviços
docker-compose up -d

# Verificar status
docker-compose ps

# Ver logs
docker-compose logs -f
```

### Opção B: Usando Scripts

**Windows:**
```bash
start-all.bat
```

**Linux/Mac:**
```bash
chmod +x start-all.sh
./start-all.sh
```

## ⚙️ Passo 3: Verificar se os Serviços Estão Rodando

```bash
# Verificar containers
docker ps

# Você deve ver:
# - postgres (porta 5432)
# - redis (porta 6379)
# - backend (porta 8000)
```

## 🔨 Passo 4: Rodar o Worker

O worker processa as análises em background. Abra um novo terminal:

```bash
# Entrar no container do backend
docker exec -it backend bash

# Rodar o worker
rq worker
```

Ou em um terminal separado (sem entrar no container):

```bash
docker exec -it backend rq worker
```

## ✅ Passo 5: Verificar se Está Funcionando

### Testar API

```bash
# Verificar status
curl http://localhost:8000/

# Verificar health
curl http://localhost:8000/health

# Testar verificação de link
curl "http://localhost:8000/verify/https://example.com"
```

### Abrir Página Web

Abra o arquivo `verify.html` no navegador:
- Windows: `start verify.html`
- Linux/Mac: `open verify.html` ou `xdg-open verify.html`

## 🖥️ Passo 6: Rodar Painel Admin (Opcional)

```bash
cd admin
npm install
npm run dev
```

Acesse: `http://localhost:3000`

## 📱 Passo 7: Rodar App Mobile (Opcional)

```bash
cd mobile
npm install
npx expo start
```

## 🛠️ Comandos Úteis

### Parar todos os serviços
```bash
docker-compose down
```

### Parar e remover volumes (limpar dados)
```bash
docker-compose down -v
```

### Reconstruir containers
```bash
docker-compose build --no-cache
docker-compose up -d
```

### Ver logs do backend
```bash
docker logs -f backend
```

### Ver logs do postgres
```bash
docker logs -f postgres
```

### Ver logs do redis
```bash
docker logs -f redis
```

### Acessar banco de dados
```bash
docker exec -it postgres psql -U appuser -d protecao
```

### Reiniciar um serviço específico
```bash
docker-compose restart backend
```

## 🐛 Troubleshooting

### Docker não está rodando
- Abra o Docker Desktop
- Aguarde até aparecer "Docker is running"

### Porta já em uso
```bash
# Verificar o que está usando a porta
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000
```

### Erro ao construir backend
```bash
# Reconstruir sem cache
docker-compose build --no-cache backend
docker-compose up -d backend
```

### Worker não processa jobs
```bash
# Verificar se Redis está rodando
docker ps | grep redis

# Verificar fila
docker exec -it backend python -c "from rq import Queue; import redis; r = redis.from_url('redis://redis:6379/0'); q = Queue(connection=r); print(f'Jobs na fila: {len(q)}')"
```

### Banco de dados não inicializa
```bash
# Verificar se tabelas foram criadas
docker exec -it postgres psql -U appuser -d protecao -c "\dt"

# Se não existirem, executar script
docker exec -i postgres psql -U appuser -d protecao < backend/init_schema.sql
```

## 📊 Verificar Status Completo

```bash
# Status dos containers
docker-compose ps

# Health check da API
curl http://localhost:8000/health

# Métricas
curl http://localhost:8000/metrics

# Estatísticas
curl http://localhost:8000/stats
```

## 🎯 Checklist de Inicialização

- [ ] Docker Desktop rodando
- [ ] `docker-compose up -d` executado
- [ ] Todos os containers rodando (`docker ps`)
- [ ] Worker rodando (`docker exec -it backend rq worker`)
- [ ] API respondendo (`curl http://localhost:8000/`)
- [ ] Health check OK (`curl http://localhost:8000/health`)
- [ ] Página verify.html aberta no navegador
- [ ] Painel admin rodando (opcional)
- [ ] App mobile rodando (opcional)

## 🚀 Início Rápido (Um Comando)

```bash
# Windows
docker-compose up -d && timeout /t 5 && docker exec -d backend rq worker && start verify.html

# Linux/Mac
docker-compose up -d && sleep 5 && docker exec -d backend rq worker && open verify.html
```

