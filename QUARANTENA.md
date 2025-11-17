# 🛡️ Sistema de Quarentena - Proteção contra Vírus e Ataques Hackers

Sistema completo de quarentena para detectar, isolar e gerenciar ameaças de segurança.

## 📋 Funcionalidades

### 1. **Detecção de Ataques**
- **SQL Injection**: Detecta tentativas de injeção SQL
- **XSS (Cross-Site Scripting)**: Identifica scripts maliciosos
- **Command Injection**: Detecta tentativas de execução de comandos
- **Path Traversal**: Identifica tentativas de acesso a arquivos do sistema
- **File Upload Attacks**: Detecta uploads de arquivos perigosos

### 2. **Análise de Arquivos**
- Cálculo de hash MD5 para identificação única
- Verificação de assinaturas de malware conhecidas
- Detecção de extensões perigosas (.exe, .php, .sh, etc)
- Análise de conteúdo em busca de código malicioso

### 3. **Sistema de Quarentena**
- Isolamento automático de URLs e arquivos maliciosos
- Classificação por nível de risco (low, medium, high, critical)
- Histórico completo de ameaças detectadas
- Liberação manual de itens em quarentena

### 4. **Blacklist**
- Bloqueio automático de URLs, domínios, IPs e hashes maliciosos
- Verificação em tempo real antes de processar requisições
- Gerenciamento de blacklist ativa/inativa

## 🔧 Como Usar

### Analisar Arquivo

```bash
curl -X POST "http://localhost:8000/quarantine/file" \
  -F "file=@arquivo_suspeito.exe"
```

**Resposta:**
```json
{
  "quarantined": true,
  "quarantine_id": 1,
  "analysis": {
    "file_hash": "abc123...",
    "threats": [
      {
        "type": "dangerous_extension",
        "severity": "high",
        "extension": ".exe"
      }
    ],
    "risk_level": "high"
  },
  "message": "Arquivo colocado em quarentena"
}
```

### Listar Itens em Quarentena

```bash
curl "http://localhost:8000/quarantine?status=quarantined&limit=50"
```

### Liberar Item da Quarentena

```bash
curl -X POST "http://localhost:8000/quarantine/1/release?user_id=1"
```

### Adicionar à Blacklist

```bash
curl -X POST "http://localhost:8000/blacklist" \
  -H "Content-Type: application/json" \
  -d '{
    "item_type": "url",
    "item_value": "https://site-malicioso.com",
    "threat_type": "phishing",
    "notes": "Site de phishing detectado"
  }'
```

### Listar Blacklist

```bash
curl "http://localhost:8000/blacklist?limit=100"
```

## 🗄️ Estrutura do Banco de Dados

### Tabela `quarantine`
- `id`: ID único
- `item_type`: Tipo ('url' ou 'file')
- `item_identifier`: URL ou hash do arquivo
- `threat_analysis`: Análise completa em JSONB
- `risk_level`: Nível de risco (low, medium, high, critical)
- `quarantined_at`: Data/hora da quarentena
- `released_at`: Data/hora da liberação (se aplicável)
- `status`: Status (quarantined, released, deleted)

### Tabela `blacklist`
- `id`: ID único
- `item_type`: Tipo ('url', 'domain', 'ip', 'hash')
- `item_value`: Valor a ser bloqueado
- `threat_type`: Tipo de ameaça (malware, phishing, spam, etc)
- `is_active`: Se está ativo
- `added_at`: Data/hora de adição

## 🔍 Tipos de Ameaças Detectadas

### SQL Injection
Padrões detectados:
- Comandos SQL (SELECT, INSERT, UPDATE, DELETE, DROP, etc)
- Caracteres especiais ('; -- /* */)
- Operadores lógicos (OR, AND)

### XSS (Cross-Site Scripting)
Padrões detectados:
- Tags `<script>`
- Eventos JavaScript (`onclick`, `onerror`, etc)
- URLs `javascript:`
- Tags `<iframe>`, `<object>`, `<embed>`

### Command Injection
Padrões detectados:
- Comandos shell (cat, ls, wget, curl, etc)
- Caracteres de controle (; | & ` $)
- Execução de comandos ($(), `${}`, ``)

### Path Traversal
Padrões detectados:
- `../` e `..\\`
- Encodings (`%2e%2e%2f`, `%2e%2e%5c`)

## 📊 Níveis de Risco

- **low**: Ameaça menor, pode ser falsa positivo
- **medium**: Ameaça moderada, requer atenção
- **high**: Ameaça alta, bloqueio recomendado
- **critical**: Ameaça crítica, bloqueio imediato

## 🔒 Integração Automática

O sistema está integrado ao fluxo normal de análise:

1. **URLs**: Verificadas automaticamente antes de processar
2. **Conteúdo**: Analisado durante a análise com Playwright
3. **Blacklist**: Verificada em tempo real
4. **Quarentena**: Aplicada automaticamente para ameaças críticas

## 🚀 Próximos Passos

- [ ] Integração com VirusTotal API
- [ ] Machine Learning para detecção avançada
- [ ] Análise comportamental de arquivos
- [ ] Sandbox isolado para execução de arquivos
- [ ] Notificações automáticas de ameaças críticas
- [ ] Dashboard de ameaças em tempo real

