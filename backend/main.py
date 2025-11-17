from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import redis
import os
from pydantic import BaseModel, HttpUrl
from rq import Queue
import uuid
from datetime import datetime
import logging
from contextlib import contextmanager

from db_pool import get_db_conn, return_db_conn
from url_validator import validate_url
from metrics import track_request, get_metrics
from time import time

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Golpe Detector API", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://appuser:appsenha@postgres:5432/protecao")

r = redis.from_url(REDIS_URL)
q = Queue(connection=r, default_timeout=300)  # Timeout de 5 minutos

@contextmanager
def get_db():
    """Context manager para conexões do banco"""
    conn = None
    try:
        conn = get_db_conn()
        yield conn
    finally:
        if conn:
            return_db_conn(conn)

def init_db():
    """Cria tabelas se não existirem"""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            
            # Criar tabela de submissões
            cur.execute("""
                CREATE TABLE IF NOT EXISTS submissions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER,
                    url TEXT,
                    status TEXT DEFAULT 'queued',
                    result JSONB,
                    job_id TEXT UNIQUE,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT now(),
                    processed_at TIMESTAMP
                )
            """)
            
            # Criar índices
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_submissions_job_id ON submissions(job_id)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_submissions_status ON submissions(status)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_submissions_created_at ON submissions(created_at)
            """)
            
            conn.commit()
            cur.close()
            logger.info("Banco de dados inicializado com sucesso")
    except Exception as e:
        logger.error("Erro ao inicializar banco: %s", e)

# Inicializar banco na startup
init_db()

class SubmitURL(BaseModel):
    url: HttpUrl
    user_id: int | None = None

@app.get("/")
def index():
    return {"status": "online", "mensagem": "Sistema de proteção educacional ativo."}

@app.post("/submit")
def submit(payload: SubmitURL, request: Request):
    """Envia URL para análise"""
    # Validar URL
    is_valid, error_msg = validate_url(payload.url)
    if not is_valid:
        logger.warning("URL bloqueada: %s - %s", payload.url, error_msg)
        raise HTTPException(status_code=400, detail=f"URL inválida ou bloqueada: {error_msg}")
    
    job_id = str(uuid.uuid4())
    
    # Criar registro no banco
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO submissions (url, user_id, status, job_id)
                VALUES (%s, %s, 'queued', %s)
                RETURNING id
            """, (str(payload.url), payload.user_id, job_id))
            
            submission_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            logger.info("Submissão criada: %s - %s", job_id, payload.url)
    except Exception as e:
        logger.error("Erro ao criar submissão: %s", e)
        raise HTTPException(status_code=500, detail=f"Erro ao criar submissão: {str(e)}")
    
    # Enfileirar job com timeout
    try:
        q.enqueue(
            "worker.analyze_url",
            payload.url,
            payload.user_id,
            job_id,
            job_id=job_id,
            job_timeout=300,  # 5 minutos
            result_ttl=3600   # Resultado válido por 1 hora
        )
        logger.info("Job enfileirado: %s", job_id)
    except Exception as e:
        logger.error("Erro ao enfileirar análise: %s", e)
        # Atualizar status para failed
        try:
            with get_db() as conn:
                cur = conn.cursor()
                cur.execute("""
                    UPDATE submissions 
                    SET status = 'failed', error_message = %s 
                    WHERE job_id = %s
                """, (str(e), job_id))
                conn.commit()
                cur.close()
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Erro ao enfileirar análise: {str(e)}")
    
    return {"job_id": job_id, "status": "enfileirado", "submission_id": submission_id}

