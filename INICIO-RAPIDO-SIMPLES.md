# ⚡ Início Rápido - 3 Passos

## 1️⃣ Iniciar Docker Desktop
- Abra o Docker Desktop
- Aguarde até aparecer "Docker is running"

## 2️⃣ Executar Comandos

```bash
# Subir serviços
docker-compose up -d

# Aguardar 10 segundos
timeout /t 10

# Iniciar worker
docker exec -d backend rq worker

# Abrir página
start verify.html
```

## 3️⃣ Testar

Abra no navegador: `http://localhost:8000/health`

Pronto! 🎉

