import requests
from datetime import datetime
from django.core.management.base import BaseCommand
from core.models import SafraAnual, Localidade, DadoMeteorologicoDiario
from django.db import transaction

class Command(BaseCommand):
    help = 'Busca e importa dados da API NASA POWER para localidades pré-definidas.'

    LOCALIDADES_MT = {
        "Cuiabá": {"lat": -15.59, "lon": -56.09}, "Rondonópolis": {"lat": -16.47, "lon": -54.63},
        "Sinop": {"lat": -11.86, "lon": -55.50}, "Sorriso": {"lat": -12.54, "lon": -55.71},
        "Primavera do Leste": {"lat": -15.56, "lon": -54.29},
    }
    API_BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
    PARAMS = "parameters=T2M_MAX,T2M_MIN,PRECTOTCORR&community=AG&format=JSON"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Iniciando importação de dados da NASA POWER...'))
        self.cadastrar_localidades()
        self.importar_dados_diarios()
        self.stdout.write(self.style.SUCCESS('Importação de dados da NASA POWER concluída com sucesso!'))

    def cadastrar_localidades(self):
        self.stdout.write('Cadastrando ou atualizando localidades...')
        with transaction.atomic():
            for nome, coords in self.LOCALIDADES_MT.items():
                Localidade.objects.update_or_create(
                    nome=nome,
                    defaults={'latitude': coords['lat'], 'longitude': coords['lon']}
                )
        self.stdout.write(self.style.SUCCESS(f'{len(self.LOCALIDADES_MT)} localidades salvas.'))

    def importar_dados_diarios(self):
        anos = SafraAnual.objects.values_list('ano', flat=True).distinct().order_by('ano')
        localidades = Localidade.objects.all() # <-- AQUI ESTÁ A CORREÇÃO PRINCIPAL

        if not list(anos):
            self.stdout.write(self.style.WARNING('Nenhum ano de safra encontrado. Rode a importação da Conab primeiro.'))
            return

        self.stdout.write(f'Iniciando busca de dados diários para {localidades.count()} localidades...')
        for local in localidades:
            for ano in anos:
                # ... (resto da função, que já estava correta)
                self.stdout.write(f'  - Buscando dados para {local.nome} no ano {ano}...')
                start_date = f"{ano}0101"; end_date = f"{ano}1231"
                url = f"{self.API_BASE_URL}?{self.PARAMS}&latitude={local.latitude}&longitude={local.longitude}&start={start_date}&end={end_date}"
                try:
                    response = requests.get(url, timeout=60.0)
                    response.raise_for_status()
                    api_data = response.json()
                    params = api_data['properties']['parameter']
                    t2m_max_data = params['T2M_MAX']
                    t2m_min_data = params['T2M_MIN']
                    prec_data = params['PRECTOTCORR']
                    with transaction.atomic():
                        for date_str, temp_max in t2m_max_data.items():
                            data_obj = datetime.strptime(date_str, '%Y%m%d').date()
                            temp_min = t2m_min_data.get(date_str, -999)
                            prec = prec_data.get(date_str, -999)
                            if temp_max == -999 or temp_min == -999 or prec == -999:
                                continue
                            DadoMeteorologicoDiario.objects.update_or_create(
                                localidade=local, data=data_obj,
                                defaults={
                                    'temp_maxima_c': temp_max, 'temp_minima_c': temp_min,
                                    'precipitacao_mm': prec,
                                }
                            )
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'    Erro ao processar dados para {local.nome} em {ano}: {e}'))