# ⚡ Início Rápido - Golpe Detector

## 🚨 IMPORTANTE: Antes de Começar

1. **Inicie o Docker Desktop** (se estiver no Windows/Mac)
2. Aguarde até que o Docker esteja totalmente iniciado
3. Verifique se está rodando: `docker ps` (não deve dar erro)

## 🚀 Passo a Passo Rápido

### 1. Iniciar Docker Desktop
- Windows: Procure "Docker Desktop" no menu iniciar
- Mac: Abra Docker Desktop do Applications
- Linux: Docker geralmente já está rodando como serviço

### 2. Subir Serviços

**Windows:**
```bash
start-all.bat
```

**Linux/Mac:**
```bash
chmod +x start-all.sh
./start-all.sh
```

**Ou manualmente:**
```bash
docker-compose up -d
```

### 3. Verificar se Subiu

```bash
docker ps
```

Você deve ver 3 containers:
- `postgres`
- `redis`  
- `backend`

### 4. Testar Backend

Abra no navegador: http://localhost:8000

Deve aparecer:
```json
{
  "status": "online",
  "mensagem": "Sistema de proteção educacional ativo."
}
```

### 5. Iniciar Worker

Em um **NOVO terminal**:

```bash
docker exec -it backend bash
rq worker
```

Mantenha este terminal aberto!

### 6. Iniciar Painel Admin

Em **OUTRO terminal**:

```bash
cd admin
npm install
npm run dev
```

Acesse: http://localhost:3000

### 7. Testar Enviando uma URL

Em **OUTRO terminal**:

```bash
curl -X POST "http://localhost:8000/submit" -H "Content-Type: application/json" -d "{\"url\": \"https://google.com\", \"user_id\": 1}"
```

Ou use o Postman/Insomnia:
- POST http://localhost:8000/submit
- Body (JSON):
```json
{
  "url": "https://google.com",
  "user_id": 1
}
```

## ✅ Checklist

- [ ] Docker Desktop rodando
- [ ] `docker ps` mostra 3 containers
- [ ] Backend responde em http://localhost:8000
- [ ] Worker rodando (terminal com "Listening for work")
- [ ] Painel admin em http://localhost:3000
- [ ] Teste de envio de URL funcionando

## 🐛 Problemas?

### "Docker não está rodando"
→ Inicie o Docker Desktop e aguarde alguns segundos

### "Porta já em uso"
→ Altere as portas no `docker-compose.yml` ou pare o serviço que está usando

### "Backend não inicia"
→ Verifique logs: `docker logs backend`

### "Worker não processa"
→ Verifique se Redis está rodando: `docker ps | grep redis`

## 📚 Mais Detalhes

Veja o arquivo `GUIA-EXECUCAO.md` para instruções completas.

