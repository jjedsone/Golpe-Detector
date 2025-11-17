@echo off
REM Script para iniciar todo o projeto (Windows)

echo 🚀 Iniciando Golpe Detector - Sistema Completo
echo.

REM Verificar se Docker está rodando
docker ps >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker não está rodando. Por favor, inicie o Docker primeiro.
    pause
    exit /b 1
)

REM 1. Subir infraestrutura
echo 📦 Subindo PostgreSQL, Redis e Backend...
docker-compose up -d

REM Aguardar serviços ficarem prontos
echo ⏳ Aguardando serviços ficarem prontos...
timeout /t 5 /nobreak >nul

REM Verificar se serviços estão rodando
echo.
echo ✅ Serviços iniciados:
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo.
echo 📱 Backend API: http://localhost:8000
echo 📚 Docs: http://localhost:8000/docs
echo.
echo ⚙️  Para iniciar o worker, abra outro terminal e execute:
echo    docker exec -it backend bash
echo    rq worker
echo.
echo 🖥️  Para iniciar o painel admin, abra outro terminal e execute:
echo    cd admin
echo    npm install
echo    npm run dev
echo.
echo 📱 Para iniciar o app mobile, abra outro terminal e execute:
echo    cd mobile
echo    npm install
echo    npm start
echo.

pause

