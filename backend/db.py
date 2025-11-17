import psycopg2
import os

def get_conn():
    """Retorna conexão com o banco de dados"""
    url = os.getenv("DATABASE_URL")
    return psycopg2.connect(url)

