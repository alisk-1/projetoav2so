import pandas as pd
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import time
import os

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

arquivo = "votacao_candidato_munzona_2026_SP.csv"
municipio = "GUARULHOS"

num_threads_or_process = min(4, os.cpu_count() or 1)

def calcular(dados):

    dados = dados.copy()

    dados["QT_VOTOS_NOMINAIS_VALIDOS"] = pd.to_numeric(
        dados["QT_VOTOS_NOMINAIS_VALIDOS"],errors="coerce").fillna(0)

    dados["QT_VOTOS_NOMINAIS_VALIDOS"] = (
        dados["QT_VOTOS_NOMINAIS_VALIDOS"].clip(lower=0)
    )

    votos = dados["QT_VOTOS_NOMINAIS_VALIDOS"]

    soma = votos.sum()
    quantidade = votos.count()

    partidos = dados.groupby(
        "SG_PARTIDO", dropna=False)["QT_VOTOS_NOMINAIS_VALIDOS"].agg(["sum", "count"])

    cargo = dados.groupby(
        "DS_CARGO", dropna=False)["QT_VOTOS_NOMINAIS_VALIDOS"].agg(["sum", "count"])

    return soma, quantidade, partidos, cargo


def carregar_dados():

    print("Lendo o arquivo...")

    df = pd.read_csv(arquivo,sep=";",encoding="latin1",low_memory=False)

    df = df[
        df["NM_MUNICIPIO"].astype("string").str.strip().str.upper() == municipio].copy()

    if df.empty:
        raise ValueError("Nenhum registro encontrado para Guarulhos.")

    print(f"Registros encontrados: {len(df)}")

    return df

def dividir_dados(df):

    quantidade_processadores = min(num_threads_or_process,len(df))

    indices = np.array_split(np.arange(len(df)),quantidade_processadores)

    partes = [df.iloc[indice].copy() for indice in indices
        if len(indice) > 0]

    return partes

def combinar_resultados(resultados):
    soma_total = 0
    qtd_total = 0
    partidos_lista = []
    cargos_lista = []

    for soma, qtd, partidos, cargo in resultados:
        soma_total += soma
        qtd_total += qtd
        partidos_lista.append(partidos)
        cargos_lista.append(cargo)

    df_partidos = pd.concat(partidos_lista).groupby(level=0).sum()
    df_cargos = pd.concat(cargos_lista).groupby(level=0).sum()

    media_global = soma_total / qtd_total if qtd_total > 0 else 0
    media_partidos = df_partidos["sum"] / df_partidos["count"]
    media_cargos = df_cargos["sum"] / df_cargos["count"]

    return media_global, media_partidos, media_cargos


def executar_processos(df):

    partes = dividir_dados(df)

    print(f"Quantidade de processos: {len(partes)}")

    with multiprocessing.Pool(
        processes=len(partes)
    ) as pool:

        resultados = pool.map(calcular, partes)

    return combinar_resultados(resultados)

def executar_threads(df):

    partes = dividir_dados(df)

    print(f"Quantidade de threads: {len(partes)}")

    with ThreadPoolExecutor(
        max_workers=len(partes)
    ) as executor:

        resultados = list(executor.map(calcular, partes))

    return combinar_resultados(resultados)


def mostrar_resultados(titulo, resultado):

    media_global, media_partidos, media_cargos = resultado

    partido_vencedor = media_partidos.idxmax()
    cargo_vencedor = media_cargos.idxmax()

    tabela = Table(
        title=titulo,
        box=box.ROUNDED,
        title_style="bold cyan",
        header_style="bold magenta"
    )

    tabela.add_column("Indicador", style="cyan")
    tabela.add_column("Resultado", style="green")
    tabela.add_column("Média de votos", justify="right", style="yellow")

    tabela.add_row(
        "Média geral",
        municipio,
        f"{media_global:.2f}"
    )

    tabela.add_row(
        "Partido vencedor",
        str(partido_vencedor),
        f"{media_partidos[partido_vencedor]:.2f}"
    )

    tabela.add_row(
        "Cargo vencedor",
        str(cargo_vencedor),
        f"{media_cargos[cargo_vencedor]:.2f}"
    )

    console.print(tabela)


def conferir_resultados(resultado1, resultado2):

    media1, partidos1, cargos1 = resultado1
    media2, partidos2, cargos2 = resultado2

    def series_iguais(a, b):

        a = a.sort_index()
        b = b.sort_index()

        return (
            a.index.equals(b.index)
            and np.allclose(
                a.to_numpy(dtype=float),
                b.to_numpy(dtype=float),
                rtol=1e-10,atol=1e-10))

    return (
        np.isclose(media1, media2, rtol=1e-10, atol=1e-10)
        and series_iguais(partidos1, partidos2)
        and series_iguais(cargos1, cargos2))


def comparar_desempenho(tempo_processos, tempo_threads):

    tabela = Table(
        title="COMPARANDO O DESEMPENHO",
        box=box.ROUNDED,
        title_style="bold cyan"
    )

    tabela.add_column("Abordagem", style="cyan")
    tabela.add_column("Tempo (segundos)", justify="right")
    tabela.add_column("Desempenho", justify="center")

    tabela.add_row(
        "Multiprocessing",
        f"{tempo_processos:.4f}",
        "[green]Mais rápido[/green]"
        if tempo_processos < tempo_threads
        else "[yellow]—[/yellow]"
    )

    tabela.add_row("Multithreading",f"{tempo_threads:.4f}","[green]Mais rápido[/green]"
        if tempo_threads < tempo_processos
        else "[yellow]—[/yellow]"
    )

    console.print(tabela)

    if tempo_processos < tempo_threads:
        console.print("[bold green]Multiprocessing foi mais rápido![/bold green]")

    elif tempo_threads < tempo_processos:
        console.print("[bold green]Multithreading foi mais rápido![/bold green]")

    else:
        console.print("[bold yellow]As duas abordagens tiveram o mesmo tempo![/bold yellow]")

if __name__ == "__main__":

    console.print(
        Panel("[bold cyan]ANÁLISE ELEITORAL[/bold cyan]\n""[white]Comparação entre Processos e Threads[/white]\n"
            f"[yellow]Município: {municipio}[/yellow]",border_style="cyan",box=box.DOUBLE))

    inicio_leitura = time.perf_counter()

    df = carregar_dados()

    tempo_leitura = time.perf_counter() - inicio_leitura


    inicio_processos = time.perf_counter()

    resultado_do_processo = executar_processos(df)

    tempo_do_processo = time.perf_counter() - inicio_processos

    inicio_thread = time.perf_counter()

    resultado_da_threads = executar_threads(df)

    tempo_da_threads = time.perf_counter() - inicio_thread

    mostrar_resultados("RESULTADO DO MULTIPROCESSAMENTO",resultado_do_processo)

    mostrar_resultados("RESULTADO DO MULTITHREADING",resultado_da_threads)

    comparar_desempenho(tempo_do_processo,tempo_da_threads)

    if conferir_resultados(resultado_do_processo,resultado_da_threads):

        console.print(
            Panel("[bold green]Os resultados de processos e threads são iguais![/bold green]",title="VALIDANDO",
                border_style="green"))

    else:

        console.print(Panel("[bold red]ATENÇÃO: Os resultados são diferentes![/bold red]",title="VALIDANDO",
        border_style="red"))

    console.print("\n[bold cyan]Programa finalizado![/bold cyan]")