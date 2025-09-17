# Importa nossa app Celery para que ela seja carregada com o Django
from .celery import app as celery_app

__all__ = ('celery_app',)