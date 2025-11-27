import streamlit as st
import pandas as pd
import os
import ast

# ---------------------------
# Configuração básica
# ---------------------------
st.set_page_config(
    page_title="Capacidade x Demanda - Laboratório",
    layout="wide"
)

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

PATH_COLAB = os.path.join(DATA_DIR, "colaboradores.csv")
PATH_MICRO = os.path.join(DATA_DIR, "microareas.csv")
PATH_ATIV = os.path.join(DATA_DIR, "atividades.csv")
PATH_DEM = os.path.join(DATA_DIR, "demandas.csv")


# ---------------------------
# Funções utilitárias de dados
# ---------------------------
def load_csv(path, columns):
    if not os.path.exists(path):
        df = pd.DataFrame(columns=columns)
        df.to_csv(path, index=False)
    else:
        df = pd.read_csv(path)
    # Garante todas as colunas
    for c in columns:
        if c not in df.columns:
            df[c] = None
    return df[columns]


def save_csv(path, df):
    df.to_csv(path, index=False)


def get_colaboradores():
    cols = [
        "id", "nome", "tipo", "carga_diaria", "microarea_principal",
        "microareas_secundarias", "ativo"
    ]
    df = load_csv(PATH_COLAB, cols)
    # Ajustes de tipo
    if df.empty:
        return df
    df["carga_diaria"] = pd.to_numeric(df["carga_diaria"], errors="coerce")
    df["ativo"] = df["ativo"].fillna("sim")
    return df


def get_microareas():
    cols = ["id", "nome", "descricao"]
    return load_csv(PATH_MICRO, cols)


def get_atividades():
    cols = [
        "id", "nome", "microarea", "categoria", "responsavel_funcao",
        "executores_ids", "pesos_executores", "hh_por_unidade"
    ]
    df = load_csv(PATH_ATIV, cols)
    if df.empty:
        return df
    df["hh_por_unidade"] = pd.to_numeric(df["hh_por_unidade"], errors="coerce")
    return df


def get_demandas():
    cols = ["id", "periodo", "atividade_id", "quantidade"]
    df = load_csv(PATH_DEM, cols)
    if df.empty:
        return df
    df["quantidade"] = pd.to_numeric(df["quantidade"], errors="coerce")
    return df


def new_id(df):
    if df.empty or "id" not in df.columns:
        return 1
    return int(df["id"].max()) + 1


def parse_list(value):
    """Converte string em lista (usando ast.literal_eval) ou retorna []"""
    if pd.isna(value) or value == "":
        return []
    if isinstance(value, list):
        return value
    try:
        return ast.literal_eval(str(value))
    except Exception:
        return []


# ---------------------------
# Cálculos de capacidade e alocação
# ---------------------------
def calcular_capacidades(colabs, periodo):
    """
    Capacidade mensal simplificada: carga_diaria * 5 * 4.
    Retorna df com colunas: id, nome, capacidade_mensal
    """
    df = colabs.copy()
    df["capacidade_mensal"] = df["carga_diaria"].fillna(0) * 5 * 4
    return df[["id", "nome", "microarea_principal", "capacidade_mensal"]]


