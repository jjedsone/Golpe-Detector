@echo off
REM Script para iniciar todos os serviços (Windows)

echo 🚀 Iniciando Golpe Detector...

REM Verificar se Docker está rodando
docker ps >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker não está rodando. Por favor, inicie o Docker primeiro.
    exit /b 1
)

REM Subir infraestrutura
echo 📦 Subindo PostgreSQL e Redis...
docker-compose up -d

REM Aguardar serviços ficarem prontos
echo ⏳ Aguardando serviços ficarem prontos...
timeout /t 5 /nobreak >nul

REM Iniciar backend
echo 🔧 Iniciando backend...
cd backend
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install -r requirements.txt >nul 2>&1
start "Backend API" cmd /k "uvicorn main:app --reload --host 0.0.0.0 --port 8000"
cd ..

REM Iniciar worker
echo ⚙️  Iniciando worker...
cd worker
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install -r requirements.txt >nul 2>&1
start "Worker" cmd /k "python worker.py"
cd ..

echo.
echo ✅ Serviços iniciados!
echo 📱 Backend: http://localhost:8000
echo 📚 Docs: http://localhost:8000/docs
echo.
echo Para parar os serviços, feche as janelas do Backend e Worker
echo e execute: docker-compose down

pause

