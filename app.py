import os
import time
from multiprocessing import Pool
from multiprocessing.pool import ThreadPool
import pandas as pd

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

ARQUIVO = "votacao_candidato_munzona_2026_SP.csv"
MUNICIPIO = "GUARULHOS"

TOTAL_DE_DIVISOES = 4


def processar_chunk(df_chunk):
    df_chunk = df_chunk.copy()
    
    df_chunk["QT_VOTOS_NOMINAIS_VALIDOS"] = pd.to_numeric(
        df_chunk["QT_VOTOS_NOMINAIS_VALIDOS"], errors="coerce"
    ).fillna(0)

    soma_votos = df_chunk["QT_VOTOS_NOMINAIS_VALIDOS"].sum()
    qtd_votos = df_chunk["QT_VOTOS_NOMINAIS_VALIDOS"].count()

    partidos = df_chunk.groupby("SG_PARTIDO", dropna=False)["QT_VOTOS_NOMINAIS_VALIDOS"].agg(["sum", "count"])
    cargos = df_chunk.groupby("DS_CARGO", dropna=False)["QT_VOTOS_NOMINAIS_VALIDOS"].agg(["sum", "count"])

    return {
        "soma_votos": soma_votos,
        "qtd_votos": qtd_votos,
        "partidos": partidos,
        "cargos": cargos
    }


def consolidar_resultados(resultados_parciais):
    
    soma_total = sum(r["soma_votos"] for r in resultados_parciais)
    qtd_total = sum(r["qtd_votos"] for r in resultados_parciais)
    media_geral = soma_total / qtd_total if qtd_total > 0 else 0.0

    df_partidos = pd.concat([r["partidos"] for r in resultados_parciais])
    df_partidos = df_partidos.groupby(level=0).sum()
    media_partidos = df_partidos["sum"] / df_partidos["count"]

    df_cargos = pd.concat([r["cargos"] for r in resultados_parciais])
    df_cargos = df_cargos.groupby(level=0).sum()
    media_cargos = df_cargos["sum"] / df_cargos["count"]

    return {
        "media_geral": media_geral,
        "partido_vencedor": media_partidos.idxmax(),
        "media_partido_vencedor": media_partidos.max(),
        "cargo_vencedor": media_cargos.idxmax(),
        "media_cargo_vencedor": media_cargos.max()
    }


def rodar_com_threads(chunks):
    
    inicio = time.perf_counter()
    with ThreadPool(processes=TOTAL_DE_DIVISOES) as pool:
        resultados = pool.map(processar_chunk, chunks)
    res_final = consolidar_resultados(resultados)
    tempo = time.perf_counter() - inicio
    return res_final, tempo


def rodar_com_processos(chunks):
    
    inicio = time.perf_counter()
    with Pool(processes=TOTAL_DE_DIVISOES) as pool:
        resultados = pool.map(processar_chunk, chunks)
    res_final = consolidar_resultados(resultados)
    tempo = time.perf_counter() - inicio
    return res_final, tempo


if __name__ == "__main__":
    print("Lendo o arquivo...")

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

    print("Resultado Multiprocesso")
    print(f"Média geral:{media_global}")

    print("Partido com maior média",partido_vencedor)
    print(f"Média : {media_partidos[partido_vencedor]:.2f}")

    print("Cargo com maior média :", cargo_vencedor)
    print(f"Média: {media_cargos[cargo_vencedor]:.2f}")

    print(f"Tempo dos processos: {tempo_do_processo:.2f} Segunods")

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

    print("\n Programa finaizado")











