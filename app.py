import pandas as pd
import multiprocessing
import threading
import time

arquivo = "votacao_candidato_munzona_2026_SP.csv"

def calcular(dados):
  
    dados["QT_VOTOS_NOMINAIS_VALIDOS"] = pd.to_numeric(
        dados["QT_VOTOS_NOMINAIS_VALIDOS"], errors="coerce"
    ).fillna(0)
    dados["QT_VOTOS_NOMINAIS_VALIDOS"] = dados["QT_VOTOS_NOMINAIS_VALIDOS"].apply(
        lambda x: 0 if x < 0 else x
    )

    media = dados["QT_VOTOS_NOMINAIS_VALIDOS"].mean()
    partidos = dados.groupby("SG_PARTIDO")["QT_VOTOS_NOMINAIS_VALIDOS"].mean()
    cargo = dados.groupby("DS_CARGO")["QT_VOTOS_NOMINAIS_VALIDOS"].mean()

    return media, partidos, cargo

if __name__ == "__main__":
    print("Lendo o arquivo...")

    df = pd.read_csv(arquivo, sep=";", encoding="latin1", low_memory=False)

    inicio_processos = time.perf_counter()
    with multiprocessing.Pool() as pool:
        resultado_do_processo = pool.apply(calcular, args=(df,))
    tempo_do_processo = time.perf_counter() - inicio_processos

    inicio_thread = time.perf_counter()
    resultado_da_threads = None 
    
    def executar_na_thread():
        resultado_da_threads.append(calcular(df))
        
    t = threading.Thread(target=executar_na_thread)
    t.start()
    t.join()

    tempo_da_threads = time.perf_counter() - inicio_thread

    media_global, media_partidos, media_cargos = resultado_do_processo

