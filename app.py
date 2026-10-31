import pandas as pd
import multiprocessing
import threading
import time

arquivo = "votacao_candidato_munzona_2026_SP.csv"
municipi = "GUARULHOS"

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
    print("\nLendo o arquivo...")

    df = pd.read_csv(arquivo, sep=";", encoding="latin1", low_memory=False)

    inicio_processos = time.perf_counter()
    with multiprocessing.Pool() as pool:
        resultado_do_processo = pool.apply(calcular, args=(df,))
    tempo_do_processo = time.perf_counter() - inicio_processos

    inicio_thread = time.perf_counter()
    resultado_da_threads = []
    
    def executar_na_thread():
        resultado_da_threads.append(calcular(df))
        
    t = threading.Thread(target=executar_na_thread)
    t.start()
    t.join()

    tempo_da_threads = time.perf_counter() - inicio_thread

    media_global, media_partidos, media_cargos = resultado_do_processo

    partido_vencedor = media_partidos.idxmax()
    cargo_vencedor = media_cargos.idxmax()

    print("\nResultado Multiprocesso")
    print(f"Média geral:{media_global}")

    print("Partido com maior média",partido_vencedor)
    print(f"Média : {media_partidos[partido_vencedor]:.2f}")

    print("Cargo com maior média :", cargo_vencedor)
    print(f"Média: {media_cargos[cargo_vencedor]:.2f}")

    print(f"Tempo dos processos: {tempo_do_processo:.2f} Segunods")

    time.sleep(5)

    if resultado_da_threads:
        media_global, media_partidos,media_cargos = resultado_da_threads[0]

        print("\nResultado multithreading")
        print(f"Média geral: {media_global:.2f}")

        partido_vencedor = media_partidos.idxmax()
        cargo_vencedor = media_cargos.idxmax()

        print("Partido com maior média",partido_vencedor)
        print(f"Média: {media_cargos[cargo_vencedor]:.2f}")
    
    print(f"Tempo das thereds:{tempo_da_threads:.2f} Segundos")

    print("Comparar desenpenho")


    if tempo_do_processo < tempo_da_threads:
        print("Multiprocesso foi mais rápido")
    elif tempo_da_threads < tempo_do_processo:
        print("MultiThreads foi mais rápido")

    else:
        print("As duas tiveram o mesmo tempo")

    time.sleep(5)

    print("\n Programa finaizado")