def calcular_alocacoes(colabs, microareas, atividades, demandas, periodo):
    """
    Calcula horas necessárias por atividade e distribui entre executores
    proporcionalmente aos pesos.
    Retorna:
      - df_aloc_colab: horas por colaborador (id_colaborador, hh_alocadas)
      - df_micro: demanda x capacidade por microarea
    """
    # Filtra demandas do período
    dem = demandas[demandas["periodo"] == periodo].copy()
    if dem.empty:
        return (
            pd.DataFrame(columns=["id_colaborador", "hh_alocadas"]),
            pd.DataFrame(columns=[
                "microarea", "hh_necessarias", "capacidade_microarea", "saldo"
            ])
        )

    # Junta com atividades
    ativ = atividades.copy()
    dem_ativ = dem.merge(
        ativ,
        left_on="atividade_id",
        right_on="id",
        suffixes=("_dem", "_ativ")
    )

    # Calcula hh total por atividade
    dem_ativ["hh_total_atividade"] = (
        dem_ativ["quantidade"] * dem_ativ["hh_por_unidade"]
    )

    # Distribui por executores
    alocacoes = []

    for _, row in dem_ativ.iterrows():
        hh_total = row["hh_total_atividade"]
        microarea = row["microarea"]
        atividade_id = row["atividade_id"]

        executores_ids = parse_list(row["executores_ids"])
        pesos_exec = parse_list(row["pesos_executores"])

        if not executores_ids:
            # Se não tem executor definido, não aloca
            continue

        # Ajusta pesos: se vazio ou tamanho diferente, usa 1 para todos
        if not pesos_exec or len(pesos_exec) != len(executores_ids):
            pesos_exec = [1] * len(executores_ids)

        soma_pesos = sum(pesos_exec) if sum(pesos_exec) > 0 else 1

        for colab_id, peso in zip(executores_ids, pesos_exec):
            frac = peso / soma_pesos
            hh_exec = hh_total * frac
            alocacoes.append({
                "id_colaborador": colab_id,
                "atividade_id": atividade_id,
                "microarea": microarea,
                "hh_alocadas": hh_exec
            })

    if not alocacoes:
        df_aloc = pd.DataFrame(columns=["id_colaborador", "hh_alocadas"])
    else:
        df_aloc = pd.DataFrame(alocacoes)
        df_aloc = df_aloc.groupby("id_colaborador", as_index=False)["hh_alocadas"].sum()

    # Demanda por microarea
    dem_micro = dem_ativ.groupby("microarea", as_index=False)["hh_total_atividade"].sum()
    dem_micro.rename(columns={"hh_total_atividade": "hh_necessarias"}, inplace=True)

    # Capacidade por microarea (considerando microarea_principal)
    caps = calcular_capacidades(colabs, periodo)
    cap_micro = caps.groupby("microarea_principal", as_index=False)["capacidade_mensal"].sum()
    cap_micro.rename(columns={
        "microarea_principal": "microarea",
        "capacidade_mensal": "capacidade_microarea"
    }, inplace=True)

    df_micro = dem_micro.merge(cap_micro, on="microarea", how="left")
    df_micro["capacidade_microarea"] = df_micro["capacidade_microarea"].fillna(0)
    df_micro["saldo"] = df_micro["capacidade_microarea"] - df_micro["hh_necessarias"]

    return df_aloc, df_micro


# ---------------------------
# Telas
# ---------------------------
def tela_colaboradores():
    st.header("Cadastro de Colaboradores")

    colabs = get_colaboradores()
    microareas = get_microareas()

    st.subheader("Novo colaborador")

    with st.form("form_colaborador"):
        nome = st.text_input("Nome")
        tipo = st.selectbox("Tipo", ["funcionario", "estagiario"])
        if tipo == "funcionario":
            carga_default = 8.0
        else:
            carga_default = 6.0

        carga_diaria = st.number_input(
            "Carga horária diária (h)",
            min_value=1.0, max_value=12.0,
            value=carga_default, step=0.5
        )

        micro_princ = st.selectbox(
            "Micro-área principal",
            options=[""] + microareas["nome"].tolist()
        )

        micro_sec = st.text_input(
            "Micro-áreas secundárias (separe por vírgula, opcional)"
        )

        ativo = st.checkbox("Ativo", value=True)

        submitted = st.form_submit_button("Salvar colaborador")

        if submitted:
            if not nome:
                st.error("Informe o nome do colaborador.")
            else:
                new = {
                    "id": new_id(colabs),
                    "nome": nome,
                    "tipo": tipo,
                    "carga_diaria": carga_diaria,
                    "microarea_principal": micro_princ,
                    "microareas_secundarias": micro_sec,
                    "ativo": "sim" if ativo else "nao"
                }
                colabs = pd.concat([colabs, pd.DataFrame([new])], ignore_index=True)
                save_csv(PATH_COLAB, colabs)
                st.success("Colaborador salvo com sucesso!")

    st.subheader("Colaboradores cadastrados")
    if colabs.empty:
        st.info("Nenhum colaborador cadastrado ainda.")
    else:
        colabs_show = colabs.copy()
        colabs_show["capacidade_mensal"] = colabs_show["carga_diaria"].fillna(0) * 5 * 4
        st.dataframe(colabs_show, use_container_width=True)


