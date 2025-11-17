# 🚀 Guia de Execução Completo

Este guia mostra como rodar todo o sistema Golpe Detector.

## 📋 Pré-requisitos

- Docker e Docker Compose instalados
- Node.js 16+ (para admin e mobile)
- Python 3.11+ (opcional, se rodar localmente)

## 🎯 Opção 1: Execução Rápida (Recomendado)

### Windows:
```bash
start-all.bat
```

### Linux/Mac:
```bash
chmod +x start-all.sh
./start-all.sh
```

## 🎯 Opção 2: Execução Manual Passo a Passo

### 1️⃣ Subir Infraestrutura (PostgreSQL + Redis + Backend)

```bash
docker-compose up -d
```

Verificar se está rodando:
```bash
docker ps
```

Você deve ver:
- `postgres` na porta 5432
- `redis` na porta 6379
- `backend` na porta 8000

### 2️⃣ Verificar Backend

Acesse no navegador:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs

Você deve ver:
```json
{
  "status": "online",
  "mensagem": "Sistema de proteção educacional ativo."
}
```

### 3️⃣ Iniciar Worker (Terminal 2)

O worker processa as análises de URLs:

```bash
docker exec -it backend bash
rq worker
```

Você verá mensagens como:
```
*** Listening for work on default...
```

**Mantenha este terminal aberto!**

### 4️⃣ Iniciar Painel Admin (Terminal 3)

```bash
cd admin
npm install
npm run dev
```

Acesse: **http://localhost:3000**

### 5️⃣ (Opcional) Iniciar App Mobile (Terminal 4)

```bash
cd mobile
npm install
npm start
```

Escaneie o QR code com o Expo Go no celular.

## 🧪 Testar o Sistema

### Teste 1: Enviar URL para Análise

```bash
curl -X POST "http://localhost:8000/submit" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://exemplo.com", "user_id": 1}'
```

Resposta esperada:
```json
{
  "job_id": "abc-123-def",
  "status": "enfileirado",
  "submission_id": 1
}
```

### Teste 2: Verificar Resultado

Use o `job_id` retornado:

```bash
curl "http://localhost:8000/submission/{job_id}"
```

### Teste 3: Ver no Painel Admin

1. Acesse http://localhost:3000
2. Vá para "Submissões"
3. Você verá a análise processada

## 📊 Verificar Status dos Serviços

### Ver logs do backend:
```bash
docker logs backend
```

### Ver logs do worker:
O worker mostra logs diretamente no terminal onde está rodando.

### Verificar fila Redis:
```bash
docker exec -it redis redis-cli
> KEYS *
> LLEN rq:queue:default
```

### Verificar banco de dados:
```bash
docker exec -it postgres psql -U appuser -d protecao
```

No psql:
```sql
SELECT COUNT(*) FROM submissions;
SELECT * FROM submissions ORDER BY created_at DESC LIMIT 5;
```

## 🐛 Problemas Comuns

### Backend não inicia

```bash
# Ver logs
docker logs backend

# Reconstruir
docker-compose build backend
docker-compose up -d backend
```

### Worker não processa jobs

1. Verifique se Redis está rodando: `docker ps | grep redis`
2. Verifique se o worker está conectado (deve mostrar "Listening for work")
3. Verifique logs: `docker logs backend`

### Painel admin não conecta

1. Verifique se o backend está rodando: http://localhost:8000
2. Verifique o console do navegador (F12) para erros
3. Confirme que a URL da API está correta em `admin/src/services/api.js`

### Porta já em uso

Se alguma porta estiver ocupada:

```bash
# Ver o que está usando a porta
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/Mac

# Ou altere as portas no docker-compose.yml
```

## 🛑 Parar o Sistema

```bash
# Parar todos os serviços
docker-compose down

# Parar e remover volumes (CUIDADO: apaga dados)
docker-compose down -v
```

## 📝 Próximos Passos

1. ✅ Sistema rodando
2. ✅ Worker processando análises
3. ✅ Painel admin visualizando dados
4. 🎯 Testar com URLs reais
5. 🎯 Adicionar mais casos de treino
6. 🎯 Configurar autenticação

## 🎉 Tudo Funcionando?

Se tudo estiver OK, você terá:

- ✅ Backend rodando em http://localhost:8000
- ✅ Worker processando jobs
- ✅ Painel admin em http://localhost:3000
- ✅ Banco de dados criado automaticamente
- ✅ Análises sendo processadas e salvas

**Boa sorte! 🚀**

