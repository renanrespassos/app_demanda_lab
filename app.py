import streamlit as st
import pandas as pd
import os

# ---------------------------
# Paths e diretórios
# ---------------------------
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

PATH_COLAB = os.path.join(DATA_DIR, "colaboradores.csv")
PATH_MICRO = os.path.join(DATA_DIR, "microareas.csv")
PATH_ATIV = os.path.join(DATA_DIR, "atividades.csv")
PATH_DEM = os.path.join(DATA_DIR, "demandas.csv")
PATH_COLAB_ATIV = os.path.join(DATA_DIR, "colab_atividades.csv")

# ---------------------------
# Lista padrão Grupo (microárea) x Atividade
# ---------------------------
DEFAULT_GRUPOS_ATIVIDADES = [
    ("Entrada", "Fotos"),
    ("Entrada", "Dar entrada labtrack"),
    ("Entrada", "Dar entrada atlas"),
    ("Entrada", "Montar minuta"),
    ("Entrada", "Assinar ID"),
    ("Entrada", "Emendas ID"),
    ("Entrada", "Planilha ETS"),
    ("Entrada", "Gerar minutas"),

    ("17087", "Ensaiar aquecimento"),
    ("17087", "Devolução"),
    ("17087", "Choque"),
    ("17087", "Fechar relatório 17087"),
    ("17087", "Assinar 17087"),
    ("17087", "Emendas 17087"),

    ("EMC", "Radiada"),
    ("EMC", "Imunidade"),
    ("EMC", "Intensidade de campo"),
    ("EMC", "Ensaio conduzido"),
    ("EMC", "Imunidade conduzida"),
    ("EMC", "Configurações EMC"),
    ("EMC", "Fechar relatório EMC"),
    ("EMC", "Assinar EMC"),
    ("EMC", "Emendas EMC"),
    ("EMC", "Ensaio acompanhado"),
    ("EMC", "Estudo de Normas, Acompanhamento Clientes, Desenvolvimento da Área, Gerenciar a Agenda"),
    ("EMC", "Dúvidas comercial"),
    ("EMC", "Reuniões"),

    ("RF", "Configurações RF"),
    ("RF", "Wi-Fi"),
    ("RF", "Ensaio DFS"),
    ("RF", "Ensaio SAR"),
    ("RF", "BT"),
    ("RF", "Lora"),
    ("RF", "Emendas RF"),
    ("RF", "Fechar relatório RF"),
    ("RF", "Assinar RF"),
    ("RF", "Reuniões"),
    ("RF", "Dúvidas comercial"),

    ("EMC Extras", "Ensaios Eletrodomésticos"),
    ("EMC Extras", "Devolver eletrodoméstico"),
    ("EMC Extras", "Fechar relatório eletrodomésticos"),
    ("EMC Extras", "Eletromedicos"),
    ("EMC Extras", "Fechar relatório eletromedicos"),
    ("EMC Extras", "Fechar relatório TV"),
    ("EMC Extras", "TVs"),

    ("3GPP", "IPV6"),
    ("3GPP", "Ensaios Funcionais (2G, 3G e 4G)"),
    ("3GPP", "Reuniões"),
    ("3GPP", "Retestes"),
    ("3GPP", "Funcional"),
    ("3GPP", "Fechar relatório ipv6"),

    ("Baterias", "Ensaio de Powerbank"),
    ("Baterias", "Fechar relatório Powerbank"),
    ("Baterias", "Organizar Powerbanks (devolução, cronograma, etc)"),

    ("Acústicos", "Ensaio acústico"),
    ("Acústicos", "Relatórios ensaio acústico"),
    ("Acústicos", "Devolver amostras acústico"),
    ("Acústicos", "Retirar amostras acústico"),
    ("Acústicos", "Fotos das amostras acústico"),
    ("Acústicos", "outros ensaios (Exemplo, TV)"),

    ("Desenvolvimento", "Desenvolvimento de Melhorias"),
]

