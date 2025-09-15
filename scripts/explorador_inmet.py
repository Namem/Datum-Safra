import requests
import json

# URL base da API (verificar na documentação se ainda é esta)
BASE_URL = "https://apitempo.inmet.gov.br"

def listar_estacoes_mt():
    """Busca todas as estações e filtra as do Mato Grosso (MT)."""
    print("Buscando estações meteorológicas...")
    try:
        # O endpoint '/estacoes/T' geralmente retorna todas as estações automáticas
        response = requests.get(f"{BASE_URL}/estacoes/T")
        response.raise_for_status()

        todas_estacoes = response.json()
        estacoes_mt = [est for est in todas_estacoes if est.get("SG_ESTADO") == "MT"]

        print(f"Encontradas {len(estacoes_mt)} estações em Mato Grosso.")

        # Imprime as 5 primeiras para vermos a estrutura
        for estacao in estacoes_mt[:5]:
            print(f"  - ID: {estacao['CD_ESTACAO']}, Nome: {estacao['DC_NOME']}, Latitude: {estacao['VL_LATITUDE']}")

        return estacoes_mt
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar estações: {e}")
        return []

def buscar_dados_estacao(codigo_estacao, data_inicio, data_fim):
    """Busca dados diários para uma estação específica em um intervalo de datas."""
    print(f"\nBuscando dados para a estação {codigo_estacao} de {data_inicio} a {data_fim}...")
    try:
        # Exemplo de endpoint para dados diários (verificar na documentação)
        endpoint = f"/estacao/diario/{data_inicio}/{data_fim}/{codigo_estacao}"
        response = requests.get(f"{BASE_URL}{endpoint}")
        response.raise_for_status()

        dados = response.json()
        print(f"Encontrados {len(dados)} registros para o período.")

        # Imprime os 2 primeiros registros para análise
        if dados:
            print("Amostra dos dados recebidos:")
            print(json.dumps(dados[:2], indent=2, ensure_ascii=False))

    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar dados da estação: {e}")

# --- Execução do Script ---
if __name__ == "__main__":
    estacoes_mt = listar_estacoes_mt()

    # Se encontrou estações, pega o código da primeira e busca dados para um período curto
    if estacoes_mt:
        primeira_estacao_codigo = estacoes_mt[0]['CD_ESTACAO']
        # Vamos buscar dados para a primeira semana de Janeiro de 2024 como teste
        buscar_dados_estacao(primeira_estacao_codigo, "2024-01-01", "2024-01-07")