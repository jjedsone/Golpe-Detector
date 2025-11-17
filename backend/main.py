from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import redis
import os
import tempfile
import shutil
from pydantic import BaseModel, HttpUrl
from rq import Queue
import uuid
from datetime import datetime, timedelta
from typing import Optional, List
import logging
from contextlib import contextmanager
from urllib.parse import urlparse

from db_pool import get_db_conn, return_db_conn
from url_validator import validate_url
from metrics import track_request, get_metrics
from time import time
from quarantine import analyze_url_for_attacks, should_quarantine
from quarantine_api import add_to_quarantine, check_blacklist, add_to_blacklist
from defense import extract_attack_metadata, analyze_attack_pattern, should_block_ip, create_attack_report
from link_trust import verify_link_trust, calculate_trust_score
import json

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
            
            # Criar tabela de quarentena
            cur.execute("""
                CREATE TABLE IF NOT EXISTS quarantine (
                    id SERIAL PRIMARY KEY,
                    item_type TEXT NOT NULL,
                    item_identifier TEXT NOT NULL,
                    threat_analysis JSONB NOT NULL,
                    risk_level TEXT NOT NULL,
                    quarantined_at TIMESTAMP DEFAULT now(),
                    released_at TIMESTAMP,
                    released_by INTEGER,
                    status TEXT DEFAULT 'quarantined',
                    notes TEXT
                )
            """)
            
            # Criar tabela de blacklist
            cur.execute("""
                CREATE TABLE IF NOT EXISTS blacklist (
                    id SERIAL PRIMARY KEY,
                    item_type TEXT NOT NULL,
                    item_value TEXT NOT NULL UNIQUE,
                    threat_type TEXT,
                    added_at TIMESTAMP DEFAULT now(),
                    added_by INTEGER,
                    is_active BOOLEAN DEFAULT true,
                    notes TEXT
                )
            """)
            
            # Criar tabela de logs de ataques
            cur.execute("""
                CREATE TABLE IF NOT EXISTS attack_logs (
                    id SERIAL PRIMARY KEY,
                    client_ip TEXT NOT NULL,
                    attack_type TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    metadata JSONB NOT NULL,
                    report JSONB,
                    created_at TIMESTAMP DEFAULT now()
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
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_quarantine_status ON quarantine(status)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_quarantine_item ON quarantine(item_type, item_identifier)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_blacklist_value ON blacklist(item_value)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_blacklist_active ON blacklist(is_active)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_attack_logs_ip ON attack_logs(client_ip)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_attack_logs_created ON attack_logs(created_at)
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

class BlacklistItem(BaseModel):
    item_type: str  # 'url', 'domain', 'ip', 'hash'
    item_value: str
    threat_type: Optional[str] = None
    notes: Optional[str] = None

@app.get("/")
def index():
    return {"status": "online", "mensagem": "Sistema de proteção educacional ativo."}

def _verify_link_internal(url: str) -> dict:
    """
    Função auxiliar para verificar link (evita duplicação de código)
    """
    # Adicionar protocolo se não tiver
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Verificar confiabilidade
    trust_result = verify_link_trust(url)
    
    # Verificar se está na blacklist
    parsed = urlparse(url)
    domain = parsed.netloc
    
    is_blacklisted = check_blacklist('url', url) or check_blacklist('domain', domain)
    
    if is_blacklisted:
        trust_result['is_trusted'] = False
        trust_result['trust_score'] = 0
        trust_result['trust_level'] = 'não confiável'
        trust_result['trust_icon'] = '❌'
        if 'issues' not in trust_result:
            trust_result['issues'] = []
        trust_result['issues'].append("URL ou domínio está na blacklist")
        trust_result['recommendation'] = "Este link foi bloqueado por segurança. NÃO acesse."
    
    return trust_result

@app.get("/verify/{url:path}")
def verify_link(url: str):
    """
    Verifica se um link é confiável ou não
    Exemplo: GET /verify/https://example.com
    """
    try:
        return _verify_link_internal(url)
    except Exception as e:
        logger.error("Erro ao verificar link: %s", e)
        raise HTTPException(status_code=400, detail=f"Erro ao verificar link: {str(e)}")

@app.post("/verify")
def verify_link_post(payload: SubmitURL):
    """
    Verifica se um link é confiável ou não (POST)
    """
    try:
        return _verify_link_internal(str(payload.url))
    except Exception as e:
        logger.error("Erro ao verificar link: %s", e)
        raise HTTPException(status_code=400, detail=f"Erro ao verificar link: {str(e)}")

@app.post("/submit")
def submit(payload: SubmitURL, request: Request):
    """Envia URL para análise"""
    url_str = str(payload.url)
    
    # Obter IP do cliente
    client_ip = request.client.host if request.client else "unknown"
    if request.headers.get("x-forwarded-for"):
        client_ip = request.headers.get("x-forwarded-for").split(",")[0].strip()
    
    # Verificar blacklist primeiro
    if check_blacklist('url', url_str):
        logger.warning("URL na blacklist: %s", url_str)
        raise HTTPException(status_code=403, detail="URL está na blacklist e foi bloqueada")
    
    # Verificar se IP está bloqueado
    if check_blacklist('ip', client_ip):
        logger.warning("IP bloqueado tentou acessar: %s", client_ip)
        raise HTTPException(status_code=403, detail="Seu IP foi bloqueado por atividades suspeitas")
    
    # Extrair domínio para verificar blacklist
    parsed = urlparse(url_str)
    domain = parsed.netloc
    if domain and check_blacklist('domain', domain):
        logger.warning("Domínio na blacklist: %s", domain)
        raise HTTPException(status_code=403, detail="Domínio está na blacklist e foi bloqueado")
    
    # Validar URL
    is_valid, error_msg = validate_url(payload.url)
    if not is_valid:
        logger.warning("URL bloqueada: %s - %s", payload.url, error_msg)
        raise HTTPException(status_code=400, detail=f"URL inválida ou bloqueada: {error_msg}")
    
    # Análise rápida de ataques na URL
    attack_analysis = analyze_url_for_attacks(url_str)
    if attack_analysis.get('is_malicious', False):
        # Extrair metadados do ataque
        attack_metadata = extract_attack_metadata(dict(request.headers), client_ip)
        attack_metadata.update({
            'threat_type': 'url_attack',
            'risk_level': attack_analysis.get('risk_level', 'high'),
            'target_url': url_str,
            'threat_analysis': attack_analysis,
            'payload': url_str
        })
        
        # Criar relatório forense
        attack_report = create_attack_report(attack_metadata)
        
        # Registrar ataque no banco
        try:
            with get_db() as conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO attack_logs (client_ip, attack_type, risk_level, metadata, report, created_at)
                    VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s)
                """, (
                    client_ip,
                    attack_analysis.get('threats', [{}])[0].get('type', 'unknown') if attack_analysis.get('threats') else 'unknown',
                    attack_analysis.get('risk_level', 'high'),
                    json.dumps(attack_metadata),
                    json.dumps(attack_report),
                    datetime.now()
                ))
                conn.commit()
                cur.close()
        except Exception as e:
            logger.error("Erro ao registrar ataque: %s", e)
        
        # Verificar se deve bloquear IP
        try:
            with get_db() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT metadata FROM attack_logs 
                    WHERE client_ip = %s 
                    AND created_at > %s
                """, (client_ip, datetime.now() - timedelta(hours=24)))
                recent_attacks = [json.loads(row[0]) for row in cur.fetchall()]
                cur.close()
                
                should_block, reason = should_block_ip(client_ip, recent_attacks)
                if should_block:
                    # Bloquear IP automaticamente
                    add_to_blacklist('ip', client_ip, threat_type='repeated_attacks',
                                   notes=f"Bloqueado automaticamente: {reason}")
                    logger.warning("IP bloqueado automaticamente: %s - %s", client_ip, reason)
        except Exception as e:
            logger.error("Erro ao verificar bloqueio de IP: %s", e)
        
        # Adicionar à blacklist automaticamente
        add_to_blacklist('url', url_str, threat_type='attack_detected', 
                        notes=f"Ataque detectado: {attack_analysis.get('risk_level')}")
        
        # Adicionar à quarentena
        if should_quarantine(attack_analysis):
            add_to_quarantine('url', url_str, attack_analysis, 
                            attack_analysis.get('risk_level', 'high'),
                            notes="Ataque detectado na URL")
        
        logger.warning("Ataque detectado na URL: %s - %s - IP: %s", url_str, attack_analysis.get('risk_level'), client_ip)
        raise HTTPException(
            status_code=403, 
            detail=f"Ataque detectado: {', '.join([t.get('type', 'unknown') for t in attack_analysis.get('threats', [])[:3]])}"
        )
    
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

@app.post("/quarantine/file")
async def quarantine_file(file: UploadFile = File(...)):
    """Analisa e coloca arquivo em quarentena se necessário"""
    # Criar arquivo temporário
    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            shutil.copyfileobj(file.file, tmp)
            temp_file = tmp.name
        
        # Analisar arquivo
        from quarantine import analyze_file_content
        analysis = analyze_file_content(temp_file)
        
        # Se for malicioso, adicionar à quarentena
        if should_quarantine(analysis):
            quarantine_id = add_to_quarantine(
                'file',
                analysis.get('file_hash', ''),
                analysis,
                analysis.get('risk_level', 'high'),
                notes=f"Arquivo: {file.filename}"
            )
            
            # Adicionar hash à blacklist
            if analysis.get('file_hash'):
                add_to_blacklist('hash', analysis['file_hash'], 
                               threat_type='malware',
                               notes=f"Arquivo malicioso: {file.filename}")
            
            return {
                "quarantined": True,
                "quarantine_id": quarantine_id,
                "analysis": analysis,
                "message": "Arquivo colocado em quarentena"
            }
        else:
            return {
                "quarantined": False,
                "analysis": analysis,
                "message": "Arquivo seguro"
            }
    finally:
        # Limpar arquivo temporário
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)

@app.get("/quarantine")
def list_quarantine(status: Optional[str] = None, limit: int = 100):
    """Lista itens em quarentena"""
    from quarantine_api import get_quarantine_items
    items = get_quarantine_items(status, limit)
    return {"items": items, "total": len(items)}

@app.post("/quarantine/{quarantine_id}/release")
def release_from_quarantine(quarantine_id: int, user_id: Optional[int] = None):
    """Libera item da quarentena"""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE quarantine 
                SET status = 'released', released_at = %s, released_by = %s
                WHERE id = %s
            """, (datetime.now(), user_id, quarantine_id))
            conn.commit()
            cur.close()
            return {"message": "Item liberado da quarentena", "quarantine_id": quarantine_id}
    except Exception as e:
        logger.error("Erro ao liberar da quarentena: %s", e)
        raise HTTPException(status_code=500, detail=f"Erro ao liberar: {str(e)}")

