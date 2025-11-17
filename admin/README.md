# Painel Admin - Golpe Detector

Painel web administrativo para visualizar e gerenciar análises de golpes.

## 🚀 Instalação

```bash
cd admin
npm install
```

## 🏃 Executar

```bash
npm run dev
```

O painel estará disponível em: `http://localhost:3000`

## 📋 Funcionalidades

### Dashboard
- Visão geral das análises
- Estatísticas em tempo real
- Distribuição de risco
- Submissões recentes

### Submissões
- Lista completa de todas as análises
- Filtros por status
- Detalhes completos de cada análise
- Visualização de resultados

### Estatísticas
- Gráficos de distribuição por status
- Gráficos de distribuição por risco
- Análises por hora do dia
- Métricas agregadas

## 🔧 Configuração

O painel se conecta automaticamente ao backend em `http://localhost:8000`.

Para alterar a URL da API, crie um arquivo `.env`:

```
VITE_API_URL=http://localhost:8000
```

## 📦 Build para Produção

```bash
npm run build
```

Os arquivos estarão em `dist/`.

