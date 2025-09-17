import requests
from datetime import datetime
from django.core.management.base import BaseCommand
from core.models import SafraAnual, EstacaoMeteorologica, DadoMeteorologicoDiario

class Command(BaseCommand):
    help = 'Busca e importa dados das estações meteorológicas e seus registros diários do INMET.'

    BASE_URL = "https://apitempo.inmet.gov.br"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Iniciando importação de dados do INMET...'))

        # FASE 1: Cadastrar as estações de Mato Grosso
        self.cadastrar_estacoes()

        # FASE 2: Buscar dados diários para as estações e anos relevantes
        self.importar_dados_diarios()

        self.stdout.write(self.style.SUCCESS('Importação de dados do INMET concluída com sucesso!'))

    def cadastrar_estacoes(self):
        """Busca todas as estações de MT na API do INMET e salva no banco de dados."""
        self.stdout.write(self.style.HTTP_INFO('Buscando e cadastrando estações de MT...'))
        try:
            response = requests.get(f"{self.BASE_URL}/estacoes/T")
            response.raise_for_status()
            todas_estacoes = response.json()
            estacoes_mt = [est for est in todas_estacoes if est.get("SG_ESTADO") == "MT"]

            for estacao_data in estacoes_mt:
                EstacaoMeteorologica.objects.update_or_create(
                    codigo=estacao_data['CD_ESTACAO'],
                    defaults={
                        'nome': estacao_data['DC_NOME'],
                        'latitude': float(estacao_data['VL_LATITUDE']),
                        'longitude': float(estacao_data['VL_LONGITUDE']),
                        'altitude': float(estacao_data['VL_ALTITUDE']),
                        'data_inicio_operacao': datetime.strptime(estacao_data['DT_INICIO_OPERACAO'].split('T')[0], '%Y-%m-%d').date(),
                        'uf': estacao_data['SG_ESTADO']
                    }
                )
            self.stdout.write(self.style.SUCCESS(f'{len(estacoes_mt)} estações de MT foram salvas ou atualizadas.'))
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f'Erro ao buscar estações: {e}'))

    def importar_dados_diarios(self):
        """Busca os dados diários para cada estação e ano existentes na base de safras."""
        anos = SafraAnual.objects.values_list('ano', flat=True).distinct().order_by('ano')
        estacoes = EstacaoMeteorologica.objects.filter(uf='MT')

        if not anos:
            self.stdout.write(self.style.WARNING('Nenhum ano de safra encontrado. Pule a importação de dados diários.'))
            return

        self.stdout.write(self.style.HTTP_INFO(f'Anos de safra encontrados: {list(anos)}'))
        self.stdout.write(self.style.HTTP_INFO(f'Iniciando busca de dados diários para {estacoes.count()} estações...'))

        # ...
        # ...
        for estacao in estacoes:
            for ano in anos:
                if ano >= estacao.data_inicio_operacao.year:
                    # ===== NOVA LÓGICA: DIVIDIR O ANO EM DOIS SEMESTRES =====
                    periodos = [
                        (f"{ano}-01-01", f"{ano}-06-30"), # Primeiro semestre
                        (f"{ano}-07-01", f"{ano}-12-31")  # Segundo semestre
                    ]

                    self.stdout.write(f'  - Buscando dados para estação {estacao.codigo} no ano {ano}...')

                    for data_inicio, data_fim in periodos:
                        dados_diarios = None
                        try:
                            endpoint = f"/estacao/{data_inicio}/{data_fim}/{estacao.codigo}"
                            response = requests.get(f"{self.BASE_URL}{endpoint}", timeout=30.0) # Adiciona um timeout
                            response.raise_for_status()
                            dados_diarios = response.json()

                            if not dados_diarios:
                                self.stdout.write(self.style.WARNING(f'    Aviso: Período {data_inicio} a {data_fim} retornou vazio (sem erro).'))
                                continue

                        except requests.exceptions.RequestException as e:
                            self.stdout.write(self.style.WARNING(f'    Aviso: Sem dados para {estacao.codigo} no período {data_inicio}-{data_fim}. (API retornou: {e})'))
                            continue 

                        # ... o resto do código para salvar os dados continua o mesmo ...
                        try:
                            for dado in dados_diarios:
                                DadoMeteorologicoDiario.objects.update_or_create(
                                    estacao=estacao,
                                    data=datetime.strptime(dado['DT_MEDICAO'], '%Y-%m-%d').date(),
                                    defaults={
                                        'precipitacao_mm': float(dado['PRE_MAX']) if dado.get('PRE_MAX') else None,
                                        'temp_maxima_c': float(dado['TEM_MAX']) if dado.get('TEM_MAX') else None,
                                        'temp_minima_c': float(dado['TEM_MIN']) if dado.get('TEM_MIN') else None,
                                        'umidade_media_porc': float(dado['UMD_MED']) if dado.get('UMD_MED') else None,
                                    }
                                )
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'    ERRO ao SALVAR dados para {estacao.codigo} em {ano}: {e}'))