@app.get("/submission/{job_id}")
def get_submission(job_id: str):
    """Obtém resultado da análise"""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, url, status, result, created_at, processed_at, error_message
                FROM submissions
                WHERE job_id = %s
            """, (job_id,))
            
            row = cur.fetchone()
            cur.close()
            
            if not row:
                raise HTTPException(status_code=404, detail="Submissão não encontrada")
            
            return {
                "id": row[0],
                "url": row[1],
                "status": row[2],
                "result": row[3],
                "created_at": row[4].isoformat() if row[4] else None,
                "processed_at": row[5].isoformat() if row[5] else None,
                "error_message": row[6]
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao buscar submissão %s: %s", job_id, e)
        raise HTTPException(status_code=500, detail=f"Erro ao buscar submissão: {str(e)}")

@app.get("/submissions")
def list_submissions(limit: int = 100, offset: int = 0, status: str = None):
    """Lista todas as submissões com paginação"""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            
            query = """
                SELECT id, url, status, result, job_id, created_at, processed_at, user_id, error_message
                FROM submissions
            """
            params = []
            
            if status:
                query += " WHERE status = %s"
                params.append(status)
            
            query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cur.execute(query, params)
            rows = cur.fetchall()
            
            # Contar total
            count_query = "SELECT COUNT(*) FROM submissions"
            if status:
                count_query += " WHERE status = %s"
                cur.execute(count_query, [status])
            else:
                cur.execute(count_query)
            total = cur.fetchone()[0]
            
            cur.close()
            
            submissions = []
            for row in rows:
                submissions.append({
                    "id": row[0],
                    "url": row[1],
                    "status": row[2],
                    "result": row[3],
                    "job_id": row[4],
                    "created_at": row[5].isoformat() if row[5] else None,
                    "processed_at": row[6].isoformat() if row[6] else None,
                    "user_id": row[7],
                    "error_message": row[8]
                })
            
            return {
                "submissions": submissions,
                "total": total,
                "limit": limit,
                "offset": offset
            }
    except Exception as e:
        logger.error("Erro ao listar submissões: %s", e)
        raise HTTPException(status_code=500, detail=f"Erro ao listar submissões: {str(e)}")

@app.get("/stats")
def get_stats():
    """Retorna estatísticas agregadas"""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'queued') as queued,
                    COUNT(*) FILTER (WHERE status = 'processing') as processing,
                    COUNT(*) FILTER (WHERE status = 'done') as done,
                    COUNT(*) FILTER (WHERE status = 'failed') as failed,
                    COUNT(*) FILTER (WHERE result->>'level' = 'alto') as alto,
                    COUNT(*) FILTER (WHERE result->>'level' = 'médio') as medio,
                    COUNT(*) FILTER (WHERE result->>'level' = 'baixo') as baixo,
                    AVG(EXTRACT(EPOCH FROM (processed_at - created_at))) as avg_processing_time
                FROM submissions
                WHERE processed_at IS NOT NULL
            """)
            
            row = cur.fetchone()
            
            # Estatísticas de hoje
            cur.execute("""
                SELECT COUNT(*) 
                FROM submissions 
                WHERE DATE(created_at) = CURRENT_DATE
            """)
            today_count = cur.fetchone()[0] or 0
            
            cur.close()
            
            return {
                "total": row[0] or 0,
                "queued": row[1] or 0,
                "processing": row[2] or 0,
                "done": row[3] or 0,
                "failed": row[4] or 0,
                "alto": row[5] or 0,
                "medio": row[6] or 0,
                "baixo": row[7] or 0,
                "avg_processing_time_seconds": float(row[8]) if row[8] else 0,
                "today_count": today_count
            }
    except Exception as e:
        logger.error("Erro ao buscar estatísticas: %s", e)
        raise HTTPException(status_code=500, detail=f"Erro ao buscar estatísticas: {str(e)}")

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Middleware para coletar métricas"""
    start_time = time()
    response = await call_next(request)
    processing_time = time() - start_time
    
    track_request(
        endpoint=request.url.path,
        status_code=response.status_code,
        processing_time=processing_time
    )
    
    return response

@app.get("/metrics")
def metrics_endpoint():
    """Endpoint de métricas para monitoramento"""
    return get_metrics()

@app.get("/health")
def health():
    """Health check detalhado"""
    health_status = {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "services": {}
    }
    
    # Verificar banco de dados
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.close()
        health_status["services"]["database"] = "ok"
    except Exception as e:
        health_status["services"]["database"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Verificar Redis
    try:
        r.ping()
        health_status["services"]["redis"] = "ok"
    except Exception as e:
        health_status["services"]["redis"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Verificar fila
    try:
        queue_length = len(q)
        health_status["services"]["queue"] = {
            "status": "ok",
            "pending_jobs": queue_length
        }
    except Exception as e:
        health_status["services"]["queue"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status

