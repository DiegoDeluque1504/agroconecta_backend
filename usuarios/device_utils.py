import re

def get_client_ip(request):
    """
    Obtiene la dirección IP real del cliente considerando proxies (como Render o Cloudflare).
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def parse_user_agent(user_agent_string):
    """
    Analiza de forma simple el User-Agent para extraer el sistema operativo y el navegador.
    """
    if not user_agent_string:
        return 'Desconocido', 'Desconocido'
        
    ua = user_agent_string.lower()
    
    # Detección de Sistema Operativo
    if 'windows' in ua:
        os = 'Windows'
    elif 'android' in ua:
        os = 'Android'
    elif 'iphone' in ua or 'ipad' in ua:
        os = 'iOS'
    elif 'macintosh' in ua or 'mac os' in ua:
        os = 'macOS'
    elif 'linux' in ua:
        os = 'Linux'
    else:
        os = 'Desconocido'
        
    # Detección de Navegador
    if 'edge' in ua or 'edg/' in ua:
        browser = 'Edge'
    elif 'opera' in ua or 'opr/' in ua:
        browser = 'Opera'
    elif 'chrome' in ua or 'crios' in ua:
        browser = 'Chrome'
    elif 'firefox' in ua or 'fxios' in ua:
        browser = 'Firefox'
    elif 'safari' in ua and 'chrome' not in ua:
        browser = 'Safari'
    else:
        browser = 'Otro'
        
    return browser, os
