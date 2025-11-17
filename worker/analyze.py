import json
import re
import socket
import ssl
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse
import tldextract
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from models import Submission

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://golpe_user:golpe_pass@localhost:5432/golpe_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def simple_domain_check(url):
    """Extrai domínio base da URL"""
    parsed = urlparse(url)
    domain = parsed.netloc
    ext = tldextract.extract(domain)
    return f"{ext.domain}.{ext.suffix}"

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

def check_typosquatting(domain):
    """Verifica se domínio parece typosquatting (heurística simples)"""
    # Lista de domínios oficiais conhecidos (exemplo)
    official_domains = [
        "banco.com.br", "itau.com.br", "bradesco.com.br",
        "bb.com.br", "santander.com.br", "nubank.com.br"
    ]
    
    try:
        from Levenshtein import distance
    except ImportError:
        # Fallback simples se Levenshtein não estiver instalado
        def distance(s1, s2):
            if len(s1) < len(s2):
                return distance(s2, s1)
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
    
    for official in official_domains:
        dist = distance(domain.lower(), official.lower())
        if dist <= 2 and dist > 0:  # Similar mas diferente
            return True, f"Domínio similar a {official} (distância: {dist})"
    return False, None

def analyze_url(url, user_id, job_id):
    """Função principal de análise - executada pelo worker"""
    result = {
        "url": url,
        "job_id": job_id,
        "checks": [],
        "score": 0
    }
    
    parsed = urlparse(url)
    hostname = parsed.hostname
    
    if not hostname:
        result['checks'].append({
            "name": "invalid_url",
            "ok": False,
            "reason": "URL inválida"
        })
        result['score'] = 100
        return finalize_result(result)
    
    # 1. Verificar TLS
    tls_ok, tls_reason = check_tls(hostname)
    if not tls_ok:
        result['checks'].append({
            "name": "tls",
            "ok": False,
            "reason": tls_reason or "Certificado TLS inválido ou ausente"
        })
        result['score'] += 30
    
    # 2. Verificar typosquatting
    domain = simple_domain_check(url)
    is_typo, typo_reason = check_typosquatting(domain)
    if is_typo:
        result['checks'].append({
            "name": "typosquatting",
            "ok": False,
            "reason": typo_reason
        })
        result['score'] += 40
    
    # 3. Análise com Playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        page = browser.new_page()
        
        try:
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            content = page.content()
            title = page.title()
            
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
            
            # Verificar redirecionamentos (contar quantos ocorreram)
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
    
    return finalize_result(result)

def finalize_result(result):
    """Finaliza resultado com classificação e dicas pedagógicas"""
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
    db = SessionLocal()
    try:
        submission = db.query(Submission).filter(Submission.job_id == result['job_id']).first()
        if submission:
            submission.status = "done"
            submission.result = result
            submission.processed_at = datetime.now()
            db.commit()
    except Exception as e:
        print(f"Erro ao salvar resultado: {e}")
    finally:
        db.close()
    
    return result

