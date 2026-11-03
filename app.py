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
    console.print(
        Panel(
            "[bold cyan]ANÁLISE ELEITORAL[/bold cyan]",
            border_style="cyan",
            box=box.ROUNDED,
            expand=False
        )
    )
    console.print("[bold white]Lendo o arquivo...[/bold white]\n")

    df = pd.read_csv(ARQUIVO, sep=";", encoding="latin1", low_memory=False)
    df_filtrado = df[df["NM_MUNICIPIO"].astype(str).str.strip().str.upper() == MUNICIPIO].copy()
    
    total_registros = len(df_filtrado)

    tabela_info = Table(title="DADOS", box=box.ROUNDED)
    tabela_info.add_column("Itens", style="bold cyan")
    tabela_info.add_column("Detalhes", style="purple")
    tabela_info.add_row("PID Principal(N° de identificação do sistema)", str(os.getpid()))
    tabela_info.add_row("Município Selecionado", MUNICIPIO)
    tabela_info.add_row("Total de Registros", f"{total_registros:,}")
    tabela_info.add_row("N° de divisões", f"{TOTAL_DE_DIVISOES} (threads/processos)")
    
    console.print(tabela_info)
    console.print()

    tamanho_chunk = len(df_filtrado) // TOTAL_DE_DIVISOES 
    chunks = [
        df_filtrado.iloc[i * tamanho_chunk : (i + 1) * tamanho_chunk if i < TOTAL_DE_DIVISOES - 1 else len(df_filtrado)].copy()
        for i in range(TOTAL_DE_DIVISOES)
    ]

    res_final_threads, tempo_threads = rodar_com_threads(chunks)
    res_final_processos, tempo_processos = rodar_com_processos(chunks)

    tabela_resultados = Table(title="RESULTADOS DA APURAÇÃO", box=box.ROUNDED)
    tabela_resultados.add_column("Indicador Requisitado", style="bold cyan")
    tabela_resultados.add_column("Detalhes / Vencedor", style="bold green")
    tabela_resultados.add_column("Média de Votos", justify="right", style="purple")

    tabela_resultados.add_row(
        "Média Geral do Município",
        MUNICIPIO,
        f"{res_final_threads['media_geral']:.2f}"
    )
    tabela_resultados.add_row(
        "Partido com Melhor Média",
        str(res_final_threads["partido_vencedor"]),
        f"{res_final_threads['media_partido_vencedor']:.2f}"
    )
    tabela_resultados.add_row(
        "Cargo com Melhor Média",
        str(res_final_threads["cargo_vencedor"]),
        f"{res_final_threads['media_cargo_vencedor']:.2f}"
    )

    console.print(tabela_resultados)
    console.print()

    tabela_desempenho = Table(title="COMPARANDO O DESEMPENHO", box=box.ROUNDED)
    tabela_desempenho.add_column("Abordagem", style="bold cyan")
    tabela_desempenho.add_column("Tempo de Execução (s)", justify="right", style="purple")
    tabela_desempenho.add_column("Vencedor (Melhor Desempenho)", justify="center")

    eh_processo_mais_rapido = tempo_processos < tempo_threads

    tabela_desempenho.add_row(
        "Multiprocessing",
        f"{tempo_processos:.4f}",
        "[bold green]Mais Rápido[/bold green]" if eh_processo_mais_rapido else "[purple]—[/purple]"
    )
    tabela_desempenho.add_row(
        "Multithreading",
        f"{tempo_threads:.4f}",
        "[bold green]Mais Rápido[/bold green]" if not eh_processo_mais_rapido else "[purple]—[/purple]"
    )

    console.print(tabela_desempenho)

    console.print("\n[bold cyan]Programa finalizado![/bold cyan]")