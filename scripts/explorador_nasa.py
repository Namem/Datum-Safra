import requests
import json

# URL gerada pela ferramenta da NASA para Cuiabá, Janeiro de 2024
# Parâmetros: Temp. Max/Min e Precipitação
API_URL = "https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M_MAX,T2M_MIN,PRECTOTCORR&community=AG&longitude=-56.09&latitude=-15.59&start=20240101&end=20240131&format=JSON"

print(f"Tentando acessar a API da NASA em: {API_URL}")

try:
    response = requests.get(API_URL)
    response.raise_for_status()

    data = response.json()

    print("\nSUCESSO! A API da NASA respondeu.")

    # A estrutura do JSON da NASA é um pouco diferente, vamos explorá-la
    print("\nCabeçalhos recebidos:")
    print(data.get('header'))

    print("\nParâmetros disponíveis:")
    print(data.get('parameters'))

    print("\nPrimeiro registro de dados (exemplo):")
    # Os dados ficam dentro de 'properties' -> 'parameter'
    temp_max_data = data['properties']['parameter']['T2M_MAX']
    primeira_data = list(temp_max_data.keys())[0]
    primeiro_valor = temp_max_data[primeira_data]

    print(f"Data: {primeira_data}, Temperatura Máxima: {primeiro_valor}")

except requests.exceptions.RequestException as e:
    print(f"\nERRO ao acessar a API: {e}")
except Exception as e:
    print(f"Ocorreu um erro ao processar a resposta: {e}")