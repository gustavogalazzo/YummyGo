"""
Serviço de Geolocalização

Contém a lógica matemática para calcular distâncias geográficas e 
chamar a API de Geocoding.
"""
import math
import requests # Necessário para fazer chamadas HTTP à API
from flask import current_app # Necessário para ler a chave API da app.config

# Raio médio da Terra em quilómetros
R = 6371 

def haversine(lat1, lon1, lat2, lon2):
    """
    Calcula a distância geodésica em quilómetros entre dois 
    pontos definidos por Latitude e Longitude (Fórmula de Haversine).
    """
    # Converte graus para radianos
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Diferenças
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    # Aplicação da fórmula
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Distância final
    distance = R * c
    return distance


# --- NOVO: FUNÇÃO DE CONVERSÃO DE ENDEREÇO PARA COORDENADAS (OpenCage) ---
def get_coordinates(address):
    """
    Converte um endereço de texto em coordenadas (Latitude, Longitude) 
    usando a API OpenCage.
    
    :param address: Uma string completa do endereço (Rua, Número, Cidade, Estado).
    :return: Uma tupla (latitude, longitude) ou (None, None) em caso de falha.
    """
    # Lê a chave da API do app.config (que foi lida do .env)
    api_key = current_app.config.get('OPENCAGE_API_KEY')
    if not api_key:
        # Se esta mensagem aparecer, a chave não está no .env ou config.py
        print("ERRO: Chave OPENCAGE_API_KEY não configurada.")
        return None, None
        
    base_url = "https://api.opencagedata.com/geocode/v1/json"
    params = {
        'q': address, # O OpenCage usa 'q' para a string de busca
        'key': api_key,
        'countrycode': 'br', # Otimiza a busca para o Brasil
        'limit': 1
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status() # Lança um erro para status 4xx/5xx
        data = response.json()
        
        # Verifica se a API retornou um resultado válido
        if data['results']:
            location = data['results'][0]['geometry']
            return location['lat'], location['lng']
        
    except requests.exceptions.RequestException as e:
        print(f"Erro ao chamar API OpenCage Geocoding: {e}")
        
    return None, None