import pandas as pd
import requests # Biblioteca para fazer requisições HTTP
import os
from django.core.management.base import BaseCommand
from core.models import SafraAnual

class Command(BaseCommand):
    help = 'Baixa e importa dados de safras anuais a partir do site da Conab.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Iniciando pipeline de dados da Conab...'))

        # --- NOVA ETAPA: EXTRAÇÃO (DOWNLOAD) ---
        url = 'https://portaldeinformacoes.conab.gov.br/downloads/arquivos/SerieHistoricaGraos.txt'
        local_filename = 'data/SerieHistoricaGraos.csv' # Salvaremos em uma pasta 'data'

        # Garante que o diretório 'data' exista
        os.makedirs(os.path.dirname(local_filename), exist_ok=True)

        self.stdout.write(f'Baixando dados de: {url}')
        try:
            response = requests.get(url)
            response.raise_for_status() # Lança um erro para respostas ruins (4xx ou 5xx)

            # O arquivo .txt usa encoding 'latin-1' e podemos salvá-lo como .csv
            with open(local_filename, 'w', encoding='latin-1') as f:
                f.write(response.text)

            self.stdout.write(self.style.SUCCESS(f'Arquivo salvo com sucesso em: {local_filename}'))
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f'Erro ao baixar o arquivo: {e}'))
            return

        # --- PASSO 2: TRANSFORMAÇÃO E CARGA (Lógica que já tínhamos) ---
        try:
            df = pd.read_csv(local_filename, sep=';', encoding='latin-1')
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Arquivo "{local_filename}" não encontrado.'))
            return

        # ... (o resto do código de transformação e carga permanece exatamente o mesmo) ...
        self.stdout.write('Iniciando processamento e importação para o banco de dados...')
        colunas_renomeadas = {
            'ano_agricola': 'ano_safra', 'dsc_safra_previsao': 'tipo_safra', 'uf': 'uf',
            'produto': 'produto', 'area_plantada_mil_ha': 'area_plantada_ha',
            'producao_mil_t': 'producao_toneladas', 'produtividade_mil_ha_mil_t': 'produtividade_kg_ha'
        }
        df_transformado = df.rename(columns=colunas_renomeadas)
        df_transformado['area_plantada_ha'] = df_transformado['area_plantada_ha'] * 1000
        df_transformado['producao_toneladas'] = df_transformado['producao_toneladas'] * 1000
        df_transformado['ano'] = df_transformado['ano_safra'].str.split('/').str[0].astype(int)
        df_mt = df_transformado[df_transformado['uf'] == 'MT'].copy()
        colunas_finais = ['ano', 'uf', 'produto', 'area_plantada_ha', 'producao_toneladas', 'produtividade_kg_ha']
        df_final = df_mt[colunas_finais]

        self.stdout.write(f'{len(df_final)} registros para o Mato Grosso foram processados.')

        SafraAnual.objects.all().delete()

        registros_criados = 0
        for index, row in df_final.iterrows():
            obj, created = SafraAnual.objects.update_or_create(
                ano=row['ano'], uf=row['uf'], produto=row['produto'],
                defaults={
                    'area_plantada_ha': row['area_plantada_ha'],
                    'producao_toneladas': row['producao_toneladas'],
                    'produtividade_kg_ha': row['produtividade_kg_ha']
                }
            )
            if created:
                registros_criados += 1

        self.stdout.write(self.style.SUCCESS(f'Pipeline concluída! {registros_criados} registros importados para o MT.'))