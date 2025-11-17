# 🛡️ Sistema de Defesa e Análise Forense

Sistema legal e ético de defesa contra ataques, com coleta de informações forenses para reporte às autoridades.

## ⚠️ IMPORTANTE - Limitações Legais

Este sistema implementa apenas funcionalidades **LEGAIS e ÉTICAS**:

✅ **PERMITIDO:**
- Bloquear IPs/domínios atacantes
- Registrar informações de ataque (logs, metadados)
- Coletar evidências forenses
- Análise de padrões de ataque
- Reporte às autoridades competentes

❌ **NÃO IMPLEMENTADO (ILEGAL):**
- Acesso não autorizado a sistemas de atacantes
- Contra-ataques (hackback)
- Penetração em sistemas de terceiros
- Interceptação não autorizada de comunicações

## 🔍 Funcionalidades Implementadas

### 1. **Coleta de Metadados de Ataque**

Coleta informações legais disponíveis na requisição HTTP:

- **IP do atacante**: Endereço IP de origem
- **User-Agent**: Navegador e sistema operacional
- **Headers HTTP**: Referer, Accept-Language, etc
- **Informações de rede**: Proxy, VPN, etc
- **Timestamp**: Data e hora exata do ataque

### 2. **Análise de IP**

Informações coletadas sobre IPs:

- Tipo de IP (IPv4/IPv6)
- Se é IP privado/público
- Reverse DNS (hostname)
- Detecção de VPN/Proxy
- Histórico de ataques do IP

### 3. **Bloqueio Automático**

Sistema bloqueia automaticamente IPs que:

- Realizam 3+ ataques críticos em 24h
- Realizam 5+ ataques de alta severidade
- Realizam 10+ ataques em 24h

### 4. **Relatórios Forenses**

Gera relatórios completos para:

- Análise interna de segurança
- Reporte às autoridades competentes
- Documentação legal de incidentes
- Análise de padrões de ataque

### 5. **Histórico de Ataques**

Registra todos os ataques com:

- Tipo de ataque detectado
- Nível de risco
- Metadados completos
- Relatório forense
- Timestamp preciso

## 📡 Endpoints da API

### Análise e Monitoramento

```bash
# Listar todos os ataques detectados
GET /defense/attacks?limit=100&ip=192.168.1.1

# Obter relatório forense de um ataque específico
GET /defense/attacks/{attack_id}/report

# Obter informações sobre um IP
GET /defense/ip/{ip}/info

# Bloquear IP manualmente
POST /defense/ip/{ip}/block?reason=Atividade suspeita
```

## 📊 Estrutura de Dados

### Tabela `attack_logs`

```sql
CREATE TABLE attack_logs (
  id SERIAL PRIMARY KEY,
  client_ip TEXT NOT NULL,
  attack_type TEXT NOT NULL,
  risk_level TEXT NOT NULL,
  metadata JSONB NOT NULL,
  report JSONB,
  created_at TIMESTAMP DEFAULT now()
);
```

### Exemplo de Relatório Forense

```json
{
  "report_id": "ATK-20240101-120000-192-168-1-1",
  "timestamp": "2024-01-01T12:00:00",
  "attack_details": {
    "type": "sql_injection",
    "severity": "high",
    "target": "https://example.com/api",
    "payload": "SELECT * FROM users"
  },
  "attacker_info": {
    "ip_address": "192.168.1.1",
    "ip_information": {
      "ip": "192.168.1.1",
      "is_private": true,
      "hostname": null
    },
    "user_agent": "Mozilla/5.0...",
    "browser": "Chrome",
    "os": "Windows",
    "is_bot": false
  },
  "recommendations": [
    "Bloquear IP imediatamente",
    "Adicionar à blacklist permanente",
    "Reportar às autoridades se necessário"
  ]
}
```

## 🔒 Fluxo de Defesa

1. **Detecção**: Sistema detecta ataque em URL ou conteúdo
2. **Coleta**: Extrai metadados legais da requisição
3. **Análise**: Analisa padrões e características do ataque
4. **Registro**: Salva no banco de dados com relatório forense
5. **Bloqueio**: Bloqueia IP se exceder limites configurados
6. **Reporte**: Gera relatório para análise e possível reporte legal

## 📈 Análise de Padrões

O sistema analisa:

- **Frequência de ataques**: Quantos ataques por IP
- **Tipos de ataque**: SQL Injection, XSS, etc
- **Padrões temporais**: Horários preferenciais
- **Ferramentas**: Bots vs humanos
- **Origem**: IPs, países, ISPs

## 🚨 Alertas e Notificações

Recomendações para implementação futura:

- Alertas em tempo real para ataques críticos
- Notificações por email/SMS
- Integração com sistemas de SIEM
- Dashboard de ameaças em tempo real
- Reporte automático às autoridades

## ⚖️ Considerações Legais

### O que é Legal:

1. **Bloqueio de IPs**: Legal em todos os países
2. **Logs de acesso**: Legal com aviso de privacidade
3. **Análise de padrões**: Legal para defesa própria
4. **Reporte às autoridades**: Legal e recomendado

### O que NÃO é Legal:

1. **Hackback**: Contra-ataques são ilegais
2. **Acesso não autorizado**: Mesmo em resposta a ataques
3. **Interceptação**: Sem autorização judicial
4. **Vigilância excessiva**: Violação de privacidade

## 🔐 Boas Práticas

1. **Documentação**: Mantenha logs detalhados
2. **Retenção**: Defina política de retenção de logs
3. **Privacidade**: Respeite leis de proteção de dados
4. **Autoridades**: Reporte crimes cibernéticos
5. **Transparência**: Seja claro sobre coleta de dados

## 📝 Uso Responsável

Este sistema deve ser usado apenas para:

- ✅ Defesa própria legítima
- ✅ Coleta de evidências legais
- ✅ Análise de segurança
- ✅ Reporte às autoridades

**NÃO use para:**
- ❌ Vigilância não autorizada
- ❌ Retaliação ou vingança
- ❌ Acesso não autorizado
- ❌ Violação de privacidade

## 🚀 Próximos Passos

- [ ] Integração com serviços de geolocalização IP
- [ ] Dashboard de ameaças em tempo real
- [ ] Alertas automáticos
- [ ] Integração com SIEM
- [ ] Reporte automático às autoridades
- [ ] Análise de comportamento (ML)

