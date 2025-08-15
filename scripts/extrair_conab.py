import pandas as pd
import os

file_name = '/home/namem/Área de Trabalho/Datum Safra/Datum-Safra/Data/SerieHistoricaGraos.csv'

if not os.path.exists(file_name):
    print(f"O arquivo {file_name} não existe.")
else:
    try:
        df = pd.read_csv(file_name, sep=';', encoding='latin-1')
        print("\n--- DADOS CARREGADOS COM SUCESSO! ---")
        print("\n--- 1. Amostra dos Dados (10 primeiras linhas): ---")
        print(df.head(10))
        print("\n--- 2. Informações Gerais sobre as Colunas e Tipos de Dados: ---")
        df.info()
        print("\n--- 3. Estatísticas Descritivas: ---")
        print(df.describe())

        if 'Produto' in df.columns:
            print("\n--- 4. Culturas encontradas no arquivo: ---")
            print(df['Produto'].unique())
    
    except Exception as e:
        print(f"Ocorreu um erro ao carregar o arquivo CSV: {e}")

