# 🚀 Guia Rápido de Início

## Passo a Passo para Rodar o MVP

### 1. Subir Infraestrutura (PostgreSQL + Redis)

```bash
docker-compose up -d
```

Verifique se está rodando:
```bash
docker ps
```

### 2. Configurar Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Criar Tabelas no Banco

```bash
# Ainda no diretório backend, com venv ativado
python -c "from database import engine, Base; from models import *; Base.metadata.create_all(bind=engine)"
```

### 4. Popular Casos de Treino (Opcional)

```bash
python seed_training_cases.py
```

### 5. Iniciar Backend API

```bash
# No diretório backend, com venv ativado
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Acesse: http://localhost:8000/docs

### 6. Configurar e Iniciar Worker

Em outro terminal:

```bash
cd worker
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
playwright install chromium
python worker.py
```

### 7. Configurar App Mobile

Em outro terminal:

```bash
cd mobile
npm install
npm start
```

No app Expo Go (celular), escaneie o QR code ou pressione:
- `a` para Android
- `i` para iOS

### 8. Testar

1. No app mobile, cole uma URL suspeita
2. Aguarde a análise (pode levar alguns segundos)
3. Veja o resultado com nível de risco e dicas
4. Clique em "Treinar" para fazer o quiz

## 🧪 Testar API Diretamente

```bash
# Enviar URL para análise
curl -X POST "http://localhost:8000/api/v1/submit" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://exemplo-suspeito.com"}'

# Verificar resultado (use o job_id retornado)
curl "http://localhost:8000/api/v1/submission/{job_id}"
```

## ⚠️ Problemas Comuns

### Worker não processa jobs
- Verifique se Redis está rodando: `docker ps`
- Verifique logs do worker
- Certifique-se que Playwright está instalado

### Erro de conexão com banco
- Verifique se PostgreSQL está rodando: `docker ps`
- Confirme credenciais no `.env` (ou use as padrões do docker-compose.yml)

### App não conecta ao backend
- Altere `API_BASE_URL` em `mobile/App.js` para o IP da sua máquina
- Exemplo: `const API_BASE_URL = 'http://192.168.1.100:8000';`
- Certifique-se que backend está acessível na rede local

## 📝 Próximos Passos

- [ ] Adicionar autenticação JWT
- [ ] Criar painel web admin
- [ ] Adicionar mais heurísticas de detecção
- [ ] Coletar mais casos reais de golpes
- [ ] Implementar testes automatizados

