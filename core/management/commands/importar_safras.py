import pandas as pd
import requests
import os
from django.core.management.base import BaseCommand
from core.models import SafraAnual
from django.db import transaction

class Command(BaseCommand):
    help = 'Baixa, processa e importa os dados de safra da Conab.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Iniciando pipeline de dados da Conab...'))
        
        # Etapa de Extração
        url = 'https://portaldeinformacoes.conab.gov.br/downloads/arquivos/SerieHistoricaGraos.txt'
        local_filename = 'data/SerieHistoricaGraos.csv'
        os.makedirs(os.path.dirname(local_filename), exist_ok=True)
        try:
            response = requests.get(url)
            response.raise_for_status()
            with open(local_filename, 'w', encoding='latin-1') as f:
                f.write(response.text)
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f'Erro no download da Conab: {e}'))
            return

        # Etapa de Transformação
        df = pd.read_csv(local_filename, sep=';', encoding='latin-1')
        colunas_renomeadas = {'ano_agricola': 'ano_safra', 'dsc_safra_previsao': 'tipo_safra', 'uf': 'uf', 'produto': 'produto', 'area_plantada_mil_ha': 'area_plantada_ha', 'producao_mil_t': 'producao_toneladas', 'produtividade_mil_ha_mil_t': 'produtividade_kg_ha'}
        df_transformado = df.rename(columns=colunas_renomeadas)
        df_transformado['area_plantada_ha'] = df_transformado['area_plantada_ha'] * 1000
        df_transformado['producao_toneladas'] = df_transformado['producao_toneladas'] * 1000
        df_transformado['ano'] = df_transformado['ano_safra'].str.split('/').str[0].astype(int)
        df_mt = df_transformado[df_transformado['uf'] == 'MT'].copy()
        colunas_finais = ['ano', 'uf', 'produto', 'area_plantada_ha', 'producao_toneladas', 'produtividade_kg_ha']
        df_final = df_mt[colunas_finais]
        self.stdout.write(f'{len(df_final)} registros para o Mato Grosso foram processados.')

        # Etapa de Carga
        try:
            with transaction.atomic():
                SafraAnual.objects.all().delete()
                registros_criados = 0
                for index, row in df_final.iterrows():
                    # AQUI ESTÁ A CORREÇÃO PRINCIPAL: USANDO update_or_create
                    obj, created = SafraAnual.objects.update_or_create(
                        ano=row['ano'],
                        uf=row['uf'],
                        produto=row['produto'].strip(), # Adicionado .strip() para remover espaços extras
                        defaults={
                            'area_plantada_ha': row['area_plantada_ha'],
                            'producao_toneladas': row['producao_toneladas'],
                            'produtividade_kg_ha': row['produtividade_kg_ha']
                        }
                    )
                    if created:
                        registros_criados += 1
            self.stdout.write(self.style.SUCCESS(f'Pipeline da Conab concluída! {registros_criados} novos registros criados.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro durante a transação da Conab: {e}'))