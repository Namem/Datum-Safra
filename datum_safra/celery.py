import os
from celery import Celery

# Define o módulo de configurações do Django para o Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datum_safra.settings')

# Cria a instância da aplicação Celery
app = Celery('datum_safra')

# Carrega as configurações do Celery a partir do settings.py do Django
# O namespace='CELERY' significa que todas as configurações devem começar com CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Descobre e carrega automaticamente as tarefas dos apps instalados no Django
app.autodiscover_tasks()