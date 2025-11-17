"""
Sistema de Quarentena para vírus e ataques hackers
"""
import hashlib
import os
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

# Blacklist de padrões maliciosos conhecidos
MALICIOUS_PATTERNS = {
    'sql_injection': [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b.*\b(FROM|INTO|TABLE|DATABASE|WHERE)\b)",
        r"('|(\\')|(;)|(--)|(/\*)|(\*/)|(xp_)|(sp_))",
        r"(\bOR\b.*=.*)|(\bAND\b.*=.*)",
    ],
    'xss': [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
    ],
    'command_injection': [
        r"[;&|`$(){}[\]]",
        r"\b(cat|ls|pwd|whoami|id|uname|wget|curl|nc|netcat|bash|sh|python|perl|ruby)\b",
        r"(\$\{|\$\(|`.*`|;.*;|&&.*&&|\|\|.*\|\|)",
    ],
    'path_traversal': [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e%2f",
        r"%2e%2e%5c",
        r"\.\.%2f",
        r"\.\.%5c",
    ],
    'file_upload_attack': [
        r"\.(php|phtml|php3|php4|php5|phps|cgi|exe|scr|bat|cmd|com|pif|vbs|js|jar|sh|pl|py|rb|asp|aspx|jsp)\s*$",
    ],
}

# Extensões de arquivos perigosos
DANGEROUS_EXTENSIONS = [
    '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js',
    '.jar', '.sh', '.pl', '.py', '.rb', '.php', '.asp', '.aspx',
    '.jsp', '.cgi', '.dll', '.sys', '.drv', '.msi', '.app', '.deb',
    '.rpm', '.dmg', '.pkg', '.run', '.bin'
]

# Assinaturas de malware conhecidas (hashes MD5)
MALWARE_SIGNATURES = [
    # Exemplos - em produção, usar banco de dados atualizado
    # 'd41d8cd98f00b204e9800998ecf8427e',  # Exemplo
]

def calculate_file_hash(file_path: str) -> str:
    """Calcula hash MD5 de um arquivo"""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logger.error("Erro ao calcular hash do arquivo: %s", e)
        return ""

def check_malware_signature(file_hash: str) -> bool:
    """Verifica se hash do arquivo está na lista de malware conhecido"""
    return file_hash.lower() in [sig.lower() for sig in MALWARE_SIGNATURES]

def detect_sql_injection(content: str) -> List[Dict]:
    """Detecta tentativas de SQL Injection"""
    threats = []
    for pattern in MALICIOUS_PATTERNS['sql_injection']:
        matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            threats.append({
                'type': 'sql_injection',
                'severity': 'high',
                'pattern': pattern,
                'match': match.group()[:100],
                'position': match.start()
            })
    return threats

def detect_xss(content: str) -> List[Dict]:
    """Detecta tentativas de Cross-Site Scripting (XSS)"""
    threats = []
    for pattern in MALICIOUS_PATTERNS['xss']:
        matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            threats.append({
                'type': 'xss',
                'severity': 'high',
                'pattern': pattern,
                'match': match.group()[:100],
                'position': match.start()
            })
    return threats

def detect_command_injection(content: str) -> List[Dict]:
    """Detecta tentativas de Command Injection"""
    threats = []
    for pattern in MALICIOUS_PATTERNS['command_injection']:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            threats.append({
                'type': 'command_injection',
                'severity': 'critical',
                'pattern': pattern,
                'match': match.group()[:100],
                'position': match.start()
            })
    return threats

def detect_path_traversal(content: str) -> List[Dict]:
    """Detecta tentativas de Path Traversal"""
    threats = []
    for pattern in MALICIOUS_PATTERNS['path_traversal']:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            threats.append({
                'type': 'path_traversal',
                'severity': 'high',
                'pattern': pattern,
                'match': match.group()[:100],
                'position': match.start()
            })
    return threats

