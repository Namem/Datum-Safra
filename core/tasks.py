import requests
import os
import pandas as pd
from datetime import datetime
from celery import shared_task
from django.db import transaction
from .models import SafraAnual, Localidade, DadoMeteorologicoDiario

@shared_task
def importar_dados_conab_task():
    """
    Tarefa Celery para baixar, processar e importar dados da Conab.
    """
    print("INICIANDO TAREFA CELERY: Importação de dados da Conab.")
    
    # Etapa de Extração (Download)
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

    # Etapa de Transformação e Carga (Transform & Load)
    try:
        df = pd.read_csv(local_filename, sep=';', encoding='latin-1')
        
        colunas_renomeadas = {'ano_agricola': 'ano_safra', 'dsc_safra_previsao': 'tipo_safra', 'uf': 'uf', 'produto': 'produto', 'area_plantada_mil_ha': 'area_plantada_ha', 'producao_mil_t': 'producao_toneladas', 'produtividade_mil_ha_mil_t': 'produtividade_kg_ha'}
        df_transformado = df.rename(columns=colunas_renomeadas)
        df_transformado['area_plantada_ha'] = df_transformado['area_plantada_ha'] * 1000
        df_transformado['producao_toneladas'] = df_transformado['producao_toneladas'] * 1000
        df_transformado['ano'] = df_transformado['ano_safra'].str.split('/').str[0].astype(int)
        df_mt = df_transformado[df_transformado['uf'] == 'MT'].copy()
        colunas_finais = ['ano', 'uf', 'produto', 'area_plantada_ha', 'producao_toneladas', 'produtividade_kg_ha']
        df_final = df_mt[colunas_finais]

        SafraAnual.objects.all().delete()
        
        with transaction.atomic(): # <-- Bloco de transação adicionado
            for index, row in df_final.iterrows():
                SafraAnual.objects.create(
                    ano=row['ano'], uf=row['uf'], produto=row['produto'],
                    area_plantada_ha=row['area_plantada_ha'],
                    producao_toneladas=row['producao_toneladas'],
                    produtividade_kg_ha=row['produtividade_kg_ha']
                )
        
        print(f"TAREFA CONCLUÍDA: {len(df_final)} registros da Conab importados.")
        return f"Importação da Conab finalizada. {len(df_final)} registros criados."

    except Exception as e:
        print(f"ERRO no processamento dos dados da Conab: {e}")
        return f"ERRO no processamento dos dados da Conab: {e}"


@shared_task
def importar_dados_nasa_task():
    """
    Tarefa Celery para buscar e importar dados da API NASA POWER.
    """
    print("INICIANDO TAREFA CELERY: Importação de dados da NASA.")
    
    LOCALIDADES_MT = {
        "Cuiabá": {"lat": -15.59, "lon": -56.09}, "Rondonópolis": {"lat": -16.47, "lon": -54.63},
        "Sinop": {"lat": -11.86, "lon": -55.50}, "Sorriso": {"lat": -12.54, "lon": -55.71},
        "Primavera do Leste": {"lat": -15.56, "lon": -54.29},
    }
    API_BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
    PARAMS = "parameters=T2M_MAX,T2M_MIN,PRECTOTCORR&community=AG&format=JSON"

    # Fase 1: Cadastrar Localidades
    with transaction.atomic(): # <-- Bloco de transação adicionado
        for nome, coords in LOCALIDADES_MT.items():
            Localidade.objects.update_or_create(
                nome=nome,
                defaults={'latitude': coords['lat'], 'longitude': coords['lon']}
            )
    print(f"{len(LOCALIDADES_MT)} localidades salvas/atualizadas.")

    # Fase 2: Buscar dados diários
    anos = SafraAnual.objects.values_list('ano', flat=True).distinct().order_by('ano')
    localidades = Localidade.objects.all()

    if not anos:
        print('Aviso: Nenhum ano de safra encontrado.')
        return "Nenhum ano de safra encontrado."

    for local in localidades:
        for ano in anos:
            # ... (Lógica de busca da API, exatamente como no management command)
            start_date = f"{ano}0101"; end_date = f"{ano}1231"
            url = f"{API_BASE_URL}?{PARAMS}&latitude={local.latitude}&longitude={local.longitude}&start={start_date}&end={end_date}"
            
            try:
                response = requests.get(url, timeout=60.0)
                response.raise_for_status()
                api_data = response.json()
                
                params = api_data['properties']['parameter']
                t2m_max_data = params['T2M_MAX']
                t2m_min_data = params['T2M_MIN']
                prec_data = params['PRECTOTCORR']

                with transaction.atomic(): # <-- Bloco de transação adicionado
                    for date_str, temp_max in t2m_max_data.items():
                        # ... (lógica de parse de cada dia)
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
                print(f'Erro ao processar dados para {local.nome} em {ano}: {e}')
    
    print("TAREFA CONCLUÍDA: Importação de dados da NASA.")
    return "Importação do INMET finalizada com sucesso."