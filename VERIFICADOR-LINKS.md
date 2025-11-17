# 🔍 Verificador de Confiabilidade de Links

Sistema para verificar se um link é confiável ou não antes de acessá-lo.

## 🎯 Funcionalidades

### Análise de Confiabilidade

O sistema analisa múltiplos fatores para determinar a confiabilidade:

1. **Estrutura da URL**
   - Protocolo HTTPS/HTTP
   - Uso de encurtadores de URL
   - IP direto vs domínio
   - Número de subdomínios
   - Palavras-chave suspeitas

2. **Reputação do Domínio**
   - Domínios confiáveis conhecidos
   - Extensões de domínio (.com, .org, .gov, etc)
   - Domínios gratuitos suspeitos
   - Estrutura do nome do domínio

3. **Verificações Adicionais**
   - Blacklist de URLs/domínios
   - Certificado TLS
   - Typosquatting
   - Conteúdo suspeito

## 📊 Score de Confiabilidade

O sistema retorna um score de 0 a 100:

- **80-100**: ✅ **Confiável** - Pode acessar com segurança
- **60-79**: ⚠️ **Moderadamente Confiável** - Tenha cuidado
- **40-59**: ⚠️ **Suspeito** - Evite acessar
- **0-39**: ❌ **Não Confiável** - NÃO acesse

## 📡 Como Usar

### Verificação Rápida (GET)

```bash
# URL completa
curl "http://localhost:8000/verify/https://example.com"

# Sem protocolo (adiciona https:// automaticamente)
curl "http://localhost:8000/verify/example.com"
```

### Verificação via POST

```bash
curl -X POST "http://localhost:8000/verify" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

## 📋 Exemplo de Resposta

```json
{
  "url": "https://example.com",
  "domain": "example.com",
  "trust_score": 85.5,
  "trust_level": "confiável",
  "trust_icon": "✅",
  "structure_score": 90,
  "reputation_score": 82,
  "issues": [],
  "info": [
    "Usa HTTPS (seguro)",
    "Extensão de domínio confiável"
  ],
  "is_trusted": true,
  "recommendation": "Link parece confiável. Pode acessar com segurança.",
  "analyzed_at": "2024-01-01T12:00:00"
}
```

### Exemplo de Link Suspeito

```json
{
  "url": "http://bit.ly/suspicious-link",
  "domain": "bit.ly",
  "trust_score": 35.0,
  "trust_level": "não confiável",
  "trust_icon": "❌",
  "structure_score": 50,
  "reputation_score": 25,
  "issues": [
    "Não usa HTTPS",
    "Usa encurtador de URL ou domínio suspeito"
  ],
  "info": [],
  "is_trusted": false,
  "recommendation": "Link não confiável. NÃO acesse este link.",
  "analyzed_at": "2024-01-01T12:00:00"
}
```

## 🔍 Fatores Analisados

### ✅ Fatores Positivos

- Uso de HTTPS
- Domínios conhecidos e confiáveis
- Extensões de domínio confiáveis (.com, .org, .gov, .edu)
- Estrutura de URL limpa
- Sem encurtadores de URL

### ⚠️ Fatores Negativos

- Não usa HTTPS
- Encurtadores de URL (bit.ly, tinyurl, etc)
- IP direto em vez de domínio
- Domínios gratuitos (.tk, .ml, .ga, .cf)
- Muitos subdomínios
- Palavras-chave suspeitas (click, verify, urgent, etc)
- Parâmetros suspeitos (redirect, url, link)
- URL na blacklist

## 🛡️ Integração com Sistema de Segurança

O verificador integra com:

- **Blacklist**: Verifica se URL/domínio está bloqueado
- **Quarentena**: Considera itens em quarentena
- **Análise de Ataques**: Detecta padrões maliciosos

## 📱 Uso no App Mobile

O app mobile pode usar este endpoint para:

1. Verificar links antes de abrir
2. Mostrar aviso de segurança
3. Bloquear links não confiáveis
4. Educar usuários sobre segurança

## 🔧 Personalização

### Adicionar Domínios Confiáveis

Edite `backend/link_trust.py`:

```python
TRUSTED_DOMAINS = [
    'seu-dominio.com',
    'outro-dominio.com.br',
    # ...
]
```

### Ajustar Pesos do Score

Edite a função `calculate_trust_score()`:

```python
# Ajustar pesos
base_score = (structure_score * 0.4) + (reputation_score * 0.6)
```

## 🚀 Melhorias Futuras

- [ ] Integração com APIs de reputação (VirusTotal, etc)
- [ ] Verificação de WHOIS para idade do domínio
- [ ] Análise de conteúdo da página
- [ ] Machine Learning para melhorar detecção
- [ ] Cache de resultados para performance
- [ ] Histórico de verificações por usuário

## ⚠️ Limitações

- Análise baseada em padrões e heurísticas
- Não substitui análise humana completa
- Domínios novos podem ter score baixo mesmo sendo legítimos
- Alguns encurtadores legítimos podem ser marcados como suspeitos

## 📝 Boas Práticas

1. **Sempre verifique** links antes de clicar
2. **Use HTTPS** sempre que possível
3. **Desconfie** de encurtadores de URL
4. **Verifique** o domínio completo antes de inserir dados
5. **Não ignore** avisos de segurança

