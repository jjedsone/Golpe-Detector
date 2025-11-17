"""
Sistema de Verificação de Confiabilidade de Links
Analisa múltiplos fatores para determinar se um link é confiável
"""
import re
from urllib.parse import urlparse
from typing import Dict, List, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Domínios conhecidos como confiáveis
TRUSTED_DOMAINS = [
    'google.com', 'youtube.com', 'facebook.com', 'twitter.com', 'instagram.com',
    'linkedin.com', 'github.com', 'stackoverflow.com', 'wikipedia.org',
    'amazon.com', 'microsoft.com', 'apple.com', 'netflix.com',
    'gov.br', 'gov.uk', 'gov.au', 'gov.ca',  # Sites governamentais
    'edu.br', 'edu',  # Instituições educacionais
    'itau.com.br', 'bradesco.com.br', 'bb.com.br', 'santander.com.br',  # Bancos oficiais
    'nubank.com.br', 'picpay.com', 'mercadopago.com', 'pagseguro.com.br'
]

# Padrões suspeitos em URLs
SUSPICIOUS_PATTERNS = [
    r'bit\.ly|tinyurl|t\.co|goo\.gl|ow\.ly',  # Encurtadores de URL
    r'\d+\.\d+\.\d+\.\d+',  # IP direto
    r'[a-z0-9-]+\.tk|\.ml|\.ga|\.cf',  # Domínios gratuitos suspeitos
    r'[a-z0-9-]+-[a-z0-9-]+-[a-z0-9-]+',  # Múltiplos hífens
    r'[0-9]{4,}',  # Muitos números
]

# Palavras-chave suspeitas
SUSPICIOUS_KEYWORDS = [
    'click', 'verify', 'confirm', 'update', 'secure', 'account',
    'suspended', 'locked', 'urgent', 'immediate', 'action-required',
    'prize', 'winner', 'congratulations', 'free', 'limited-time'
]

def check_domain_age(domain: str) -> Tuple[bool, str]:
    """
    Verifica se domínio parece novo/suspeito
    (Em produção, usar API de WHOIS)
    """
    # Domínios muito curtos ou muito longos são suspeitos
    if len(domain) < 4:
        return False, "Domínio muito curto"
    if len(domain) > 50:
        return False, "Domínio muito longo"
    
    # Muitos números no domínio
    if len(re.findall(r'\d', domain)) > len(domain) * 0.5:
        return False, "Domínio contém muitos números"
    
    return True, "OK"

def check_url_structure(url: str) -> Tuple[int, List[str]]:
    """
    Analisa estrutura da URL
    Retorna score (0-100) e lista de problemas
    """
    score = 100
    issues = []
    
    parsed = urlparse(url)
    
    # Verificar protocolo
    if parsed.scheme != 'https':
        score -= 30
        issues.append("Não usa HTTPS")
    
    # Verificar domínio
    domain = parsed.netloc.lower()
    
    # Verificar se é IP direto
    if re.match(r'^\d+\.\d+\.\d+\.\d+', domain):
        score -= 50
        issues.append("Usa IP direto em vez de domínio")
    
    # Verificar encurtadores de URL
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, domain, re.IGNORECASE):
            score -= 20
            issues.append("Usa encurtador de URL ou domínio suspeito")
            break
    
    # Verificar múltiplos subdomínios
    subdomain_count = domain.count('.')
    if subdomain_count > 3:
        score -= 15
        issues.append("Muitos subdomínios")
    
    # Verificar caminho suspeito
    path = parsed.path.lower()
    for keyword in SUSPICIOUS_KEYWORDS:
        if keyword in path:
            score -= 10
            issues.append(f"Palavra-chave suspeita no caminho: {keyword}")
    
    # Verificar parâmetros suspeitos
    query = parsed.query.lower()
    if query:
        suspicious_params = ['redirect', 'url', 'link', 'goto', 'next']
        for param in suspicious_params:
            if param in query:
                score -= 15
                issues.append(f"Parâmetro suspeito: {param}")
    
    return max(0, score), issues