# ---------------------------
# Lista padrão de colaboradores: (cargo, microarea_principal, nome)
# ---------------------------
DEFAULT_COLABS = [
    ("Estagiário", "Entrada", "Kaua"),
    ("Estagiário", "Entrada", "Henrique"),
    ("Assistente", "Entrada", "Cristian"),
    ("Estagiário", "Entrada", "Isadora"),

    ("Assistente", "17087", "Arthur"),

    ("Analista", "EMC", "Philipe"),
    ("Especialista", "EMC", "Elinaldo"),
    ("Assistente", "EMC", "Fernando"),
    ("Estagiário", "EMC", "João de Paula"),
    ("Assistente", "EMC", "Eduardo Altnetter"),
    ("Assistente", "EMC", "Júlia Nascimento"),
    ("Analista", "EMC", "Felipe Constant"),

    ("Assistente", "RF", "João Daneres"),
    ("Assistente", "RF", "Bernardo"),
    ("Estagiário", "RF", "Rafael"),
    ("Assistente", "RF", "Francis"),
    ("Assistente", "RF", "João Vitor"),
    ("Estagiário", "RF", "Georgia"),

    ("Analista", "3GPP", "Greter"),
    ("Analista", "3GPP", "Eduardo Oliveira"),

    ("Analista", "RF", "João Pinheiro"),
    ("Assistente", "RF", "Marcelo"),

    ("Estagiário", "Baterias", "Fabricio"),
]

# ---------------------------
# Utilitários de dados
# ---------------------------
def load_csv(path, columns):
    if not os.path.exists(path):
        df = pd.DataFrame(columns=columns)
        df.to_csv(path, index=False)
    else:
        df = pd.read_csv(path)
    for c in columns:
        if c not in df.columns:
            df[c] = None
    return df[columns]


def save_csv(path, df):
    df.to_csv(path, index=False)


def new_id(df):
    if df.empty or "id" not in df.columns:
        return 1
    return int(df["id"].max()) + 1


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
    return load_csv(PATH_MICRO, ["id", "nome", "descricao"])


def get_atividades():
    cols = [
        "id", "nome", "microarea", "categoria",
        "responsavel_funcao", "hh_por_unidade", "fator_por_projeto"
    ]
    df = load_csv(PATH_ATIV, cols)
    if df.empty:
        return df
    df["hh_por_unidade"] = pd.to_numeric(df["hh_por_unidade"], errors="coerce")
    df["fator_por_projeto"] = pd.to_numeric(df["fator_por_projeto"], errors="coerce")
    df["hh_por_unidade"] = df["hh_por_unidade"].fillna(1.0)
    df["fator_por_projeto"] = df["fator_por_projeto"].fillna(1.0)
    return df


def get_demandas():
    cols = ["id", "periodo", "atividade_id", "quantidade"]
    df = load_csv(PATH_DEM, cols)
    if df.empty:
        return df
    df["quantidade"] = pd.to_numeric(df["quantidade"], errors="coerce")
    return df


def get_colab_atividades():
    cols = ["id", "colab_id", "atividade_id", "microarea", "percentual"]
    df = load_csv(PATH_COLAB_ATIV, cols)
    if df.empty:
        return df
    df["colab_id"] = pd.to_numeric(df["colab_id"], errors="coerce")
    df["atividade_id"] = pd.to_numeric(df["atividade_id"], errors="coerce")
    df["percentual"] = pd.to_numeric(df["percentual"], errors="coerce")
    return df

# ---------------------------
# Seed inicial de micro-áreas + atividades
# ---------------------------
def seed_default_microareas_atividades(microareas, atividades):
    # Micro-áreas
    existentes_micro = set(microareas["nome"].dropna().tolist())
    novas_micro = []

    for grupo, _ in DEFAULT_GRUPOS_ATIVIDADES:
        if grupo and grupo not in existentes_micro:
            base = microareas if not novas_micro else pd.concat([microareas, pd.DataFrame(novas_micro)], ignore_index=True)
            new = {
                "id": new_id(base),
                "nome": grupo,
                "descricao": ""
            }
            novas_micro.append(new)
            existentes_micro.add(grupo)

    if novas_micro:
        microareas = pd.concat([microareas, pd.DataFrame(novas_micro)], ignore_index=True)
        save_csv(PATH_MICRO, microareas)

    # Atividades
    existentes_ativ = set(atividades["nome"].dropna().tolist())
    novas_ativ = []

    for grupo, nome in DEFAULT_GRUPOS_ATIVIDADES:
        if nome not in existentes_ativ:
            base = atividades if not novas_ativ else pd.concat([atividades, pd.DataFrame(novas_ativ)], ignore_index=True)
            new = {
                "id": new_id(base),
                "nome": nome,
                "microarea": grupo,
                "categoria": "",
                "responsavel_funcao": "",
                "hh_por_unidade": 1.0,      # armazena em horas
                "fator_por_projeto": 1.0    # quantas execuções por projeto
            }
            novas_ativ.append(new)
            existentes_ativ.add(nome)

    if novas_ativ:
        atividades = pd.concat([atividades, pd.DataFrame(novas_ativ)], ignore_index=True)
        save_csv(PATH_ATIV, atividades)

    return microareas, atividades

