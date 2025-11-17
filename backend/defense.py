"""
Sistema de Defesa e Análise Forense
Coleta informações sobre atacantes de forma legal e ética
"""
import ipaddress
import socket
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def get_ip_info(ip: str) -> Dict:
    """
    Obtém informações públicas sobre um IP (geolocalização, ISP, etc)
    Usa APIs públicas legais
    """
    try:
        # Verificar se é IP válido
        ipaddress.ip_address(ip)
        
        info = {
            'ip': ip,
            'is_private': ipaddress.ip_address(ip).is_private,
            'is_loopback': ipaddress.ip_address(ip).is_loopback,
            'ip_type': 'IPv4' if '.' in ip else 'IPv6',
            'timestamp': datetime.now().isoformat()
        }
        
        # Para IPs privados, não tentar geolocalização
        if info['is_private']:
            info['location'] = 'Private Network'
            info['isp'] = 'Local Network'
            return info
        
        # Tentar reverse DNS (legal e público)
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            info['hostname'] = hostname
        except:
            info['hostname'] = None
        
        # Informações básicas de rede
        try:
            # Verificar se IP está em ranges conhecidos de VPN/Proxy
            # (lista simplificada - em produção usar banco de dados atualizado)
            vpn_ranges = [
                ipaddress.ip_network('10.0.0.0/8'),
                ipaddress.ip_network('172.16.0.0/12'),
            ]
            info['is_vpn'] = any(ipaddress.ip_address(ip) in net for net in vpn_ranges)
        except:
            info['is_vpn'] = False
        
        return info
    except Exception as e:
        logger.error("Erro ao obter informações do IP %s: %s", ip, e)
        return {'ip': ip, 'error': str(e)}

def extract_attack_metadata(request_headers: Dict, client_ip: str) -> Dict:
    """
    Extrai metadados do ataque de forma legal
    Apenas informações já disponíveis na requisição HTTP
    """
    metadata = {
        'client_ip': client_ip,
        'timestamp': datetime.now().isoformat(),
        'user_agent': request_headers.get('user-agent', 'Unknown'),
        'referer': request_headers.get('referer'),
        'accept_language': request_headers.get('accept-language'),
        'accept_encoding': request_headers.get('accept-encoding'),
        'connection': request_headers.get('connection'),
        'x_forwarded_for': request_headers.get('x-forwarded-for'),
        'x_real_ip': request_headers.get('x-real-ip'),
    }
    
    # Informações do IP
    ip_info = get_ip_info(client_ip)
    metadata['ip_info'] = ip_info
    
    # Detectar se está usando proxy/VPN
    if metadata.get('x_forwarded_for'):
        metadata['is_proxied'] = True
        metadata['original_ip'] = metadata['x_forwarded_for'].split(',')[0].strip()
    else:
        metadata['is_proxied'] = False
    
    # Análise do User-Agent
    user_agent = metadata['user_agent'].lower()
    metadata['browser'] = 'Unknown'
    metadata['os'] = 'Unknown'
    metadata['is_bot'] = False
    
    if 'bot' in user_agent or 'crawler' in user_agent or 'spider' in user_agent:
        metadata['is_bot'] = True
    
    # Detectar browser
    if 'chrome' in user_agent and 'edg' not in user_agent:
        metadata['browser'] = 'Chrome'
    elif 'firefox' in user_agent:
        metadata['browser'] = 'Firefox'
    elif 'safari' in user_agent and 'chrome' not in user_agent:
        metadata['browser'] = 'Safari'
    elif 'edg' in user_agent:
        metadata['browser'] = 'Edge'
    
    # Detectar OS
    if 'windows' in user_agent:
        metadata['os'] = 'Windows'
    elif 'linux' in user_agent:
        metadata['os'] = 'Linux'
    elif 'mac' in user_agent or 'darwin' in user_agent:
        metadata['os'] = 'macOS'
    elif 'android' in user_agent:
        metadata['os'] = 'Android'
    elif 'ios' in user_agent or 'iphone' in user_agent:
        metadata['os'] = 'iOS'
    
    return metadata

