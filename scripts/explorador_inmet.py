import requests
import json

# Novo endereço base da API
BASE_URL = "https://portal.inmet.gov.br/api/historico"

# Estação de Cuiabá (A901), um período curto para teste
codigo_estacao = "A901"
data_inicio = "2024-01-01"
data_fim = "2024-01-07"

# Monta a URL final
url_final = f"{BASE_URL}/{codigo_estacao}/{data_inicio}/{data_fim}"

print(f"Tentando acessar a NOVA API em: {url_final}")

try:
    response = requests.get(url_final)
    response.raise_for_status() # Lança erro para status 4xx ou 5xx

    dados = response.json()

    print("\nSUCESSO! A API respondeu.")
    print(f"Encontrados {len(dados)} registros para o período.")

    if dados:
        print("\nAmostra do primeiro registro:")
        # Usamos json.dumps para imprimir o JSON de forma legível
        print(json.dumps(dados[0], indent=2, ensure_ascii=False))

except requests.exceptions.RequestException as e:
    print(f"\nERRO ao acessar a API: {e}")
except json.JSONDecodeError:
    print("\nERRO: A resposta não foi um JSON válido. Conteúdo da resposta:")
    print(response.text)