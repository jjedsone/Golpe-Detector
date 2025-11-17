"""
Validação de URLs para evitar ataques
"""
import re
import socket
from urllib.parse import urlparse
import ipaddress

# URLs e IPs bloqueados
BLOCKED_DOMAINS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    '::1',
]

# Redes privadas bloqueadas
PRIVATE_NETWORKS = [
    '10.0.0.0/8',
    '172.16.0.0/12',
    '192.168.0.0/16',
    '127.0.0.0/8',
    '169.254.0.0/16',
]

def is_private_ip(ip):
    """Verifica se IP é privado"""
    try:
        ip_obj = ipaddress.ip_address(ip)
        for network in PRIVATE_NETWORKS:
            if ip_obj in ipaddress.ip_network(network, strict=False):
                return True
    except:
        pass
    return False

def resolve_hostname(hostname):
    """Resolve hostname para IP"""
    try:
        return socket.gethostbyname(hostname)
    except:
        return None

def validate_url(url):
    """
    Valida URL e retorna (is_valid, error_message)
    """
    try:
        parsed = urlparse(str(url))
        hostname = parsed.hostname
        
        if not hostname:
            return False, "URL sem hostname"
        
        # Verificar domínios bloqueados
        if hostname.lower() in BLOCKED_DOMAINS:
            return False, f"Domínio bloqueado: {hostname}"
        
        # Verificar se é IP
        try:
            ip = ipaddress.ip_address(hostname)
            if is_private_ip(hostname):
                return False, f"IP privado bloqueado: {hostname}"
        except:
            # É hostname, resolver para IP
            ip = resolve_hostname(hostname)
            if ip and is_private_ip(ip):
                return False, f"Hostname resolve para IP privado: {hostname} -> {ip}"
        
        # Verificar protocolo
        if parsed.scheme not in ['http', 'https']:
            return False, f"Protocolo não permitido: {parsed.scheme}"
        
        # Verificar portas bloqueadas
        if parsed.port:
            blocked_ports = [22, 3306, 5432, 6379, 27017]  # SSH, MySQL, PostgreSQL, Redis, MongoDB
            if parsed.port in blocked_ports:
                return False, f"Porta bloqueada: {parsed.port}"
        
        return True, None
        
    except Exception as e:
        return False, f"Erro ao validar URL: {str(e)}"