# ---------------------------
# Seed de colaboradores padrão
# ---------------------------
def seed_default_colaboradores(colabs):
    """
    Cria colaboradores padrão com base em DEFAULT_COLABS.
    Não duplica nomes já existentes.
    """
    existentes = set(colabs["nome"].dropna().tolist())
    novos = []

    for cargo, microarea, nome in DEFAULT_COLABS:
        if nome in existentes:
            continue

        if cargo == "Estagiário":
            carga_diaria = 6.0
        else:
            carga_diaria = 8.0

        base = colabs if not novos else pd.concat([colabs, pd.DataFrame(novos)], ignore_index=True)
        novos.append({
            "id": new_id(base),
            "nome": nome,
            "cargo": cargo,
            "carga_diaria": carga_diaria,
            "microarea_principal": microarea,
            "microareas_secundarias": "",
            "ativo": "sim",
        })
        existentes.add(nome)

    if novos:
        colabs = pd.concat([colabs, pd.DataFrame(novos)], ignore_index=True)
        save_csv(PATH_COLAB, colabs)

    return colabs

# ---------------------------
# Cálculos de capacidade e alocação
# ---------------------------
def calcular_capacidades(colabs, dias_uteis):
    """
    capacidade_diaria = carga_diaria
    capacidade_mensal = capacidade_diaria * dias_uteis
    """
    df = colabs.copy()
    df["capacidade_diaria"] = df["carga_diaria"].fillna(0)
    df["capacidade_mensal"] = df["capacidade_diaria"] * dias_uteis
    return df[["id", "nome", "cargo", "microarea_principal", "capacidade_diaria", "capacidade_mensal"]]


