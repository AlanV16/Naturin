"""
Validadores personalizados para el sistema de usuarios
"""
from django.core.exceptions import ValidationError
from django.conf import settings
import re

# Dominios educativos permitidos para docentes
TEACHER_ALLOWED_DOMAINS = [
    '@unas.edu.pe',
    '@minedu.edu.pe', 
    '@ugel.pe',
    '@dre.pe',
    '@educacion.gob.pe',
]

def validate_teacher_email(email):
    """
    Valida que el email del docente pertenezca a un dominio educativo autorizado
    """
    if not email:
        raise ValidationError("El email es requerido.")
    
    email = email.lower().strip()
    
    # Verificar que el email tenga un formato válido básico
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        raise ValidationError("Formato de email inválido.")
    
    # Verificar que el dominio esté en la lista permitida
    valid_domain = False
    for domain in TEACHER_ALLOWED_DOMAINS:
        if email.endswith(domain):
            valid_domain = True
            break
    
    if not valid_domain:
        domains_list = ", ".join(TEACHER_ALLOWED_DOMAINS)
        raise ValidationError(
            f"Los docentes deben usar un email institucional. "
            f"Dominios permitidos: {domains_list}"
        )
    
    return email

def get_allowed_teacher_domains():
    """
    Retorna la lista de dominios permitidos para docentes
    """
    return TEACHER_ALLOWED_DOMAINS.copy()