def analyze_file_content(file_path: str) -> Dict:
    """
    Analisa conteúdo de arquivo em busca de ameaças
    Retorna resultado da análise
    """
    result = {
        'file_path': file_path,
        'threats': [],
        'is_malicious': False,
        'risk_level': 'low',
        'file_hash': '',
        'file_size': 0,
        'analysis_timestamp': datetime.now().isoformat()
    }
    
    try:
        # Obter informações do arquivo
        file_size = os.path.getsize(file_path)
        result['file_size'] = file_size
        
        # Calcular hash
        file_hash = calculate_file_hash(file_path)
        result['file_hash'] = file_hash
        
        # Verificar assinatura de malware
        if check_malware_signature(file_hash):
            result['threats'].append({
                'type': 'known_malware',
                'severity': 'critical',
                'description': 'Arquivo corresponde a assinatura de malware conhecido',
                'hash': file_hash
            })
            result['is_malicious'] = True
            result['risk_level'] = 'critical'
            return result
        
        # Verificar extensão perigosa
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext in DANGEROUS_EXTENSIONS:
            result['threats'].append({
                'type': 'dangerous_extension',
                'severity': 'high',
                'description': f'Extensão de arquivo perigosa: {file_ext}',
                'extension': file_ext
            })
            result['risk_level'] = 'high'
        
        # Ler e analisar conteúdo (apenas para arquivos de texto)
        if file_size < 10 * 1024 * 1024:  # Apenas arquivos menores que 10MB
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(100000)  # Ler primeiros 100KB
                    
                    # Detectar ameaças
                    sql_threats = detect_sql_injection(content)
                    xss_threats = detect_xss(content)
                    cmd_threats = detect_command_injection(content)
                    path_threats = detect_path_traversal(content)
                    
                    result['threats'].extend(sql_threats)
                    result['threats'].extend(xss_threats)
                    result['threats'].extend(cmd_threats)
                    result['threats'].extend(path_threats)
                    
                    if sql_threats or xss_threats or cmd_threats or path_threats:
                        result['is_malicious'] = True
                        if cmd_threats:
                            result['risk_level'] = 'critical'
                        elif sql_threats or xss_threats:
                            result['risk_level'] = 'high'
                        else:
                            result['risk_level'] = 'medium'
            except UnicodeDecodeError:
                # Arquivo binário, não analisar conteúdo
                pass
            except Exception as e:
                logger.warning("Erro ao analisar conteúdo do arquivo: %s", e)
        
    except Exception as e:
        logger.error("Erro ao analisar arquivo %s: %s", file_path, e)
        result['error'] = str(e)
    
    return result

def analyze_url_for_attacks(url: str, content: str = None) -> Dict:
    """
    Analisa URL e conteúdo em busca de ataques
    """
    result = {
        'url': url,
        'threats': [],
        'is_malicious': False,
        'risk_level': 'low',
        'analysis_timestamp': datetime.now().isoformat()
    }
    
    # Analisar URL
    sql_threats = detect_sql_injection(url)
    xss_threats = detect_xss(url)
    cmd_threats = detect_command_injection(url)
    path_threats = detect_path_traversal(url)
    
    result['threats'].extend(sql_threats)
    result['threats'].extend(xss_threats)
    result['threats'].extend(cmd_threats)
    result['threats'].extend(path_threats)
    
    # Analisar conteúdo se fornecido
    if content:
        sql_threats_content = detect_sql_injection(content)
        xss_threats_content = detect_xss(content)
        cmd_threats_content = detect_command_injection(content)
        
        result['threats'].extend(sql_threats_content)
        result['threats'].extend(xss_threats_content)
        result['threats'].extend(cmd_threats_content)
    
    # Determinar se é malicioso
    if result['threats']:
        result['is_malicious'] = True
        severities = [t.get('severity', 'low') for t in result['threats']]
        if 'critical' in severities:
            result['risk_level'] = 'critical'
        elif 'high' in severities:
            result['risk_level'] = 'high'
        else:
            result['risk_level'] = 'medium'
    
    return result

def should_quarantine(analysis_result: Dict) -> bool:
    """Determina se deve colocar em quarentena baseado no resultado da análise"""
    if analysis_result.get('is_malicious', False):
        return True
    
    risk_level = analysis_result.get('risk_level', 'low')
    if risk_level in ['critical', 'high']:
        return True
    
    # Se tem mais de 3 ameaças detectadas
    if len(analysis_result.get('threats', [])) > 3:
        return True
    
    return False

