"""
Connection pooling para PostgreSQL
"""
import os
from psycopg2 import pool

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://appuser:appsenha@postgres:5432/protecao")

# Criar pool de conexões
connection_pool = pool.SimpleConnectionPool(
    minconn=1,
    maxconn=20,
    dsn=DATABASE_URL
)

def get_db_conn():
    """Retorna conexão do pool"""
    if connection_pool:
        return connection_pool.getconn()
    raise Exception("Pool de conexões não inicializado")

def return_db_conn(conn):
    """Retorna conexão para o pool"""
    if connection_pool:
        connection_pool.putconn(conn)

def close_all_connections():
    """Fecha todas as conexões do pool"""
    if connection_pool:
        connection_pool.closeall()

