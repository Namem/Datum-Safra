import pandas as pd
import os

# --- PASSO 1: CARREGAR OS DADOS ---
file_name = '/home/namem/Área de Trabalho/Datum Safra/Datum-Safra/Data/SerieHistoricaGraos.csv'
print(f"Carregando dados de '{file_name}'...")
df = pd.read_csv(file_name, sep=';', encoding='latin-1')
print("Dados brutos carregados.")

# --- PASSO 2: TRANSFORMAÇÃO ---
print("\nIniciando processo de transformação dos dados...")

# 2.1: Renomear colunas para nomes mais limpos e padronizados
print("  - Renomeando colunas...")
colunas_renomeadas = {
    'ano_agricola': 'ano_safra',
    'dsc_safra_previsao': 'tipo_safra',
    'uf': 'uf',
    'produto': 'produto',
    'area_plantada_mil_ha': 'area_plantada_ha',
    'producao_mil_t': 'producao_toneladas',
    'produtividade_mil_ha_mil_t': 'produtividade_kg_ha' # A produtividade já está em kg/ha, vamos apenas renomear
}
df_transformado = df.rename(columns=colunas_renomeadas)

# 2.2: Ajustar unidades (multiplicar por 1000)
print("  - Ajustando unidades (de 'mil' para valor real)...")
df_transformado['area_plantada_ha'] = df_transformado['area_plantada_ha'] * 1000
df_transformado['producao_toneladas'] = df_transformado['producao_toneladas'] * 1000

# 2.3: Simplificar o ano da safra
print("  - Extraindo ano de início da safra...")
df_transformado['ano'] = df_transformado['ano_safra'].str.split('/').str[0].astype(int)

# 2.4: Filtrar dados para o escopo do MVP (Mato Grosso)
print("  - Filtrando dados para o estado de Mato Grosso (MT)...")
df_mt = df_transformado[df_transformado['uf'] == 'MT'].copy()

# 2.5: Selecionar e reordenar as colunas finais
print("  - Selecionando e reorganizando colunas finais...")
colunas_finais = [
    'ano',
    'uf',
    'produto',
    'area_plantada_ha',
    'producao_toneladas',
    'produtividade_kg_ha'
]
df_final = df_mt[colunas_finais]

print("\n--- PROCESSO DE TRANSFORMAÇÃO CONCLUÍDO! ---")


# --- PASSO 3: EXIBIR O RESULTADO FINAL ---
print("\n--- Amostra do DataFrame Final (Mato Grosso): ---")
print(df_final.head())

print("\n--- Informações do DataFrame Final: ---")
df_final.info()

print("\n--- Estatísticas do DataFrame Final: ---")
print(df_final.describe())