@app.post("/blacklist")
def add_blacklist_item(item: BlacklistItem, user_id: Optional[int] = None):
    """Adiciona item à blacklist"""
    try:
        blacklist_id = add_to_blacklist(
            item.item_type,
            item.item_value,
            item.threat_type,
            item.notes,
            user_id
        )
        return {"message": "Item adicionado à blacklist", "blacklist_id": blacklist_id}
    except Exception as e:
        logger.error("Erro ao adicionar à blacklist: %s", e)
        raise HTTPException(status_code=500, detail=f"Erro ao adicionar: {str(e)}")

@app.get("/blacklist")
def list_blacklist(limit: int = 100):
    """Lista itens da blacklist"""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, item_type, item_value, threat_type, added_at, is_active, notes
                FROM blacklist
                WHERE is_active = true
                ORDER BY added_at DESC
                LIMIT %s
            """, (limit,))
            rows = cur.fetchall()
            cur.close()
            
            items = []
            for row in rows:
                items.append({
                    'id': row[0],
                    'item_type': row[1],
                    'item_value': row[2],
                    'threat_type': row[3],
                    'added_at': row[4].isoformat() if row[4] else None,
                    'is_active': row[5],
                    'notes': row[6]
                })
            return {"items": items, "total": len(items)}
    except Exception as e:
        logger.error("Erro ao listar blacklist: %s", e)
        raise HTTPException(status_code=500, detail=f"Erro ao listar: {str(e)}")

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

