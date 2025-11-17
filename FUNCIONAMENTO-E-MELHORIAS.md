# 📖 Como Funciona o Projeto - Análise Completa

## 🎯 Visão Geral

O **Golpe Detector** é um sistema educacional que analisa URLs suspeitas e ensina usuários a identificar golpes online. O sistema funciona de forma assíncrona usando filas de processamento.

---

## 🔄 Fluxo Completo de Funcionamento

### 1️⃣ **Envio da URL** (Cliente → Backend)

```
Usuário (Mobile/Web) → POST /submit → Backend FastAPI
```

**O que acontece:**
1. Usuário envia URL via app mobile ou API
2. Backend valida a URL
3. Cria registro no banco com status `queued`
4. Gera um `job_id` único (UUID)
5. Enfileira o job no Redis
6. Retorna `job_id` imediatamente ao cliente

**Código:** `backend/main.py` - função `submit()`

### 2️⃣ **Processamento Assíncrono** (Worker)

```
Redis Queue → Worker RQ → Playwright → Análise → Banco de Dados
```

**O que acontece:**
1. Worker RQ pega o job da fila
2. Atualiza status para `processing`
3. Executa análise completa:
   - Verifica certificado TLS/SSL
   - Detecta typosquatting
   - Abre página com Playwright (headless browser)
   - Analisa formulários, scripts, redirecionamentos
4. Calcula score de risco (0-100)
5. Classifica: baixo (<20), médio (20-49), alto (≥50)
6. Gera dicas pedagógicas
7. Salva resultado no banco
8. Atualiza status para `done`

**Código:** `backend/worker.py` - função `analyze_url()`

### 3️⃣ **Consulta do Resultado** (Cliente → Backend)

```
Cliente → GET /submission/{job_id} → Backend → Banco → Resultado
```

**O que acontece:**
1. Cliente consulta resultado usando `job_id`
2. Backend busca no banco de dados
3. Retorna status e resultado completo

**Código:** `backend/main.py` - função `get_submission()`

---

## 🏗️ Arquitetura do Sistema

```
┌─────────────┐
│   Mobile    │  React Native/Expo
│     App     │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────────────────────────┐
│      Backend (FastAPI)          │
│  ┌───────────────────────────┐  │
│  │  POST /submit             │  │
│  │  GET /submission/{id}     │  │
│  │  GET /submissions         │  │
│  │  GET /stats               │  │
│  └───────────────────────────┘  │
└──────┬──────────────┬───────────┘
       │              │
       ▼              ▼
┌──────────┐    ┌──────────┐
│  Redis   │    │PostgreSQL│
│  (Fila)  │    │  (Dados) │
└────┬─────┘    └──────────┘
     │
     ▼
┌─────────────────┐
│  Worker (RQ)    │
│  ┌───────────┐  │
│  │ Playwright│  │
│  │ Análise   │  │
│  └───────────┘  │
└─────────────────┘
       │
       ▼
┌──────────┐
│PostgreSQL│
│ (Salva)  │
└──────────┘
```

---

## 🔍 Heurísticas de Detecção (Como Funciona)

### 1. **Verificação TLS/SSL** (Score: +30)
```python
# Verifica se certificado é válido
- Conecta na porta 443
- Verifica se certificado é de uma CA confiável
- Detecta certificados autoassinados
```

### 2. **Typosquatting** (Score: +40)
```python
# Compara domínio com lista de oficiais
- Calcula distância de Levenshtein
- Se distância ≤ 2 e > 0: suspeito
- Exemplo: "itau.com.br" vs "itauu.com.br"
```

### 3. **Formulários Suspeitos** (Score: +40)
```python
# Analisa campos de formulário
- Detecta campos de senha
- Procura por: "pass", "senha", "cpf", "pin"
- Identifica solicitação de dados sensíveis
```

### 4. **Auto-Submit** (Score: +10)
```python
# Verifica JavaScript
- Procura por: form.submit(), document.forms
- Detecta envio automático de formulários
```

### 5. **Redirecionamentos Múltiplos** (Score: +15)
```python
# Conta redirecionamentos HTTP
- Se > 2 redirecionamentos: suspeito
- Pode esconder destino real
```

### 6. **Scripts Ofuscados** (Score: +10)
```python
# Analisa código JavaScript
- Procura por: atob(), btoa(), eval(), unescape()
- Código ofuscado é sinal de golpe
```

### 7. **Título Suspeito** (Score: +5)
```python
# Analisa título da página
- Se contém "login" mas não "banco/oficial"
- Página genérica de login é suspeita
```

---

## 📊 Classificação de Risco

```
Score 0-19   → Risco BAIXO   🟢
Score 20-49  → Risco MÉDIO   🟠
Score 50+    → Risco ALTO    🔴
```

---

## 🎓 Componente Educacional

Após detectar golpes, o sistema:
1. **Gera dicas pedagógicas** baseadas nos sinais encontrados
2. **Oferece quiz interativo** no app mobile
3. **Ensina o que evitar** em situações similares

