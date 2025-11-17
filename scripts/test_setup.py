#!/usr/bin/env python3
"""
Script para testar se a instalação está correta
Execute: python scripts/test_setup.py
"""
import sys
import os

def test_imports():
    """Testa se as dependências estão instaladas"""
    print("🔍 Testando imports...")
    
    try:
        import fastapi
        print("  ✅ FastAPI")
    except ImportError:
        print("  ❌ FastAPI não instalado")
        return False
    
    try:
        import redis
        print("  ✅ Redis")
    except ImportError:
        print("  ❌ Redis não instalado")
        return False
    
    try:
        import rq
        print("  ✅ RQ")
    except ImportError:
        print("  ❌ RQ não instalado")
        return False
    
    try:
        from playwright.sync_api import sync_playwright
        print("  ✅ Playwright")
    except ImportError:
        print("  ❌ Playwright não instalado")
        return False
    
    try:
        import psycopg2
        print("  ✅ psycopg2")
    except ImportError:
        print("  ❌ psycopg2 não instalado")
        return False
    
    return True

def test_redis_connection():
    """Testa conexão com Redis"""
    print("\n🔍 Testando conexão com Redis...")
    try:
        import redis
        r = redis.from_url("redis://localhost:6379/0")
        r.ping()
        print("  ✅ Redis conectado")
        return True
    except Exception as e:
        print(f"  ❌ Erro ao conectar Redis: {e}")
        print("  💡 Execute: docker-compose up -d")
        return False

def test_postgres_connection():
    """Testa conexão com PostgreSQL"""
    print("\n🔍 Testando conexão com PostgreSQL...")
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="golpe_user",
            password="golpe_pass",
            database="golpe_db"
        )
        conn.close()
        print("  ✅ PostgreSQL conectado")
        return True
    except Exception as e:
        print(f"  ❌ Erro ao conectar PostgreSQL: {e}")
        print("  💡 Execute: docker-compose up -d")
        return False

def test_playwright():
    """Testa se Playwright está configurado"""
    print("\n🔍 Testando Playwright...")
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
        print("  ✅ Playwright funcionando")
        return True
    except Exception as e:
        print(f"  ❌ Erro no Playwright: {e}")
        print("  💡 Execute: playwright install chromium")
        return False

def main():
    print("🧪 Testando instalação do Golpe Detector\n")
    
    results = []
    results.append(("Imports", test_imports()))
    results.append(("Redis", test_redis_connection()))
    results.append(("PostgreSQL", test_postgres_connection()))
    results.append(("Playwright", test_playwright()))
    
    print("\n" + "="*50)
    print("📊 Resumo dos Testes")
    print("="*50)
    
    for name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 Todos os testes passaram! Sistema pronto para uso.")
        return 0
    else:
        print("\n⚠️  Alguns testes falharam. Verifique os erros acima.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