def analyze_attack_pattern(attack_data: Dict) -> Dict:
    """
    Analisa padrões de ataque para identificar características do atacante
    """
    pattern = {
        'attack_type': attack_data.get('threat_type', 'unknown'),
        'frequency': 1,
        'first_seen': attack_data.get('timestamp'),
        'last_seen': attack_data.get('timestamp'),
        'ip_addresses': [attack_data.get('client_ip')],
        'user_agents': [attack_data.get('user_agent', 'Unknown')],
        'targets': [attack_data.get('target_url', 'Unknown')],
        'risk_score': 0
    }
    
    # Calcular score de risco
    risk_score = 0
    
    # IP privado = menor risco (pode ser teste interno)
    if attack_data.get('ip_info', {}).get('is_private'):
        risk_score += 10
    else:
        risk_score += 50
    
    # Múltiplos IPs = possível botnet
    if len(pattern['ip_addresses']) > 1:
        risk_score += 30
    
    # Bot = possível automação
    if attack_data.get('is_bot'):
        risk_score += 20
    
    # Ataque crítico = maior risco
    if attack_data.get('risk_level') == 'critical':
        risk_score += 100
    elif attack_data.get('risk_level') == 'high':
        risk_score += 50
    
    pattern['risk_score'] = risk_score
    
    return pattern

def should_block_ip(ip: str, attack_history: List[Dict]) -> Tuple[bool, str]:
    """
    Decide se deve bloquear um IP baseado no histórico de ataques
    """
    # Contar ataques recentes (últimas 24 horas)
    recent_attacks = [
        a for a in attack_history 
        if a.get('client_ip') == ip and 
        datetime.fromisoformat(a.get('timestamp', datetime.now().isoformat())) > 
        datetime.now() - timedelta(hours=24)
    ]
    
    attack_count = len(recent_attacks)
    
    # Bloquear se:
    # - Mais de 10 ataques nas últimas 24h
    # - Mais de 3 ataques críticos
    # - Mais de 5 ataques de alta severidade
    
    critical_attacks = [a for a in recent_attacks if a.get('risk_level') == 'critical']
    high_attacks = [a for a in recent_attacks if a.get('risk_level') == 'high']
    
    if len(critical_attacks) >= 3:
        return True, f"3+ ataques críticos detectados"
    
    if len(high_attacks) >= 5:
        return True, f"5+ ataques de alta severidade"
    
    if attack_count >= 10:
        return True, f"{attack_count} ataques nas últimas 24h"
    
    return False, ""

def create_attack_report(attack_data: Dict) -> Dict:
    """
    Cria relatório forense completo do ataque
    Para uso legal e reporte às autoridades
    """
    report = {
        'report_id': f"ATK-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{attack_data.get('client_ip', 'unknown').replace('.', '-')}",
        'timestamp': datetime.now().isoformat(),
        'attack_details': {
            'type': attack_data.get('threat_type', 'unknown'),
            'severity': attack_data.get('risk_level', 'unknown'),
            'target': attack_data.get('target_url', 'unknown'),
            'payload': attack_data.get('payload', '')[:500],  # Limitar tamanho
        },
        'attacker_info': {
            'ip_address': attack_data.get('client_ip'),
            'ip_information': attack_data.get('ip_info', {}),
            'user_agent': attack_data.get('user_agent'),
            'browser': attack_data.get('browser'),
            'os': attack_data.get('os'),
            'is_bot': attack_data.get('is_bot', False),
            'is_proxied': attack_data.get('is_proxied', False),
        },
        'network_info': {
            'referer': attack_data.get('referer'),
            'x_forwarded_for': attack_data.get('x_forwarded_for'),
            'connection_type': attack_data.get('connection'),
        },
        'threat_analysis': attack_data.get('threat_analysis', {}),
        'recommendations': [
            'Bloquear IP imediatamente',
            'Adicionar à blacklist permanente',
            'Reportar às autoridades se necessário',
            'Monitorar padrões similares',
        ]
    }
    
    return report

