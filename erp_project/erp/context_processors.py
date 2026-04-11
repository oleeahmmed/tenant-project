"""
Context processors for ERP app
"""
from .models import Company


def company_info(request):
    """Add company information to all templates"""
    try:
        company = Company.objects.first()
    except:
        company = None
    
    return {
        'company': company
    }
