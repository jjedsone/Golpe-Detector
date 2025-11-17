"""
API para gerenciamento de quarentena
"""
from typing import Optional, List
from datetime import datetime
import logging
import json

from quarantine import analyze_file_content, analyze_url_for_attacks, should_quarantine
from db_pool import get_db_conn, return_db_conn
from contextlib import contextmanager

logger = logging.getLogger(__name__)

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

def add_to_quarantine(item_type: str, item_identifier: str, threat_analysis: dict, 
                     risk_level: str, notes: Optional[str] = None) -> int:
    """Adiciona item à quarentena"""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO quarantine (item_type, item_identifier, threat_analysis, risk_level, notes)
                VALUES (%s, %s, %s::jsonb, %s, %s)
                RETURNING id
            """, (item_type, item_identifier, json.dumps(threat_analysis), risk_level, notes))
            
            quarantine_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            logger.info("Item adicionado à quarentena: %s - %s", item_type, item_identifier)
            return quarantine_id
    except Exception as e:
        logger.error("Erro ao adicionar à quarentena: %s", e)
        raise

def check_blacklist(item_type: str, item_value: str) -> bool:
    """Verifica se item está na blacklist"""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id FROM blacklist 
                WHERE item_type = %s AND item_value = %s AND is_active = true
            """, (item_type, item_value))
            result = cur.fetchone()
            cur.close()
            return result is not None
    except Exception as e:
        logger.error("Erro ao verificar blacklist: %s", e)
        return False

def add_to_blacklist(item_type: str, item_value: str, threat_type: Optional[str] = None,
                    notes: Optional[str] = None, user_id: Optional[int] = None) -> int:
    """Adiciona item à blacklist"""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO blacklist (item_type, item_value, threat_type, added_by, notes)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (item_value) DO UPDATE SET is_active = true
                RETURNING id
            """, (item_type, item_value, threat_type, user_id, notes))
            
            blacklist_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            logger.info("Item adicionado à blacklist: %s - %s", item_type, item_value)
            return blacklist_id
    except Exception as e:
        logger.error("Erro ao adicionar à blacklist: %s", e)
        raise

def get_quarantine_items(status: Optional[str] = None, limit: int = 100) -> List[dict]:
    """Lista itens em quarentena"""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            query = """
                SELECT id, item_type, item_identifier, threat_analysis, risk_level,
                       quarantined_at, released_at, status, notes
                FROM quarantine
            """
            params = []
            
            if status:
                query += " WHERE status = %s"
                params.append(status)
            
            query += " ORDER BY quarantined_at DESC LIMIT %s"
            params.append(limit)
            
            cur.execute(query, params)
            rows = cur.fetchall()
            cur.close()
            
            items = []
            for row in rows:
                items.append({
                    'id': row[0],
                    'item_type': row[1],
                    'item_identifier': row[2],
                    'threat_analysis': row[3],
                    'risk_level': row[4],
                    'quarantined_at': row[5].isoformat() if row[5] else None,
                    'released_at': row[6].isoformat() if row[6] else None,
                    'status': row[7],
                    'notes': row[8]
                })
            return items
    except Exception as e:
        logger.error("Erro ao listar quarentena: %s", e)
        return []
