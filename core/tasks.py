import requests
import os
import pandas as pd
from datetime import datetime
from celery import shared_task
from .models import SafraAnual, EstacaoMeteorologica, DadoMeteorologicoDiario

@shared_task
def importar_dados_conab_task():
    """
    Tarefa Celery para baixar, processar e importar dados da Conab.
    """
    print("INICIANDO TAREFA: Importação de dados da Conab.")
    
    # --- ETAPA DE EXTRAÇÃO (DOWNLOAD) ---
    url = 'https://portaldeinformacoes.conab.gov.br/downloads/arquivos/SerieHistoricaGraos.txt'
    local_filename = 'data/SerieHistoricaGraos.csv'
    os.makedirs(os.path.dirname(local_filename), exist_ok=True)
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(local_filename, 'w', encoding='latin-1') as f:
            f.write(response.text)
        print("Download dos dados da Conab concluído.")
    except requests.exceptions.RequestException as e:
        print(f"ERRO no download da Conab: {e}")
        return f"ERRO no download da Conab: {e}"

    # --- ETAPA DE TRANSFORMAÇÃO E CARGA (TRANSFORM & LOAD) ---
    try:
        df = pd.read_csv(local_filename, sep=';', encoding='latin-1')
        
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

        print(f'{len(df_final)} registros da Conab para o Mato Grosso foram processados.')

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
        
        print(f"Dados da Conab salvos no banco. {registros_criados} registros criados.")
        print("TAREFA CONCLUÍDA: Importação de dados da Conab.")
        return f"Importação da Conab finalizada com sucesso. {registros_criados} registros criados."

    except Exception as e:
        print(f"ERRO no processamento dos dados da Conab: {e}")
        return f"ERRO no processamento dos dados da Conab: {e}"


@shared_task
def importar_dados_inmet_task():
    """
    Tarefa Celery para buscar e importar dados das estações e medições do INMET.
    """
    print("INICIANDO TAREFA: Importação de dados do INMET.")
    BASE_URL = "https://apitempo.inmet.gov.br"
    
    # FASE 1: Cadastrar estações de MT
    try:
        response = requests.get(f"{BASE_URL}/estacoes/T")
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
        print(f"{len(estacoes_mt)} estações de MT foram salvas/atualizadas.")
    except requests.exceptions.RequestException as e:
        print(f"ERRO ao buscar estações do INMET: {e}")
        return f"ERRO ao buscar estações do INMET: {e}"
        
    # FASE 2: Buscar dados diários para as estações e anos relevantes
    anos = SafraAnual.objects.values_list('ano', flat=True).distinct().order_by('ano')
    estacoes = EstacaoMeteorologica.objects.filter(uf='MT')

    if not anos:
        print('Aviso: Nenhum ano de safra encontrado. Pule a importação de dados diários.')
        return "Nenhum ano de safra encontrado."

    print(f'Anos de safra encontrados: {list(anos)}')
    print(f'Iniciando busca de dados diários para {estacoes.count()} estações...')

    for estacao in estacoes:
        for ano in anos:
            if ano >= estacao.data_inicio_operacao.year:
                print(f'  - Buscando dados para estação {estacao.codigo} no ano {ano}...')
                data_inicio = f"{ano}-01-01"
                data_fim = f"{ano}-12-31"
                
                dados_diarios = None
                try:
                    endpoint = f"/estacao/{data_inicio}/{data_fim}/{estacao.codigo}"
                    response = requests.get(f"{BASE_URL}{endpoint}")
                    response.raise_for_status()
                    dados_diarios = response.json()
                except requests.exceptions.RequestException as e:
                    print(f'    Aviso: Sem dados para {estacao.codigo} em {ano}. (API retornou: {e})')
                    continue 

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
                    print(f'    ERRO ao SALVAR dados para {estacao.codigo} em {ano}: {e}')

    print("TAREFA CONCLUÍDA: Importação de dados do INMET.")
    return "Importação do INMET finalizada com sucesso."