def check_domain_reputation(domain: str) -> Tuple[int, List[str]]:
    """
    Verifica reputação do domínio
    Retorna score (0-100) e lista de informações
    """
    score = 50  # Score neutro inicial
    info = []
    
    domain_lower = domain.lower()
    
    # Verificar se é domínio confiável conhecido
    for trusted in TRUSTED_DOMAINS:
        if trusted in domain_lower:
            score = 100
            info.append(f"Domínio confiável conhecido: {trusted}")
            return score, info
    
    # Verificar extensões confiáveis
    trusted_tlds = ['.com', '.org', '.net', '.edu', '.gov', '.br', '.uk', '.au', '.ca']
    has_trusted_tld = any(domain_lower.endswith(tld) for tld in trusted_tlds)
    
    if has_trusted_tld:
        score += 20
        info.append("Extensão de domínio confiável")
    else:
        score -= 20
        info.append("Extensão de domínio não comum")
    
    # Verificar domínios gratuitos suspeitos
    free_domains = ['.tk', '.ml', '.ga', '.cf', '.gq', '.xyz']
    if any(domain_lower.endswith(tld) for tld in free_domains):
        score -= 30
        info.append("Domínio gratuito (maior risco)")
    
    # Verificar estrutura do domínio
    domain_age_ok, age_msg = check_domain_age(domain)
    if not domain_age_ok:
        score -= 15
        info.append(age_msg)
    
    return max(0, min(100, score)), info

def calculate_trust_score(url: str, additional_checks: Dict = None) -> Dict:
    """
    Calcula score de confiabilidade geral (0-100)
    """
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    
    # Análise de estrutura
    structure_score, structure_issues = check_url_structure(url)
    
    # Análise de reputação
    reputation_score, reputation_info = check_domain_reputation(domain)
    
    # Score base (média ponderada)
    base_score = (structure_score * 0.4) + (reputation_score * 0.6)
    
    # Ajustes adicionais
    final_score = base_score
    all_issues = structure_issues.copy()
    all_info = reputation_info.copy()
    
    # Verificar HTTPS
    if parsed.scheme == 'https':
        final_score += 5
        all_info.append("Usa HTTPS (seguro)")
    else:
        final_score -= 10
        all_issues.append("Não usa HTTPS")
    
    # Classificação final
    if final_score >= 80:
        trust_level = "confiável"
        trust_icon = "✅"
    elif final_score >= 60:
        trust_level = "moderadamente confiável"
        trust_icon = "⚠️"
    elif final_score >= 40:
        trust_level = "suspeito"
        trust_icon = "⚠️"
    else:
        trust_level = "não confiável"
        trust_icon = "❌"
    
    result = {
        'url': url,
        'domain': domain,
        'trust_score': round(final_score, 1),
        'trust_level': trust_level,
        'trust_icon': trust_icon,
        'structure_score': structure_score,
        'reputation_score': reputation_score,
        'issues': all_issues,
        'info': all_info,
        'is_trusted': final_score >= 70,
        'recommendation': get_recommendation(final_score, all_issues),
        'analyzed_at': datetime.now().isoformat()
    }
    
    # Adicionar checks adicionais se fornecidos
    if additional_checks:
        result['additional_checks'] = additional_checks
        
        # Ajustar score baseado em checks adicionais
        if additional_checks.get('has_valid_tls'):
            final_score += 5
        if additional_checks.get('has_typosquatting'):
            final_score -= 30
        if additional_checks.get('has_suspicious_content'):
            final_score -= 20
    
    return result

def get_recommendation(score: float, issues: List[str]) -> str:
    """Gera recomendação baseada no score"""
    if score >= 80:
        return "Link parece confiável. Pode acessar com segurança."
    elif score >= 60:
        return "Link moderadamente confiável. Tenha cuidado e verifique o conteúdo."
    elif score >= 40:
        return "Link suspeito. Evite acessar ou fornecer informações pessoais."
    else:
        return "Link não confiável. NÃO acesse este link."

def verify_link_trust(url: str, include_deep_analysis: bool = False) -> Dict:
    """
    Verifica confiabilidade de um link
    """
    try:
        # Análise básica
        result = calculate_trust_score(url)
        
        # Análise profunda (opcional)
        if include_deep_analysis:
            # Aqui você pode adicionar:
            # - Verificação de TLS
            # - Verificação de typosquatting
            # - Análise de conteúdo
            # - Verificação em blacklists
            pass
        
        return result
    except Exception as e:
        logger.error("Erro ao verificar confiabilidade do link: %s", e)
        return {
            'url': url,
            'trust_score': 0,
            'trust_level': 'erro',
            'error': str(e),
            'is_trusted': False
        }

