# Standard library imports
import json
import logging
import re
import socket
import ssl
import traceback
from contextlib import contextmanager
from datetime import datetime
from urllib.parse import urlparse

# Third-party imports
# Try to import playwright, will be available in Docker
try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False
    # Dummy function for linting purposes
    def sync_playwright():
        raise ImportError("Playwright não está instalado. Execute: playwright install chromium")

# Try to import tldextract, fallback to manual extraction
try:
    import tldextract
    HAS_TLDEXTRACT = True
except ImportError:
    HAS_TLDEXTRACT = False

# Local imports
from db_pool import get_db_conn, return_db_conn
from metrics import track_worker_job
from quarantine import analyze_url_for_attacks, should_quarantine
from quarantine_api import add_to_quarantine, check_blacklist, add_to_blacklist
import json

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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

def simple_domain_check(url):
    """Extrai domínio base da URL"""
    parsed = urlparse(url)
    domain = parsed.netloc
    
    if HAS_TLDEXTRACT:
        ext = tldextract.extract(domain)
        return f"{ext.domain}.{ext.suffix}"
    else:
        # Fallback: extração manual simples
        # Remove porta se houver
        domain = domain.split(':')[0]
        # Divide por pontos e pega últimas 2 partes (ex: example.com.br -> com.br)
        parts = domain.split('.')
        if len(parts) >= 2:
            return '.'.join(parts[-2:])
        return domain

