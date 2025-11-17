# Sistema de Proteção Educacional contra Golpes

## 🚀 Início Rápido

### 1. Subir serviços

```bash
docker-compose up -d
```

### 2. Acessar backend

Abra no navegador:

```
http://localhost:8000
```

### 3. Enviar teste

POST em:

```
http://localhost:8000/submit
```

Body:

```json
{
  "url": "https://exemplo.com",
  "user_id": 1
}
```

### 4. Rodar o worker

Entre no backend:

```bash
docker exec -it backend bash
rq worker
```

### 5. Consultar resultado

GET em:

```
http://localhost:8000/submission/{job_id}
```

## 📋 Funcionalidades Implementadas

### Worker Completo
- ✅ Análise com Playwright (headless browser)
- ✅ Verificação de certificado TLS/SSL
- ✅ Detecção de typosquatting
- ✅ Análise de formulários suspeitos
- ✅ Detecção de auto-submit
- ✅ Verificação de redirecionamentos múltiplos
- ✅ Detecção de scripts ofuscados
- ✅ Classificação de risco (baixo/médio/alto)
- ✅ Geração de dicas pedagógicas

### API
- ✅ `POST /submit` - Enfileira análise
- ✅ `GET /submission/{job_id}` - Consulta resultado
- ✅ Persistência automática no banco
- ✅ Criação automática de tabelas

### Banco de Dados
- ✅ Tabela `submissions` criada automaticamente
- ✅ Armazenamento de resultados em JSONB
- ✅ Rastreamento de status (queued/processing/done)

## 🔍 Heurísticas de Detecção

O worker analisa:

1. **Certificado TLS** - Verifica se é válido ou autoassinado
2. **Typosquatting** - Compara com domínios oficiais conhecidos
3. **Formulários suspeitos** - Detecta campos de senha/CPF
4. **Auto-submit** - Identifica JavaScript que envia formulários automaticamente
5. **Redirecionamentos** - Conta múltiplos redirecionamentos
6. **Scripts ofuscados** - Detecta código JavaScript ofuscado
7. **Títulos suspeitos** - Identifica páginas de login genéricas

## 📊 Exemplo de Resultado

```json
{
  "url": "https://exemplo-suspeito.com",
  "job_id": "abc123",
  "checks": [
    {
      "name": "suspicious_form",
      "ok": false,
      "reason": "Formulário solicita credenciais/dados sensíveis"
    }
  ],
  "score": 40,
  "level": "médio",
  "tips": [
    "⚠️ A página solicita dados sensíveis (senha/CPF)..."
  ]
}
```

## 🐛 Troubleshooting

### Worker não processa jobs
- Verifique se Redis está rodando: `docker ps`
- Verifique logs: `docker logs backend`
- Certifique-se que Playwright está instalado (já incluído no Dockerfile)

### Erro de conexão com banco
- Verifique se PostgreSQL está rodando: `docker ps`
- O banco é criado automaticamente na primeira requisição

### Análise demora muito
- Alguns sites podem demorar para carregar
- Timeout padrão: 30 segundos
- Verifique logs do worker para erros específicos

## 📝 Próximos Passos

1. **Painel web admin** - Visualizar estatísticas e golpes detectados
2. **Autenticação** - Sistema de login/registro
3. **Casos de treino** - Banco de golpes para educação
4. **Notificações** - Alertas em tempo real
5. **Machine Learning** - Melhorar detecção com ML
