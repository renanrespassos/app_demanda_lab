import streamlit as st
import pandas as pd
import os

# ---------------------------
# Configuração básica e paths
# ---------------------------
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

PATH_COLAB = os.path.join(DATA_DIR, "colaboradores.csv")
PATH_MICRO = os.path.join(DATA_DIR, "microareas.csv")
PATH_ATIV = os.path.join(DATA_DIR, "atividades.csv")
PATH_DEM = os.path.join(DATA_DIR, "demandas.csv")
PATH_COLAB_ATIV = os.path.join(DATA_DIR, "colab_atividades.csv")


# ---------------------------
# Funções utilitárias
# ---------------------------
def load_csv(path, columns):
    if not os.path.exists(path):
        df = pd.DataFrame(columns=columns)
        df.to_csv(path, index=False)
    else:
        df = pd.read_csv(path)
    # garante todas as colunas
    for c in columns:
        if c not in df.columns:
            df[c] = None
    return df[columns]


def save_csv(path, df):
    df.to_csv(path, index=False)


def get_colaboradores():
    cols = [
        "id", "nome", "cargo", "carga_diaria",
        "microarea_principal", "microareas_secundarias", "ativo"
    ]
    df = load_csv(PATH_COLAB, cols)
    if df.empty:
        return df
    df["carga_diaria"] = pd.to_numeric(df["carga_diaria"], errors="coerce")
    df["ativo"] = df["ativo"].fillna("sim")
    return df


def get_microareas():
    cols = ["id", "nome", "descricao"]
    return l
