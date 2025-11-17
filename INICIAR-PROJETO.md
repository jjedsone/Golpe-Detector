# 🚀 Como Iniciar o Projeto

## ⚠️ IMPORTANTE: Docker Desktop Precisa Estar Rodando

Antes de iniciar o projeto, você precisa:

1. **Abrir o Docker Desktop**
   - Procure por "Docker Desktop" no menu Iniciar
   - Aguarde até aparecer "Docker is running" na bandeja do sistema

2. **Verificar se está rodando**
   ```bash
   docker info
   ```
   Se aparecer informações do Docker, está OK. Se der erro, o Docker não está rodando.

## 📋 Passo a Passo

### Passo 1: Iniciar Docker Desktop

1. Abra o Docker Desktop
2. Aguarde até aparecer o ícone do Docker na bandeja do sistema
3. Verifique se está verde (rodando)

### Passo 2: Executar Script de Inicialização

**Windows:**
```bash
.\start-project.bat
```

**Ou manualmente:**
```bash
# 1. Subir serviços
docker-compose up -d

# 2. Aguardar alguns segundos
timeout /t 10

# 3. Verificar status
docker-compose ps

# 4. Iniciar worker
docker exec -d backend rq worker

# 5. Abrir página de verificação
start verify.html
```

### Passo 3: Verificar se Está Funcionando

```bash
# Testar API
curl http://localhost:8000/

# Health check
curl http://localhost:8000/health
```

## 🔍 Verificar Status

```bash
# Ver containers rodando
docker ps

# Ver logs
docker-compose logs -f

# Ver logs do backend
docker logs -f backend
```

## 🛑 Parar o Projeto

```bash
docker-compose down
```

## 🐛 Problemas Comuns

### Docker não inicia
- Reinicie o Docker Desktop
- Verifique se a virtualização está habilitada no BIOS
- Verifique se o WSL2 está instalado (Windows)

### Porta já em uso
```bash
# Ver o que está usando a porta 8000
netstat -ano | findstr :8000

# Parar o processo ou mudar a porta no docker-compose.yml
```

### Erro ao construir backend
```bash
# Reconstruir sem cache
docker-compose build --no-cache backend
docker-compose up -d backend
```

## 📞 Próximos Passos

Após iniciar:
1. ✅ Abra `verify.html` no navegador
2. ✅ Teste verificando um link
3. ✅ Acesse o painel admin (opcional)
4. ✅ Use o app mobile (opcional)

