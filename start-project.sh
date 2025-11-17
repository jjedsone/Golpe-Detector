#!/bin/bash

echo "========================================"
echo "  Golpe Detector - Iniciando Projeto"
echo "========================================"
echo

echo "[1/5] Verificando Docker..."
if ! command -v docker &> /dev/null; then
    echo "ERRO: Docker não está instalado!"
    echo "Por favor, instale o Docker e tente novamente."
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "ERRO: Docker não está rodando!"
    echo "Por favor, inicie o Docker e tente novamente."
    exit 1
fi
echo "Docker OK!"
echo

echo "[2/5] Subindo serviços (PostgreSQL, Redis, Backend)..."
docker-compose up -d
if [ $? -ne 0 ]; then
    echo "ERRO: Falha ao subir serviços!"
    exit 1
fi
echo "Serviços iniciados!"
echo

echo "[3/5] Aguardando serviços iniciarem..."
sleep 10
echo

echo "[4/5] Verificando status..."
docker-compose ps
echo

echo "[5/5] Iniciando worker em background..."
docker exec -d backend rq worker
echo "Worker iniciado!"
echo

echo "========================================"
echo "  Projeto iniciado com sucesso!"
echo "========================================"
echo
echo "Serviços disponíveis:"
echo "  - API Backend: http://localhost:8000"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo
echo "Para verificar:"
echo "  curl http://localhost:8000/health"
echo
echo "Para abrir a página de verificação:"
echo "  open verify.html  # Mac"
echo "  xdg-open verify.html  # Linux"
echo
echo "Para ver logs:"
echo "  docker-compose logs -f"
echo
echo "Para parar:"
echo "  docker-compose down"
echo