def check_tls(hostname):
    """Verifica certificado TLS"""
    try:
        context = ssl.create_default_context()
        with socket.create_connection((hostname, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                # Verificar se é autoassinado ou inválido
                issuer = dict(x[0] for x in cert.get('issuer', []))
                if 'organizationName' in issuer:
                    return True, None
                return False, "Certificado suspeito ou autoassinado"
    except ssl.SSLError as e:
        return False, f"Erro SSL: {str(e)}"
    except Exception as e:
        return False, f"Erro ao conectar: {str(e)}"

def levenshtein_distance(s1, s2):
    """Calcula distância de Levenshtein entre duas strings"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def check_typosquatting(domain):
    """Verifica se domínio parece typosquatting (heurística simples)"""
    # Lista de domínios oficiais conhecidos
    official_domains = [
        "banco.com.br", "itau.com.br", "bradesco.com.br",
        "bb.com.br", "santander.com.br", "nubank.com.br",
        "picpay.com", "mercadopago.com", "pagseguro.com.br"
    ]
    
    for official in official_domains:
        dist = levenshtein_distance(domain.lower(), official.lower())
        if dist <= 2 and dist > 0:  # Similar mas diferente
            return True, f"Domínio similar a {official} (distância: {dist})"
    return False, None

def update_status(job_id, status, result=None, error_message=None):
    """Atualiza status da submissão no banco"""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            if result:
                cur.execute("""
                    UPDATE submissions 
                    SET status = %s, 
                        result = %s::jsonb, 
                        processed_at = %s,
                        error_message = %s
                    WHERE job_id = %s
                """, (status, json.dumps(result), datetime.now(), error_message, job_id))
            else:
                cur.execute("""
                    UPDATE submissions 
                    SET status = %s,
                        error_message = %s
                    WHERE job_id = %s
                """, (status, error_message, job_id))
            conn.commit()
            cur.close()
            logger.info("Status atualizado: %s -> %s", job_id, status)
    except Exception as e:
        logger.error("Erro ao atualizar status %s: %s", job_id, e)

def finalize_result(result, job_id):
    """Finaliza resultado com classificação e dicas pedagógicas, salva no banco"""
    try:
        # Classificação final
        if result['score'] >= 50:
            level = "alto"
        elif result['score'] >= 20:
            level = "médio"
        else:
            level = "baixo"
        
        # Gerar dicas pedagógicas
        tips = []
        check_names = [c['name'] for c in result['checks']]
        
        if 'suspicious_form' in check_names:
            tips.append("⚠️ A página solicita dados sensíveis (senha/CPF). Nunca insira essas informações em links recebidos por email, SMS ou WhatsApp.")
        
        if 'tls' in check_names:
            tips.append("🔒 O site não possui certificado HTTPS válido. Sites legítimos sempre usam HTTPS.")
        
        if 'typosquatting' in check_names:
            tips.append("🔤 O domínio parece similar a um site oficial, mas com pequenas diferenças. Sempre verifique o endereço completo antes de inserir dados.")
        
        if 'auto_submit' in check_names:
            tips.append("⚡ O site tenta enviar formulários automaticamente. Isso é um sinal comum de golpes.")
        
        if 'multiple_redirects' in check_names:
            tips.append("🔄 Múltiplos redirecionamentos podem esconder o destino real do link.")
        
        if not tips:
            tips = ["✅ Parece seguro, mas sempre confira o domínio e evite clicar em links desconhecidos."]
        
        result['level'] = level
        result['tips'] = tips[:3]  # Máximo 3 dicas
        
        # Salvar no banco
        update_status(job_id, 'done', result=result)
        logger.info("Análise concluída: %s - Nível: %s", job_id, level)
        track_worker_job(success=True)
        
        return result
    except Exception as e:
        logger.error("Erro ao finalizar resultado %s: %s", job_id, e)
        update_status(job_id, 'failed', error_message=str(e))
        track_worker_job(success=False)
        raise

def analyze_url(url, user_id, job_id):
    """Função principal de análise - executada pelo worker"""
    logger.info("Iniciando análise: %s - %s", job_id, url)
    
    result = {
        "url": str(url),
        "job_id": job_id,
        "checks": [],
        "score": 0
    }
    
    try:
        # Atualizar status para processing
        update_status(job_id, 'processing')
    
        parsed = urlparse(str(url))
        hostname = parsed.hostname
        
        if not hostname:
            result['checks'].append({
                "name": "invalid_url",
                "ok": False,
                "reason": "URL inválida"
            })
            result['score'] = 100
            return finalize_result(result, job_id)
    
        # 1. Verificar TLS
        try:
            tls_ok, tls_reason = check_tls(hostname)
            if not tls_ok:
                result['checks'].append({
                    "name": "tls",
                    "ok": False,
                    "reason": tls_reason or "Certificado TLS inválido ou ausente"
                })
                result['score'] += 30
        except Exception as e:
            logger.warning("Erro ao verificar TLS para %s: %s", hostname, e)
        
        # 2. Verificar typosquatting
        try:
            domain = simple_domain_check(str(url))
            is_typo, typo_reason = check_typosquatting(domain)
            if is_typo:
                result['checks'].append({
                    "name": "typosquatting",
                    "ok": False,
                    "reason": typo_reason
                })
                result['score'] += 40
        except Exception as e:
            logger.warning("Erro ao verificar typosquatting: %s", e)
        
        # 3. Análise com Playwright
        if not HAS_PLAYWRIGHT:
            raise ImportError("Playwright não está instalado. Execute: playwright install chromium")
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-setuid-sandbox"]
                )
                page = browser.new_page()
                
                try:
                    page.goto(str(url), timeout=30000, wait_until="domcontentloaded")
                    content = page.content()
                    title = page.title()
                    
                    # Análise de ataques no conteúdo
                    attack_analysis = analyze_url_for_attacks(str(url), content)
                    if attack_analysis.get('is_malicious', False):
                        result['checks'].append({
                            "name": "attack_detected",
                            "ok": False,
                            "reason": f"Ataques detectados: {', '.join(set([t.get('type', 'unknown') for t in attack_analysis.get('threats', [])[:5]]))}",
                            "details": {
                                "threats": attack_analysis.get('threats', [])[:10],
                                "risk_level": attack_analysis.get('risk_level')
                            }
                        })
                        result['score'] += 100  # Score máximo para ataques
                        
                        # Adicionar à quarentena se necessário
                        if should_quarantine(attack_analysis):
                            try:
                                add_to_quarantine('url', str(url), attack_analysis,
                                                attack_analysis.get('risk_level', 'critical'),
                                                notes="Ataque detectado durante análise")
                                # Adicionar à blacklist
                                add_to_blacklist('url', str(url), threat_type='attack_detected')
                            except Exception as e:
                                logger.warning("Erro ao adicionar à quarentena: %s", e)
                    
                    # Detectar formulários suspeitos
                    forms = page.query_selector_all("form")
                    suspicious_forms = []
                    
                    for form in forms:
                        inputs = form.query_selector_all("input")
                        names = []
                        for inp in inputs:
                            name = inp.get_attribute("name") or inp.get_attribute("id") or ""
                            input_type = inp.get_attribute("type") or ""
                            names.append(name.lower())
                            
                            if input_type.lower() == "password":
                                suspicious_forms.append({"field": name, "type": "password"})
                        
                        # Verificar se pede dados sensíveis
                        form_text = " ".join(names)
                        if re.search(r"pass|senha|password|cpf|doc|pin|cartão|card", form_text, re.IGNORECASE):
                            suspicious_forms.append({"fields": names})
                    
                    if suspicious_forms:
                        result['checks'].append({
                            "name": "suspicious_form",
                            "ok": False,
                            "reason": "Formulário solicita credenciais/dados sensíveis",
                            "details": suspicious_forms
                        })
                        result['score'] += 40
                    
                    # Verificar auto-submit
                    if re.search(r"document\.forms|form\.submit\(|\.submit\(\)", content, re.IGNORECASE):
                        result['checks'].append({
                            "name": "auto_submit",
                            "ok": False,
                            "reason": "Formulário com possível envio automático via JavaScript"
                        })
                        result['score'] += 10
                    
                    # Verificar redirecionamentos
                    try:
                        redirects = page.evaluate("""() => {
                            return window.performance.getEntriesByType('navigation')[0].redirectCount || 0;
                        }""")
                        
                        if redirects and redirects > 2:
                            result['checks'].append({
                                "name": "multiple_redirects",
                                "ok": False,
                                "reason": f"Múltiplos redirecionamentos detectados ({redirects})"
                            })
                            result['score'] += 15
                    except:
                        pass  # Ignora se não conseguir obter redirects
                    
                    # Verificar título suspeito
                    if re.search(r"login|entrar|acessar", title.lower()) and not re.search(r"banco|bank|oficial", title.lower(), re.IGNORECASE):
                        result['checks'].append({
                            "name": "title_login",
                            "ok": False,
                            "reason": f"Título sugere página de login: '{title}'"
                        })
                        result['score'] += 5
                    
                    # Verificar scripts suspeitos
                    scripts = page.query_selector_all("script")
                    suspicious_scripts = 0
                    for script in scripts:
                        script_content = script.inner_text() or ""
                        if re.search(r"atob|btoa|eval|unescape|String\.fromCharCode", script_content):
                            suspicious_scripts += 1
                    
                    if suspicious_scripts > 0:
                        result['checks'].append({
                            "name": "obfuscated_scripts",
                            "ok": False,
                            "reason": f"Scripts ofuscados detectados ({suspicious_scripts})"
                        })
                        result['score'] += 10
                        
                except Exception as e:
                    result['checks'].append({
                        "name": "error_loading",
                        "ok": False,
                        "reason": f"Erro ao carregar página: {str(e)[:100]}"
                    })
                    result['score'] += 20
                finally:
                    browser.close()
        except Exception as e:
            logger.warning("Erro no Playwright para %s: %s", url, e)
            result['checks'].append({
                "name": "playwright_error",
                "ok": False,
                "reason": f"Erro no Playwright: {str(e)[:100]}"
            })
            result['score'] += 25
        
        return finalize_result(result, job_id)
        
    except Exception as e:
        error_msg = f"Erro crítico na análise: {str(e)}"
        error_trace = traceback.format_exc()
        logger.error("Erro crítico em %s: %s\n%s", job_id, error_msg, error_trace)
        update_status(job_id, 'failed', error_message=error_msg)
        track_worker_job(success=False)
        raise

