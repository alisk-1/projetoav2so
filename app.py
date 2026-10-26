import pandas as pd
import multiprocessing
import threading
import time

arquivo = "votacao_candidato_munzona_2026_SP.csv"

def calcular (dados):
    media = dados["QT_]VOTOS_NOMINAIS_VALIDOS"].mean()
    partidos = dados.groupby("SG_PARTIDOS")["QT_VOTOS_NOMINAIS_VALIDOS"].mean()
    cargo = dados.groupby("DS_CARGOS")["QT_VOTOS_NOMINAIS"].mean()
    return media , partidos, cargo