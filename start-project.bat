@echo off
echo ========================================
echo   Golpe Detector - Iniciando Projeto
echo ========================================
echo.

echo [1/5] Verificando Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Docker nao esta instalado!
    echo Por favor, instale o Docker Desktop e tente novamente.
    pause
    exit /b 1
)

docker info >nul 2>&1
if errorlevel 1 (
    echo ERRO: Docker Desktop nao esta rodando!
    echo.
    echo Por favor:
    echo 1. Abra o Docker Desktop
    echo 2. Aguarde aparecer "Docker is running"
    echo 3. Execute este script novamente
    echo.
    pause
    exit /b 1
)
echo Docker OK!
echo.

echo [2/5] Subindo servicos (PostgreSQL, Redis, Backend)...
docker-compose up -d
if errorlevel 1 (
    echo ERRO: Falha ao subir servicos!
    pause
    exit /b 1
)
echo Servicos iniciados!
echo.

echo [3/5] Aguardando servicos iniciarem...
timeout /t 10 /nobreak
echo.

echo [4/5] Verificando status...
docker-compose ps
echo.

echo [5/5] Iniciando worker em background...
docker exec -d backend rq worker
echo Worker iniciado!
echo.

echo ========================================
echo   Projeto iniciado com sucesso!
echo ========================================
echo.
echo Servicos disponiveis:
echo   - API Backend: http://localhost:8000
echo   - PostgreSQL: localhost:5432
echo   - Redis: localhost:6379
echo.
echo Para verificar:
echo   curl http://localhost:8000/health
echo.
echo Para abrir a pagina de verificacao:
echo   start verify.html
echo.
echo Para ver logs:
echo   docker-compose logs -f
echo.
echo Para parar:
echo   docker-compose down
echo.

pause

