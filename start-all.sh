#!/bin/bash
# Script para iniciar todo o projeto

echo "🚀 Iniciando Golpe Detector - Sistema Completo"
echo ""

# Verificar se Docker está rodando
if ! docker ps > /dev/null 2>&1; then
    echo "❌ Docker não está rodando. Por favor, inicie o Docker primeiro."
    exit 1
fi

# 1. Subir infraestrutura
echo "📦 Subindo PostgreSQL, Redis e Backend..."
docker-compose up -d

# Aguardar serviços ficarem prontos
echo "⏳ Aguardando serviços ficarem prontos..."
sleep 5

# Verificar se serviços estão rodando
echo ""
echo "✅ Serviços iniciados:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "postgres|redis|backend"

echo ""
echo "📱 Backend API: http://localhost:8000"
echo "📚 Docs: http://localhost:8000/docs"
echo ""
echo "⚙️  Para iniciar o worker, execute em outro terminal:"
echo "   docker exec -it backend bash"
echo "   rq worker"
echo ""
echo "🖥️  Para iniciar o painel admin, execute em outro terminal:"
echo "   cd admin && npm install && npm run dev"
echo ""
echo "📱 Para iniciar o app mobile, execute em outro terminal:"
echo "   cd mobile && npm install && npm start"
echo ""