def tela_microareas_atividades():
    st.header("Cadastro de Micro-áreas e Atividades")

    microareas = get_microareas()
    atividades = get_atividades()
    colabs = get_colaboradores()

    tab_micro, tab_ativ = st.tabs(["Micro-áreas", "Atividades"])

    # ---- Micro-áreas ----
    with tab_micro:
        st.subheader("Nova micro-área")
        with st.form("form_micro"):
            nome = st.text_input("Nome da micro-área")
            descricao = st.text_area("Descrição (opcional)")
            submitted = st.form_submit_button("Salvar micro-área")

            if submitted:
                if not nome:
                    st.error("Informe um nome para a micro-área.")
                else:
                    if (microareas["nome"] == nome).any():
                        st.warning("Já existe uma micro-área com esse nome.")
                    else:
                        new = {
                            "id": new_id(microareas),
                            "nome": nome,
                            "descricao": descricao
                        }
                        microareas = pd.concat(
                            [microareas, pd.DataFrame([new])],
                            ignore_index=True
                        )
                        save_csv(PATH_MICRO, microareas)
                        st.success("Micro-área salva com sucesso!")

        st.subheader("Micro-áreas cadastradas")
        if microareas.empty:
            st.info("Nenhuma micro-área cadastrada ainda.")
        else:
            st.dataframe(microareas, use_container_width=True)

    # ---- Atividades ----
    with tab_ativ:
        st.subheader("Nova atividade")

        with st.form("form_ativ"):
            nome_ativ = st.text_input("Nome da atividade")
            micro = st.selectbox(
                "Micro-área",
                options=[""] + microareas["nome"].tolist()
            )
            categoria = st.text_input(
                "Categoria (ensaio, relatório, setup, análise, etc.)",
                value=""
            )

            responsavel_funcao = st.selectbox(
                "Responsável pela função",
                options=[""] + colabs["nome"].tolist()
            )

            executores_nomes = st.multiselect(
                "Colaboradores executores (quem pode executar esta atividade)",
                options=colabs["nome"].tolist()
            )

            pesos_str = st.text_input(
                "Pesos dos executores (mesma ordem, separados por vírgula; deixe vazio para peso 1 para todos)",
                value=""
            )

            hh_por_unidade = st.number_input(
                "Horas por unidade de atividade (hh/unidade)",
                min_value=0.0, step=0.5, value=1.0
            )

            submitted_ativ = st.form_submit_button("Salvar atividade")

            if submitted_ativ:
                if not nome_ativ or not micro:
                    st.error("Informe pelo menos nome da atividade e micro-área.")
                else:
                    # Mapeia executores para ids
                    exec_ids = []
                    for n in executores_nomes:
                        row = colabs[colabs["nome"] == n]
                        if not row.empty:
                            exec_ids.append(int(row.iloc[0]["id"]))

                    # Parse pesos
                    pesos = []
                    if pesos_str.strip():
                        try:
                            pesos = [float(x.strip()) for x in pesos_str.split(",")]
                        except Exception:
                            st.error("Não foi possível interpretar os pesos. Use números separados por vírgula.")
                            st.stop()

                    new = {
                        "id": new_id(atividades),
                        "nome": nome_ativ,
                        "microarea": micro,
                        "categoria": categoria,
                        "responsavel_funcao": responsavel_funcao,
                        "executores_ids": str(exec_ids),
                        "pesos_executores": str(pesos),
                        "hh_por_unidade": hh_por_unidade
                    }
                    atividades = pd.concat(
                        [atividades, pd.DataFrame([new])],
                        ignore_index=True
                    )
                    save_csv(PATH_ATIV, atividades)
                    st.success("Atividade salva com sucesso!")

        st.subheader("Atividades cadastradas")
        if atividades.empty:
            st.info("Nenhuma atividade cadastrada ainda.")
        else:
            st.dataframe(atividades, use_container_width=True)


def tela_demandas():
    st.header("Cadastro de Demandas")

    atividades = get_atividades()
    demandas = get_demandas()

    with st.form("form_demanda"):
        periodo = st.text_input("Período (ex.: 2025-11)", value="")
        if atividades.empty:
            st.warning("Cadastre atividades antes de inserir demanda.")
            st.stop()

        nome_ativ = st.selectbox(
            "Atividade",
            options=atividades["nome"].tolist()
        )

        quantidade = st.number_input(
            "Quantidade prevista no período",
            min_value=0.0, step=1.0, value=1.0
        )

        submitted_dem = st.form_submit_button("Salvar demanda")

        if submitted_dem:
            if not periodo:
                st.error("Informe o período.")
            else:
                # Pega id da atividade
                row_ativ = atividades[atividades["nome"] == nome_ativ].iloc[0]
                atividade_id = int(row_ativ["id"])
                new = {
                    "id": new_id(demandas),
                    "periodo": periodo,
                    "atividade_id": atividade_id,
                    "quantidade": quantidade
                }
                demandas = pd.concat(
                    [demandas, pd.DataFrame([new])],
                    ignore_index=True
                )
                save_csv(PATH_DEM, demandas)
                st.success("Demanda salva com sucesso!")

    st.subheader("Demandas cadastradas")
    if demandas.empty:
        st.info("Nenhuma demanda cadastrada ainda.")
    else:
        df_show = demandas.merge(
            atividades[["id", "nome", "microarea", "hh_por_unidade"]],
            left_on="atividade_id",
            right_on="id",
            suffixes=("", "_ativ")
        )
        df_show["hh_total_atividade"] = df_show["quantidade"] * df_show["hh_por_unidade"]
        df_show = df_show[[
            "id_x", "periodo", "nome", "microarea",
            "quantidade", "hh_por_unidade", "hh_total_atividade"
        ]]
        df_show.rename(columns={"id_x": "id_demanda", "nome": "atividade"}, inplace=True)
        st.dataframe(df_show, use_container_width=True)


