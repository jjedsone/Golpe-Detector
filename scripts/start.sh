#!/bin/bash
# Script para iniciar todos os serviços

echo "🚀 Iniciando Golpe Detector..."

# Verificar se Docker está rodando
if ! docker ps > /dev/null 2>&1; then
    echo "❌ Docker não está rodando. Por favor, inicie o Docker primeiro."
    exit 1
fi

# Subir infraestrutura
echo "📦 Subindo PostgreSQL e Redis..."
docker-compose up -d

# Aguardar serviços ficarem prontos
echo "⏳ Aguardando serviços ficarem prontos..."
sleep 5

# Iniciar backend (em background)
echo "🔧 Iniciando backend..."
cd backend
source venv/bin/activate 2>/dev/null || python -m venv venv && source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Iniciar worker (em background)
echo "⚙️  Iniciando worker..."
cd worker
source venv/bin/activate 2>/dev/null || python -m venv venv && source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1
python worker.py &
WORKER_PID=$!
cd ..

echo ""
echo "✅ Serviços iniciados!"
echo "📱 Backend: http://localhost:8000"
echo "📚 Docs: http://localhost:8000/docs"
echo ""
echo "Para parar os serviços, pressione Ctrl+C"

# Aguardar interrupção
trap "kill $BACKEND_PID $WORKER_PID; docker-compose down; exit" INT TERM
wait