def calcular_alocacoes(colabs, microareas, atividades, demandas, colab_ativ, periodo, dias_uteis):
    """
    Usa demandas (quantidade por atividade) + hh_por_unidade das atividades
    e distribui horas entre colaboradores de acordo com percentuais.
    Também calcula demanda x capacidade por micro-área (mensal).
    """
    dem = demandas[demandas["periodo"] == periodo].copy()
    if dem.empty:
        return (
            pd.DataFrame(columns=["id_colaborador", "hh_alocadas"]),
            pd.DataFrame(columns=["microarea", "hh_necessarias", "capacidade_mensal", "saldo"])
        )

    ativ = atividades.copy()
    dem_ativ = dem.merge(
        ativ,
        left_on="atividade_id",
        right_on="id",
        suffixes=("_dem", "_ativ")
    )

    # Horas totais por atividade no mês
    dem_ativ["hh_total_atividade"] = dem_ativ["quantidade"] * dem_ativ["hh_por_unidade"]

    # Distribuição das horas por colaborador
    alocs = []
    for _, row in dem_ativ.iterrows():
        atividade_id = int(row["atividade_id"])
        microarea = row["microarea"]
        hh_total = row["hh_total_atividade"]

        ca = colab_ativ[colab_ativ["atividade_id"] == atividade_id]
        if ca.empty:
            continue

        pesos = ca["percentual"].fillna(0).tolist()
        colab_ids = ca["colab_id"].tolist()
        if not pesos or sum(pesos) == 0:
            pesos = [1] * len(colab_ids)

        soma_pesos = float(sum(pesos))
        for cid, peso in zip(colab_ids, pesos):
            frac = peso / soma_pesos
            alocs.append({
                "id_colaborador": int(cid),
                "atividade_id": atividade_id,
                "microarea": microarea,
                "hh_alocadas": hh_total * frac
            })

    if not alocs:
        df_aloc = pd.DataFrame(columns=["id_colaborador", "hh_alocadas"])
    else:
        df_aloc = pd.DataFrame(alocs).groupby("id_colaborador", as_index=False)["hh_alocadas"].sum()

    # Demanda por micro-área (mensal)
    dem_micro = dem_ativ.groupby("microarea", as_index=False)["hh_total_atividade"].sum()
    dem_micro.rename(columns={"hh_total_atividade": "hh_necessarias"}, inplace=True)

    # Capacidade mensal por micro-área
    caps = calcular_capacidades(colabs, dias_uteis)
    cap_micro = caps.groupby("microarea_principal", as_index=False)["capacidade_mensal"].sum()
    cap_micro.rename(columns={
        "microarea_principal": "microarea",
        "capacidade_mensal": "capacidade_mensal"
    }, inplace=True)

    df_micro = dem_micro.merge(cap_micro, on="microarea", how="left")
    df_micro["capacidade_mensal"] = df_micro["capacidade_mensal"].fillna(0)
    df_micro["saldo"] = df_micro["capacidade_mensal"] - df_micro["hh_necessarias"]

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

    # Botão para carregar colaboradores padrão
    if st.button("Carregar lista padrão de colaboradores"):
        colabs = seed_default_colaboradores(colabs)
        st.success("Colaboradores padrão carregados/atualizados com sucesso!")

    # Cadastro básico
    st.subheader("Novo colaborador")

    with st.form("form_colaborador"):
        nome = st.text_input("Nome")

        cargo = st.selectbox(
            "Cargo",
            ["Estagiário", "Assistente", "Analista", "Especialista", "Coordenador"]
        )

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

    # Tabela de colaboradores
    st.subheader("Colaboradores cadastrados")
    if colabs.empty:
        st.info("Nenhum colaborador cadastrado ainda.")
    else:
        df_show = colabs.copy()
        df_show["capacidade_diaria"] = df_show["carga_diaria"].fillna(0)
        df_show["capacidade_mensal_22d"] = df_show["capacidade_diaria"] * 22
        st.dataframe(df_show, use_container_width=True)

    # Editar / excluir colaborador
    st.subheader("Editar / excluir colaborador")
    if not colabs.empty:
        nomes_colab = colabs["nome"].tolist()
        sel_nome = st.selectbox("Selecione um colaborador para editar/excluir", options=[""] + nomes_colab)
        if sel_nome:
            row = colabs[colabs["nome"] == sel_nome].iloc[0]
            col1, col2 = st.columns(2)
            with col1:
                novo_nome = st.text_input("Nome", value=row["nome"], key="edit_colab_nome")
                novo_cargo = st.selectbox(
                    "Cargo",
                    ["Estagiário", "Assistente", "Analista", "Especialista", "Coordenador"],
                    index=["Estagiário", "Assistente", "Analista", "Especialista", "Coordenador"].index(row["cargo"]) if row["cargo"] in ["Estagiário", "Assistente", "Analista", "Especialista", "Coordenador"] else 0,
                    key="edit_colab_cargo"
                )
                nova_carga = st.number_input(
                    "Carga horária diária (h)",
                    min_value=1.0, max_value=12.0,
                    value=float(row["carga_diaria"]) if not pd.isna(row["carga_diaria"]) else 8.0,
                    step=0.5,
                    key="edit_colab_carga"
                )
            with col2:
                micro_princ = st.selectbox(
                    "Micro-área principal",
                    options=[""] + microareas["nome"].tolist(),
                    index=0 if row["microarea_principal"] not in microareas["nome"].tolist()
                    else ([""] + microareas["nome"].tolist()).index(row["microarea_principal"]),
                    key="edit_colab_micro"
                )
                ativo_flag = st.checkbox("Ativo", value=(row["ativo"] == "sim"), key="edit_colab_ativo")

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Salvar alterações do colaborador"):
                    colabs.loc[colabs["id"] == row["id"], "nome"] = novo_nome
                    colabs.loc[colabs["id"] == row["id"], "cargo"] = novo_cargo
                    colabs.loc[colabs["id"] == row["id"], "carga_diaria"] = nova_carga
                    colabs.loc[colabs["id"] == row["id"], "microarea_principal"] = micro_princ
                    colabs.loc[colabs["id"] == row["id"], "ativo"] = "sim" if ativo_flag else "nao"
                    save_csv(PATH_COLAB, colabs)
                    st.success("Colaborador atualizado.")
            with col_b:
                if st.button("Excluir colaborador"):
                    # remove vínculos
                    colab_ativ = get_colab_atividades()
                    colab_ativ = colab_ativ[colab_ativ["colab_id"] != row["id"]]
                    save_csv(PATH_COLAB_ATIV, colab_ativ)
                    # remove colaborador
                    colabs = colabs[colabs["id"] != row["id"]]
                    save_csv(PATH_COLAB, colabs)
                    st.success("Colaborador excluído.")

    # Configuração de área de atuação e atividades por colaborador (modo rápido com multiselect)
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

        micro_princ = st.selectbox(
            "Micro-área principal deste colaborador",
            options=[""] + microareas["nome"].tolist(),
            index=0 if colab_row["microarea_principal"] not in microareas["nome"].tolist()
            else ([""] + microareas["nome"].tolist()).index(colab_row["microarea_principal"])
        )

        micro_sel = st.selectbox(
            "Micro-área das atividades a vincular",
            options=microareas["nome"].tolist()
        )

        atividades_micro = atividades[atividades["microarea"] == micro_sel]
        if atividades_micro.empty:
            st.warning("Não há atividades cadastradas para esta micro-área.")
            atividades_sel = []
        else:
            atividades_sel = st.multiselect(
                "Atividades para vincular a este colaborador",
                options=atividades_micro["nome"].tolist()
            )

        percentual = st.number_input(
            "Percentual de participação do colaborador em cada atividade selecionada (%)",
            min_value=0.0, max_value=100.0, value=50.0, step=5.0
        )

        submitted_atuacao = st.form_submit_button("Salvar vínculos de atividades")

        if submitted_atuacao:
            # atualiza microárea principal
            colabs.loc[colabs["id"] == colab_id, "microarea_principal"] = micro_princ
            save_csv(PATH_COLAB, colabs)

            if not atividades_sel:
                st.error("Selecione ao menos uma atividade.")
            else:
                colab_ativ = get_colab_atividades()
                novos = []
                for nome_ativ in atividades_sel:
                    ativ_row = atividades[atividades["nome"] == nome_ativ].iloc[0]
                    atividade_id = int(ativ_row["id"])
                    base = colab_ativ if not novos else pd.concat([colab_ativ, pd.DataFrame(novos)], ignore_index=True)
                    novos.append({
                        "id": new_id(base),
                        "colab_id": colab_id,
                        "atividade_id": atividade_id,
                        "microarea": micro_sel,
                        "percentual": percentual
                    })
                if novos:
                    colab_ativ = pd.concat([colab_ativ, pd.DataFrame(novos)], ignore_index=True)
                    save_csv(PATH_COLAB_ATIV, colab_ativ)
                    st.success("Vínculos de atividades registrados para o colaborador.")

    # Editar / excluir vínculos
    st.subheader("Editar / excluir vínculos de colaborador x atividade")
    colab_ativ = get_colab_atividades()
    if colab_ativ.empty:
        st.info("Ainda não há atividades vinculadas a colaboradores.")
    else:
        df_map = colab_ativ.merge(
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
        df_map_show = df_map[["id_x", "nome_colab", "nome_ativ", "microarea", "percentual"]]
        df_map_show.rename(columns={
            "id_x": "id_vinculo",
            "nome_colab": "colaborador",
            "nome_ativ": "atividade"
        }, inplace=True)
        st.dataframe(df_map_show, use_container_width=True)

        labels = df_map_show.apply(
            lambda r: f'{int(r["id_vinculo"])} - {r["colaborador"]} - {r["atividade"]} ({r["microarea"]})',
            axis=1
        ).tolist()
        ids = df_map_show["id_vinculo"].tolist()
        sel_label = st.selectbox("Selecione um vínculo para editar/excluir", options=[""] + labels)
        if sel_label:
            idx = labels.index(sel_label)
            vinc_id = ids[idx]
            vinc_row = colab_ativ[colab_ativ["id"] == vinc_id].iloc[0]
            novo_percentual = st.number_input(
                "Percentual (%)",
                min_value=0.0, max_value=100.0,
                value=float(vinc_row["percentual"]) if not pd.isna(vinc_row["percentual"]) else 0.0,
                step=5.0,
                key=f"edit_vinc_{vinc_id}"
            )
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Salvar percentual do vínculo"):
                    colab_ativ.loc[colab_ativ["id"] == vinc_id, "percentual"] = novo_percentual
                    save_csv(PATH_COLAB_ATIV, colab_ativ)
                    st.success("Vínculo atualizado.")
            with col_b:
                if st.button("Excluir vínculo"):
                    colab_ativ = colab_ativ[colab_ativ["id"] != vinc_id]
                    save_csv(PATH_COLAB_ATIV, colab_ativ)
                    st.success("Vínculo excluído.")

# ---------------------------
# Tela: Micro-áreas & Atividades
# ---------------------------
def tela_microareas_atividades():
    st.header("Cadastro de Micro-áreas e Atividades")

    microareas = get_microareas()
    atividades = get_atividades()
    colabs = get_colaboradores()

    # Botão de seed padrão
    if st.button("Carregar lista padrão de micro-áreas e atividades"):
        microareas, atividades = seed_default_microareas_atividades(microareas, atividades)
        st.success("Lista padrão carregada/atualizada com sucesso!")

    tab_micro, tab_ativ = st.tabs(["Micro-áreas", "Atividades"])

    # ---------------- Micro-áreas ----------------
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

        # Editar / excluir micro-área
        st.subheader("Editar / excluir micro-área")
        if not microareas.empty:
            nomes_micro = microareas["nome"].tolist()
            sel_micro = st.selectbox("Selecione uma micro-área", options=[""] + nomes_micro)
            if sel_micro:
                row = microareas[microareas["nome"] == sel_micro].iloc[0]
                novo_nome = st.text_input("Nome da micro-área", value=row["nome"], key="edit_micro_nome")
                nova_desc = st.text_area("Descrição", value=row["descricao"] if row["descricao"] else "", key="edit_micro_desc")

                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("Salvar alterações da micro-área"):
                        old_name = row["nome"]
                        microareas.loc[microareas["id"] == row["id"], "nome"] = novo_nome
                        microareas.loc[microareas["id"] == row["id"], "descricao"] = nova_desc
                        save_csv(PATH_MICRO, microareas)

                        # atualiza referências em atividades, colaboradores e vínculos
                        atividades = get_atividades()
                        atividades.loc[atividades["microarea"] == old_name, "microarea"] = novo_nome
                        save_csv(PATH_ATIV, atividades)

                        colabs = get_colaboradores()
                        colabs.loc[colabs["microarea_principal"] == old_name, "microarea_principal"] = novo_nome
                        save_csv(PATH_COLAB, colabs)

                        colab_ativ = get_colab_atividades()
                        colab_ativ.loc[colab_ativ["microarea"] == old_name, "microarea"] = novo_nome
                        save_csv(PATH_COLAB_ATIV, colab_ativ)

                        st.success("Micro-área atualizada.")
                with col_b:
                    if st.button("Excluir micro-área"):
                        # ATENÇÃO: aqui apenas excluímos a microárea;
                        # atividades ainda podem referenciar essa microárea.
                        microareas = microareas[microareas["id"] != row["id"]]
                        save_csv(PATH_MICRO, microareas)
                        st.success("Micro-área excluída. Verifique atividades associadas.")

    # ---------------- Atividades ----------------
    with tab_ativ:
        st.subheader("Nova atividade (tempo em minutos)")

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

            min_por_unidade = st.number_input(
                "Tempo por execução da atividade (minutos)",
                min_value=0.0, step=5.0, value=60.0
            )
            fator_por_projeto = st.number_input(
                "Fator por projeto (quantas execuções dessa atividade por projeto)",
                min_value=0.0, step=0.1, value=1.0
            )
            submitted_ativ = st.form_submit_button("Salvar atividade")

            if submitted_ativ:
                if not nome_ativ or not micro:
                    st.error("Informe pelo menos nome da atividade e micro-área.")
                else:
                    hh_por_unidade = min_por_unidade / 60.0  # converte minutos -> horas
                    new = {
                        "id": new_id(atividades),
                        "nome": nome_ativ,
                        "microarea": micro,
                        "categoria": categoria,
                        "responsavel_funcao": responsavel_funcao,
                        "hh_por_unidade": hh_por_unidade,
                        "fator_por_projeto": fator_por_projeto
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
            df_show = atividades.copy()
            df_show["min_por_unidade"] = (df_show["hh_por_unidade"].fillna(0) * 60).round(1)
            st.dataframe(df_show, use_container_width=True)

        # Editar / excluir atividade
        st.subheader("Editar / excluir atividade")
        if not atividades.empty:
            nomes_ativ = atividades["nome"].tolist()
            sel_ativ = st.selectbox("Selecione uma atividade", options=[""] + nomes_ativ)
            if sel_ativ:
                row = atividades[atividades["nome"] == sel_ativ].iloc[0]
                col1, col2 = st.columns(2)
                with col1:
                    novo_nome = st.text_input("Nome da atividade", value=row["nome"], key="edit_ativ_nome")
                    micro = st.selectbox(
                        "Micro-área",
                        options=microareas["nome"].tolist(),
                        index=microareas["nome"].tolist().index(row["microarea"]) if row["microarea"] in microareas["nome"].tolist() else 0,
                        key="edit_ativ_micro"
                    )
                    categoria = st.text_input(
                        "Categoria",
                        value=row["categoria"] if row["categoria"] else "",
                        key="edit_ativ_cat"
                    )
                with col2:
                    responsavel_funcao = st.selectbox(
                        "Responsável pela função",
                        options=[""] + colabs["nome"].tolist(),
                        index=([""] + colabs["nome"].tolist()).index(row["responsavel_funcao"]) if row["responsavel_funcao"] in colabs["nome"].tolist() else 0,
                        key="edit_ativ_resp"
                    )
                    min_por_unidade_edit = st.number_input(
                        "Tempo por execução (minutos)",
                        min_value=0.0,
                        step=5.0,
                        value=float(row["hh_por_unidade"]) * 60.0 if not pd.isna(row["hh_por_unidade"]) else 60.0,
                        key="edit_ativ_min"
                    )
                    fator_por_projeto = st.number_input(
                        "Fator por projeto",
                        min_value=0.0,
                        step=0.1,
                        value=float(row["fator_por_projeto"]) if not pd.isna(row["fator_por_projeto"]) else 1.0,
                        key="edit_ativ_fator"
                    )

                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("Salvar alterações da atividade"):
                        atividades = get_atividades()
                        hh_por_unidade_edit = min_por_unidade_edit / 60.0
                        atividades.loc[atividades["id"] == row["id"], "nome"] = novo_nome
                        atividades.loc[atividades["id"] == row["id"], "microarea"] = micro
                        atividades.loc[atividades["id"] == row["id"], "categoria"] = categoria
                        atividades.loc[atividades["id"] == row["id"], "responsavel_funcao"] = responsavel_funcao
                        atividades.loc[atividades["id"] == row["id"], "hh_por_unidade"] = hh_por_unidade_edit
                        atividades.loc[atividades["id"] == row["id"], "fator_por_projeto"] = fator_por_projeto
                        save_csv(PATH_ATIV, atividades)
                        st.success("Atividade atualizada.")
                with col_b:
                    if st.button("Excluir atividade"):
                        # remove demandas e vínculos associados
                        demandas = get_demandas()
                        demandas = demandas[demandas["atividade_id"] != row["id"]]
                        save_csv(PATH_DEM, demandas)

                        colab_ativ = get_colab_atividades()
                        colab_ativ = colab_ativ[colab_ativ["atividade_id"] != row["id"]]
                        save_csv(PATH_COLAB_ATIV, colab_ativ)

                        atividades = get_atividades()
                        atividades = atividades[atividades["id"] != row["id"]]
                        save_csv(PATH_ATIV, atividades)
                        st.success("Atividade excluída.")

# ---------------------------
# Tela: Demandas
# ---------------------------
def tela_demandas():
    st.header("Cadastro de Demandas")

    atividades = get_atividades()
    demandas = get_demandas()

    if atividades.empty:
        st.warning("Cadastre atividades antes de inserir demanda.")
        return

    st.subheader("Gerar demandas automaticamente a partir do número de projetos")

    with st.form("form_demanda_projetos"):
        periodo = st.text_input("Período (ex.: 2025-11)", value="")
        num_projetos = st.number_input(
            "Quantidade de projetos no período",
            min_value=0.0, step=1.0, value=0.0
        )

        submitted_auto = st.form_submit_button("Gerar demandas para o período")

        if submitted_auto:
            if not periodo:
                st.error("Informe o período.")
            elif num_projetos <= 0:
                st.error("Informe uma quantidade de projetos maior que zero.")
            else:
                # remove demandas existentes do período
                demandas = demandas[demandas["periodo"] != periodo].copy()

                novas_dem = []
                next_id = new_id(demandas)

                for _, row in atividades.iterrows():
                    fator = row["fator_por_projeto"] if not pd.isna(row["fator_por_projeto"]) else 1.0
                    qtd = num_projetos * fator
                    if qtd <= 0:
                        continue
                    novas_dem.append({
                        "id": next_id,
                        "periodo": periodo,
                        "atividade_id": int(row["id"]),
                        "quantidade": qtd
                    })
                    next_id += 1

                if novas_dem:
                    demandas = pd.concat(
                        [demandas, pd.DataFrame(novas_dem)],
                        ignore_index=True
                    )
                    save_csv(PATH_DEM, demandas)
                    st.success("Demandas geradas automaticamente a partir do número de projetos.")

    st.subheader("Demandas cadastradas (todas as atividades)")

    if demandas.empty:
        st.info("Nenhuma demanda cadastrada ainda.")
    else:
        df_show = demandas.merge(
            atividades[["id", "nome", "microarea", "hh_por_unidade"]],
            left_on="atividade_id",
            right_on="id",
            how="left",
            suffixes=("_dem", "_ativ")
        )

        # define id_demanda de forma robusta
        if "id_dem" in df_show.columns:
            df_show.rename(columns={"id_dem": "id_demanda"}, inplace=True)
        elif "id_x" in df_show.columns:
            df_show.rename(columns={"id_x": "id_demanda"}, inplace=True)
        else:
            df_show.rename(columns={"id": "id_demanda"}, inplace=True)

        df_show["hh_total_atividade"] = df_show["quantidade"] * df_show["hh_por_unidade"]
        df_show.rename(columns={"nome": "atividade"}, inplace=True)

        cols = [
            "id_demanda", "periodo", "atividade", "microarea",
            "quantidade", "hh_por_unidade", "hh_total_atividade"
        ]
        cols = [c for c in cols if c in df_show.columns]

        st.dataframe(df_show[cols], use_container_width=True)

    # opção para limpar demandas de um período
    st.subheader("Excluir demandas de um período")
    demandas = get_demandas()
    if not demandas.empty:
        periodos = sorted(demandas["periodo"].dropna().unique().tolist())
        sel_per = st.selectbox("Período para limpar demandas", options=[""] + periodos)
        if sel_per:
            if st.button("Excluir todas as demandas desse período"):
                demandas = demandas[demandas["periodo"] != sel_per]
                save_csv(PATH_DEM, demandas)
                st.success(f"Demandas do período {sel_per} excluídas.")

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

    periodos = sorted(demandas["periodo"].dropna().unique().tolist())
    periodo_sel = st.selectbox("Selecione o período", options=periodos)

    dias_uteis = st.number_input(
        "Dias úteis no período (para cálculo das horas diárias)",
        min_value=15, max_value=31, value=22, step=1
    )

    df_caps = calcular_capacidades(colabs, dias_uteis)
    df_aloc, df_micro = calcular_alocacoes(colabs, microareas, atividades, demandas, colab_ativ, periodo_sel, dias_uteis)

    # Resumo global diário
    st.subheader("Resumo diário global (todos os grupos)")

    if df_micro.empty:
        st.info("Nenhuma demanda para o período selecionado.")
    else:
        hh_mes_total = df_micro["hh_necessarias"].sum()
        hh_dia_necessarias = hh_mes_total / dias_uteis if dias_uteis > 0 else 0

        colabs_ativos = colabs[colabs["ativo"] == "sim"].copy()
        capacidade_dia_atual = colabs_ativos["carga_diaria"].fillna(0).sum()

        colabs_necessarios_8h = hh_dia_necessarias / 8 if hh_dia_necessarias > 0 else 0
        colabs_atuais_equiv_8h = capacidade_dia_atual / 8 if capacidade_dia_atual > 0 else 0
        gap_colabs_8h = colabs_necessarios_8h - colabs_atuais_equiv_8h

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Horas diárias necessárias", f"{hh_dia_necessarias:.2f} h/dia")
            st.metric("Colaboradores 8h necessários", f"{colabs_necessarios_8h:.2f}")
        with col2:
            st.metric("Capacidade diária atual", f"{capacidade_dia_atual:.2f} h/dia")
            st.metric("Colaboradores 8h equivalentes atuais", f"{colabs_atuais_equiv_8h:.2f}")

        st.markdown(
            f"**Gap de colaboradores (equivalente a 8h/dia):** "
            f"{gap_colabs_8h:.2f}  (positivo = falta gente, negativo = sobra capacidade)"
        )

    st.markdown("---")

    # Micro-áreas
    st.subheader("Demanda x Capacidade por Micro-área (mensal)")

    if df_micro.empty:
        st.info("Nenhuma demanda para o período selecionado.")
    else:
        st.dataframe(df_micro, use_container_width=True)
        data_chart = df_micro.set_index("microarea")[["hh_necessarias", "capacidade_mensal"]]
        if not data_chart.empty:
            st.bar_chart(data_chart)

    # Colaboradores
    st.subheader("Utilização por colaborador (mensal)")

    df_col = df_caps.merge(
        df_aloc,
        left_on="id",
        right_on="id_colaborador",
        how="left"
    )
    df_col["hh_alocadas"] = df_col["hh_alocadas"].fillna(0.0)
    df_col["utilizacao_%"] = (
        df_col["hh_alocadas"] / df_col["capacidade_mensal"].replace(0, pd.NA)
    ) * 100
    df_col["utilizacao_%"] = df_col["utilizacao_%"].round(1)

    df_col_show = df_col[[
        "nome", "cargo", "microarea_principal",
        "capacidade_diaria", "capacidade_mensal", "hh_alocadas", "utilizacao_%"
    ]].sort_values("utilizacao_%", ascending=False)

    st.dataframe(df_col_show, use_container_width=True)

    # Déficit por micro-área
    st.subheader("Necessidade de capacidade adicional por Micro-área (mensal)")

    if not df_micro.empty:
        df_deficit = df_micro[df_micro["saldo"] < 0].copy()
        if df_deficit.empty:
            st.success("Não há déficit de capacidade nas micro-áreas para o período selecionado.")
        else:
            df_deficit["faltam_horas"] = -df_deficit["saldo"]
            df_deficit["equiv_funcionarios"] = (df_deficit["faltam_horas"] / (8 * dias_uteis)).round(2)
            df_deficit["equiv_estagiarios"] = (df_deficit["faltam_horas"] / (6 * dias_uteis)).round(2)
            st.dataframe(
                df_deficit[[
                    "microarea", "hh_necessarias", "capacidade_mensal",
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