def tela_painel():
    st.header("Painel Geral – Demanda x Capacidade")

    colabs = get_colaboradores()
    microareas = get_microareas()
    atividades = get_atividades()
    demandas = get_demandas()

    if atividades.empty or demandas.empty or colabs.empty:
        st.warning("Para visualizar o painel, é necessário ter colaboradores, atividades e demandas cadastradas.")
        return

    periodos = sorted(demandas["periodo"].dropna().unique().tolist())
    periodo_sel = st.selectbox("Selecione o período", options=periodos)

    # Cálculos
    df_caps = calcular_capacidades(colabs, periodo_sel)
    df_aloc, df_micro = calcular_alocacoes(colabs, microareas, atividades, demandas, periodo_sel)

    # ---- Visão por micro-área ----
    st.subheader("Demanda x Capacidade por Micro-área")

    if df_micro.empty:
        st.info("Nenhuma demanda para o período selecionado.")
    else:
        st.dataframe(df_micro, use_container_width=True)

        # Gráfico
        st.bar_chart(
            df_micro.set_index("microarea")[["hh_necessarias", "capacidade_microarea"]]
        )

    # ---- Visão por colaborador ----
    st.subheader("Utilização por colaborador")

    # Junta capacidade com horas alocadas
    df_col = df_caps.merge(
        df_aloc,
        left_on="id",
        right_on="id_colaborador",
        how="left"
    )
    df_col["hh_alocadas"] = df_col["hh_alocadas"].fillna(0.0)
    df_col["utilizacao_%"] = (df_col["hh_alocadas"] / df_col["capacidade_mensal"].replace(0, pd.NA)) * 100
    df_col["utilizacao_%"] = df_col["utilizacao_%"].round(1)

    df_col_show = df_col[[
        "nome", "microarea_principal", "capacidade_mensal", "hh_alocadas", "utilizacao_%"
    ]].sort_values("utilizacao_%", ascending=False)

    st.dataframe(df_col_show, use_container_width=True)

    # ---- Necessidade extra por micro-área ----
    st.subheader("Necessidade de capacidade adicional")

    if not df_micro.empty:
        df_deficit = df_micro[df_micro["saldo"] < 0].copy()
        if df_deficit.empty:
            st.success("Não há déficit de capacidade nas micro-áreas para o período selecionado.")
        else:
            df_deficit["faltam_horas"] = -df_deficit["saldo"]
            # 160h/mês = 8h * 5d * 4sem (funcionário)
            df_deficit["equiv_funcionarios"] = (df_deficit["faltam_horas"] / 160).round(2)
            # 120h/mês = 6h * 5d * 4sem (estagiário)
            df_deficit["equiv_estagiarios"] = (df_deficit["faltam_horas"] / 120).round(2)

            st.dataframe(
                df_deficit[[
                    "microarea", "hh_necessarias", "capacidade_microarea",
                    "faltam_horas", "equiv_funcionarios", "equiv_estagiarios"
                ]],
                use_container_width=True
            )


# ---------------------------
# Navegação principal
# ---------------------------
def main():
    st.title("Gestão de Demanda x Capacidade do Laboratório")

    menu = st.sidebar.radio(
        "Navegação",
        [
            "Colaboradores",
            "Micro-áreas & Atividades",
            "Demandas",
            "Painel"
        ]
    )

    if menu == "Colaboradores":
        tela_colaboradores()
    elif menu == "Micro-áreas & Atividades":
        tela_microareas_atividades()
    elif menu == "Demandas":
        tela_demandas()
    elif menu == "Painel":
        tela_painel()


if __name__ == "__main__":
    main()

