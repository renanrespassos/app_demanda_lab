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
    return load_csv(PATH_MICRO, cols)


def get_atividades():
    cols = [
        "id", "nome", "microarea", "categoria",
        "responsavel_funcao", "hh_por_unidade"
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


def get_colab_atividades():
    # vínculo colaborador x atividade x microarea x percentual
    cols = ["id", "colab_id", "atividade_id", "microarea", "percentual"]
    df = load_csv(PATH_COLAB_ATIV, cols)
    if df.empty:
        return df
    df["colab_id"] = pd.to_numeric(df["colab_id"], errors="coerce")
    df["atividade_id"] = pd.to_numeric(df["atividade_id"], errors="coerce")
    df["percentual"] = pd.to_numeric(df["percentual"], errors="coerce")
    return df


def new_id(df):
    if df.empty or "id" not in df.columns:
        return 1
    return int(df["id"].max()) + 1


# ---------------------------
# Cálculos de capacidade e alocação
# ---------------------------
def calcular_capacidades(colabs, periodo):
    # capacidade mensal simples: carga_diaria * 5 dias * 4 semanas
    df = colabs.copy()
    df["capacidade_mensal"] = df["carga_diaria"].fillna(0) * 5 * 4
    return df[["id", "nome", "cargo", "microarea_principal", "capacidade_mensal"]]


def calcular_alocacoes(colabs, microareas, atividades, demandas, colab_ativ, periodo):
    # filtra demandas do período
    dem = demandas[demandas["periodo"] == periodo].copy()
    if dem.empty:
        return (
            pd.DataFrame(columns=["id_colaborador", "hh_alocadas"]),
            pd.DataFrame(columns=[
                "microarea", "hh_necessarias", "capacidade_microarea", "saldo"
            ])
        )

    # junta demanda com atividades
    ativ = atividades.copy()
    dem_ativ = dem.merge(
        ativ,
        left_on="atividade_id",
        right_on="id",
        suffixes=("_dem", "_ativ")
    )

    # hh total da atividade (demanda)
    dem_ativ["hh_total_atividade"] = (
        dem_ativ["quantidade"] * dem_ativ["hh_por_unidade"]
    )

    # --- Distribuição das horas por colaborador, usando percentuais configurados ---
    alocacoes = []

    for _, row in dem_ativ.iterrows():
        atividade_id = int(row["atividade_id"])
        microarea = row["microarea"]
        hh_total = row["hh_total_atividade"]

        # pega vínculo colaborador-atividade
        ca = colab_ativ[colab_ativ["atividade_id"] == atividade_id]
        if ca.empty:
            continue

        pesos = ca["percentual"].fillna(0).tolist()
        colab_ids = ca["colab_id"].tolist()
        if not pesos or sum(pesos) == 0:
            pesos = [1] * len(colab_ids)

        soma_pesos = float(sum(pesos))
        for colab_id, peso in zip(colab_ids, pesos):
            frac = peso / soma_pesos
            hh_exec = hh_total * frac
            alocacoes.append({
                "id_colaborador": int(colab_id),
                "atividade_id": atividade_id,
                "microarea": microarea,
                "hh_alocadas": hh_exec
            })

    if not alocacoes:
        df_aloc = pd.DataFrame(columns=["id_colaborador", "hh_alocadas"])
    else:
        df_aloc = pd.DataFrame(alocacoes)
        df_aloc = df_aloc.groupby("id_colaborador", as_index=False)["hh_alocadas"].sum()

    # --- Demanda por microarea ---
    dem_micro = dem_ativ.groupby("microarea", as_index=False)["hh_total_atividade"].sum()
    dem_micro.rename(columns={"hh_total_atividade": "hh_necessarias"}, inplace=True)

    # --- Capacidade por microarea (usa microarea_principal de cada colaborador) ---
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
# Tela: Colaboradores
# ---------------------------
def tela_colaboradores():
    st.header("Cadastro de Colaboradores")

    colabs = get_colaboradores()
    microareas = get_microareas()
    colab_ativ = get_colab_atividades()
    atividades = get_atividades()

    # ---- Cadastro básico: Nome, Cargo, Carga horária ----
    st.subheader("Novo colaborador")

    with st.form("form_colaborador"):
        nome = st.text_input("Nome")

        cargo = st.selectbox(
            "Cargo",
            ["Estagiário", "Assistente", "Analista", "Especialista", "Coordenador"]
        )

        # default de carga horária por cargo
        if cargo == "Estagiário":
            carga_default = 6.0
        else:
            carga_default = 8.0

        carga_diaria = st.number_input(
            "Carga horária diária (h)",
            min_value=1.0, max_value=12.0,
            value=carga_default, step=0.5
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
                    "cargo": cargo,
                    "carga_diaria": carga_diaria,
                    "microarea_principal": "",
                    "microareas_secundarias": "",
                    "ativo": "sim" if ativo else "nao"
                }
                colabs = pd.concat([colabs, pd.DataFrame([new])], ignore_index=True)
                save_csv(PATH_COLAB, colabs)
                st.success("Colaborador salvo com sucesso!")

    # ---- Tabela de colaboradores ----
    st.subheader("Colaboradores cadastrados")
    if colabs.empty:
        st.info("Nenhum colaborador cadastrado ainda.")
    else:
        colabs_show = colabs.copy()
        colabs_show["capacidade_mensal"] = colabs_show["carga_diaria"].fillna(0) * 5 * 4
        st.dataframe(colabs_show, use_container_width=True)

    # ---- Configurar área de atuação e atividades por colaborador ----
    st.subheader("Configurar área de atuação e atividades do colaborador")

    if colabs.empty or atividades.empty or microareas.empty:
        st.info("Cadastre colaboradores, micro-áreas e atividades para configurar área de atuação.")
        return

    with st.form("form_atuacao"):
        colab_nome = st.selectbox(
            "Colaborador",
            options=colabs["nome"].tolist()
        )
        colab_row = colabs[colabs["nome"] == colab_nome].iloc[0]
        colab_id = int(colab_row["id"])

        # micro-área principal do colaborador (para capacidade por microarea)
        micro_princ = st.selectbox(
            "Micro-área principal deste colaborador",
            options=[""] + microareas["nome"].tolist(),
            index=0 if colab_row["microarea_principal"] not in microareas["nome"].tolist()
            else ([""] + microareas["nome"].tolist()).index(colab_row["microarea_principal"])
        )

        # microarea da atividade
        micro_sel = st.selectbox(
            "Micro-área da atividade",
            options=microareas["nome"].tolist()
        )

        atividades_micro = atividades[atividades["microarea"] == micro_sel]
        if atividades_micro.empty:
            st.warning("Não há atividades cadastradas para esta micro-área.")
            atividade_nome = None
        else:
            atividade_nome = st.selectbox(
                "Atividade",
                options=atividades_micro["nome"].tolist()
            )

        percentual = st.number_input(
            "Percentual de participação do colaborador nesta atividade (%)",
            min_value=0.0, max_value=100.0, value=50.0, step=5.0
        )

        submitted_atuacao = st.form_submit_button("Salvar participação")

        if submitted_atuacao:
            # atualiza microarea principal
            colabs.loc[colabs["id"] == colab_id, "microarea_principal"] = micro_princ
            save_csv(PATH_COLAB, colabs)

            if atividade_nome is None:
                st.error("Selecione uma atividade válida.")
            else:
                ativ_row = atividades[atividades["nome"] == atividade_nome].iloc[0]
                atividade_id = int(ativ_row["id"])
                new_map = {
                    "id": new_id(colab_ativ),
                    "colab_id": colab_id,
                    "atividade_id": atividade_id,
                    "microarea": micro_sel,
                    "percentual": percentual
                }
                colab_ativ = pd.concat(
                    [colab_ativ, pd.DataFrame([new_map])],
                    ignore_index=True
                )
                save_csv(PATH_COLAB_ATIV, colab_ativ)
                st.success("Área de atuação / atividade registrada para o colaborador.")

    # ---- Mapa colaborador x atividade ----
    st.subheader("Mapa de atividades por colaborador")
    colab_ativ = get_colab_atividades()
    if colab_ativ.empty:
        st.info("Ainda não há atividades vinculadas a colaboradores.")
    else:
        df_show = colab_ativ.merge(
            colabs[["id", "nome"]],
            left_on="colab_id",
            right_on="id",
            how="left"
        ).merge(
            atividades[["id", "nome", "microarea"]],
            left_on="atividade_id",
            right_on="id",
            how="left",
            suffixes=("_colab", "_ativ")
        )
        df_show = df_show[["nome_colab", "nome_ativ", "microarea_ativ", "percentual"]]
        df_show.rename(columns={
            "nome_colab": "colaborador",
            "nome_ativ": "atividade",
            "microarea_ativ": "microarea"
        }, inplace=True)
        st.dataframe(df_show, use_container_width=True)


# ---------------------------
# Tela: Micro-áreas & Atividades
# ---------------------------
def tela_microareas_atividades():
    st.header("Cadastro de Micro-áreas e Atividades")

    microareas = get_microareas()
    atividades = get_atividades()
    colabs = get_colaboradores()

    tab_micro, tab_ativ = st.tabs(["Micro-áreas", "Atividades"])

    # --- Micro-áreas ---
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

    # --- Atividades ---
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
                "Responsável pela função (opcional)",
                options=[""] + colabs["nome"].tolist()
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
                    new = {
                        "id": new_id(atividades),
                        "nome": nome_ativ,
                        "microarea": micro,
                        "categoria": categoria,
                        "responsavel_funcao": responsavel_funcao,
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


# ---------------------------
# Tela: Demandas
# ---------------------------
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


# ---------------------------
# Tela: Painel
# ---------------------------
def tela_painel():
    st.header("Painel Geral - Demanda x Capacidade")

    colabs = get_colaboradores()
    microareas = get_microareas()
    atividades = get_atividades()
    demandas = get_demandas()
    colab_ativ = get_colab_atividades()

    if atividades.empty or demandas.empty or colabs.empty:
        st.warning("Para visualizar o painel, é necessário ter colaboradores, atividades e demandas cadastradas.")
        return

    # escolher período
    periodos = sorted(demandas["periodo"].dropna().unique().tolist())
    periodo_sel = st.selectbox("Selecione o período", options=periodos)

    # quantos dias úteis considerar (pra chegar nas horas diárias)
    dias_uteis = st.number_input(
        "Dias úteis no mês (para cálculo das horas diárias)",
        min_value=15, max_value=31, value=22, step=1
    )

    # Cálculos mensais (como já existia)
    df_caps = calcular_capacidades(colabs, periodo_sel)
    df_aloc, df_micro = calcular_alocacoes(colabs, microareas, atividades, demandas, colab_ativ, periodo_sel)

    # ----------------- RESUMO GLOBAL DIÁRIO (estilo sua planilha) -----------------
    st.subheader("Resumo diário global (laboratório)")

    if df_micro.empty:
        st.info("Nenhuma demanda para o período selecionado.")
    else:
        # horas mensais totais necessárias (somando todas as micro-áreas)
        hh_mes_total = df_micro["hh_necessarias"].sum()

        # horas por dia necessárias
        hh_dia_necessarias = hh_mes_total / dias_uteis if dias_uteis > 0 else 0

        # colaboradores equivalentes de 8h/dia necessários
        colabs_necessarios_8h = hh_dia_necessarias / 8 if hh_dia_necessarias > 0 else 0

        # capacidade diária atual (somatório da carga_diaria de todos ativos)
        colabs_ativos = colabs[colabs["ativo"] == "sim"].copy()
        capacidade_dia_atual = colabs_ativos["carga_diaria"].fillna(0).sum()

        # colaboradores equivalentes atuais (convertendo tudo para 8h)
        colabs_atuais_equiv_8h = capacidade_dia_atual / 8 if capacidade_dia_atual > 0 else 0

        gap_colabs_8h = colabs_necessarios_8h - colabs_atuais_equiv_8h

        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "Horas diárias necessárias (todas as atividades)",
                f"{hh_dia_necessarias:.2f} h/dia"
            )
            st.metric(
                "Colaboradores 8h necessários",
                f"{colabs_necessarios_8h:.2f}"
            )
        with col2:
            st.metric(
                "Capacidade diária atual",
                f"{capacidade_dia_atual:.2f} h/dia"
            )
            st.metric(
                "Colaboradores 8h equivalentes atuais",
                f"{colabs_atuais_equiv_8h:.2f}"
            )

        st.markdown(
            f"**Gap de colaboradores (equivalente a 8h/dia):** "
            f"{gap_colabs_8h:.2f} (positivo = falta gente, negativo = sobra capacidade)"
        )

    st.markdown("---")

    # ----------------- Visão por micro-área (igual já tínhamos, só reaproveitada) -----------------
    st.subheader("Demanda x Capacidade por Micro-área")

    if df_micro.empty:
        st.info("Nenhuma demanda para o período selecionado.")
    else:
        st.dataframe(df_micro, use_container_width=True)
        st.bar_chart(
            df_micro.set_index("microarea")[["hh_necessarias", "capacidade_microarea"]]
        )

    # ----------------- Visão por colaborador -----------------
    st.subheader("Utilização por colaborador")

    df_col = df_caps.merge(
        df_aloc,
        left_on("id"),
        right_on("id_colaborador"),
        how="left"
    )
    df_col["hh_alocadas"] = df_col["hh_alocadas"].fillna(0.0)
    df_col["utilizacao_%"] = (
        df_col["hh_alocadas"] / df_col["capacidade_mensal"].replace(0, pd.NA)
    ) * 100
    df_col["utilizacao_%"] = df_col["utilizacao_%"].round(1)

    df_col_show = df_col[[
        "nome", "cargo", "microarea_principal",
        "capacidade_mensal", "hh_alocadas", "utilizacao_%"
    ]].sort_values("utilizacao_%", ascending=False)

    st.dataframe(df_col_show, use_container_width=True)

    # ----------------- Necessidade adicional por micro-área -----------------
    st.subheader("Necessidade de capacidade adicional por micro-área")

    if not df_micro.empty:
        df_deficit = df_micro[df_micro["saldo"] < 0].copy()
        if df_deficit.empty:
            st.success("Não há déficit de capacidade nas micro-áreas para o período selecionado.")
        else:
            df_deficit["faltam_horas"] = -df_deficit["saldo"]
            df_deficit["equiv_funcionarios"] = (df_deficit["faltam_horas"] / 160).round(2)
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
    st.set_page_config(
        page_title="Capacidade x Demanda - Laboratório",
        layout="wide"
    )

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