---

## ⚠️ Pontos que Precisam de Melhoria

### 🔴 **CRÍTICOS**

#### 1. **Falta de Tratamento de Erros no Worker**
**Problema:** Se o worker falhar, o status fica `processing` para sempre.

**Solução:**
```python
# Adicionar try/except e atualizar status para 'failed'
try:
    result = analyze_url(...)
except Exception as e:
    update_status(job_id, 'failed', error=str(e))
```

#### 2. **Sem Timeout no Worker**
**Problema:** Jobs podem ficar travados indefinidamente.

**Solução:**
```python
# No RQ, adicionar timeout
q.enqueue("worker.analyze_url", ..., job_timeout=300)  # 5 minutos
```

#### 3. **Conexões de Banco Não Reutilizadas**
**Problema:** Cada requisição cria nova conexão (ineficiente).

**Solução:**
```python
# Usar connection pooling
from psycopg2 import pool
connection_pool = pool.SimpleConnectionPool(1, 20, DATABASE_URL)
```

#### 4. **Sem Validação de URL Maliciosa**
**Problema:** Sistema pode ser usado para atacar outros sites.

**Solução:**
```python
# Validar URLs permitidas
ALLOWED_DOMAINS = ['exemplo.com']
BLOCKED_IPS = ['127.0.0.1', 'localhost']
```

### 🟠 **IMPORTANTES**

#### 5. **Falta de Autenticação**
**Problema:** Qualquer um pode usar a API.

**Solução:**
- Implementar JWT
- Rate limiting por IP
- API keys para clientes

#### 6. **Sem Rate Limiting**
**Problema:** Usuário pode sobrecarregar o sistema.

**Solução:**
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post("/submit")
@limiter.limit("10/minute")
def submit(...):
```

#### 7. **Logs Insuficientes**
**Problema:** Difícil debugar problemas.

**Solução:**
```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info(f"Job {job_id} iniciado")
```

#### 8. **Sem Cache de Resultados**
**Problema:** Mesma URL é analisada múltiplas vezes.

**Solução:**
```python
# Verificar se URL já foi analisada
cached = get_cached_result(url)
if cached:
    return cached
```

#### 9. **Lista de Domínios Oficiais Hardcoded**
**Problema:** Difícil manter e atualizar.

**Solução:**
- Mover para banco de dados
- Endpoint para adicionar/remover
- Importar de fonte externa

#### 10. **Sem Monitoramento**
**Problema:** Não sabemos se sistema está funcionando.

**Solução:**
- Health checks mais detalhados
- Métricas (Prometheus)
- Alertas (quando worker para)

### 🟡 **MELHORIAS**

#### 11. **Interface do Painel Admin Básica**
**Melhoria:**
- Adicionar busca
- Paginação
- Exportar dados
- Filtros avançados

#### 12. **App Mobile Precisa de Melhorias**
**Melhoria:**
- Histórico de análises
- Compartilhar resultado
- Notificações push
- Modo offline

#### 13. **Falta de Testes**
**Melhoria:**
- Testes unitários
- Testes de integração
- Testes E2E

#### 14. **Documentação da API**
**Melhoria:**
- Swagger/OpenAPI completo
- Exemplos de uso
- Códigos de erro documentados

#### 15. **Segurança do Playwright**
**Melhoria:**
- Sandbox mais isolado
- Limites de recursos (CPU, memória)
- Timeout mais agressivo
- Bloquear requisições externas

---

## ✅ Pontos Fortes do Projeto

1. ✅ **Arquitetura assíncrona** bem implementada
2. ✅ **Separação de responsabilidades** clara
3. ✅ **Múltiplas heurísticas** de detecção
4. ✅ **Componente educacional** integrado
5. ✅ **Painel admin** funcional
6. ✅ **Containerização** com Docker
7. ✅ **Banco de dados** bem estruturado

---

## 🎯 Prioridades de Melhoria

### **Fase 1 - Estabilidade (Urgente)**
1. Tratamento de erros no worker
2. Timeout nos jobs
3. Connection pooling
4. Validação de URLs

### **Fase 2 - Segurança (Importante)**
5. Autenticação JWT
6. Rate limiting
7. Logs estruturados
8. Sandbox mais seguro

### **Fase 3 - Performance (Desejável)**
9. Cache de resultados
10. Otimização de queries
11. Monitoramento
12. Métricas

### **Fase 4 - Features (Futuro)**
13. Machine Learning
14. Integração com VirusTotal
15. API pública
16. Notificações

---

## 📝 Resumo

O projeto está **funcional e bem estruturado**, mas precisa de melhorias em:
- **Estabilidade** (tratamento de erros)
- **Segurança** (autenticação, rate limiting)
- **Performance** (cache, pooling)
- **Monitoramento** (logs, métricas)

A base está sólida, agora é evoluir para produção! 🚀

