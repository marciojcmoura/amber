# -*- coding: utf-8 -*-
"""
app.py  —  AMBER v2.1  |  Streamlit
-------------------------------------
Adaptive Model for Bayesian Estimation of Reliability
Ceerma - UFPE  |  Engenharia de Confiabilidade

Como rodar localmente:
    streamlit run app.py

Como publicar (gratuito):
    1. git push para repositorio publico no GitHub
    2. share.streamlit.io -> New app -> Deploy
"""

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from utils.charts import render_chart_b64, render_fig
from utils.excel_helpers import generate_template, parse_excel
from utils.model import (
    BETA_W_LABELS,
    BETA_W_OPTS,
    P_TARGET,
    R_TARGET,
    full_analysis,
)
from utils.pptx_export import export_pptx

# ─────────────────────────────────────────────────────────────────────────────
# Configuracao da pagina
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AMBER v2.1 — Ceerma-UFPE",
    page_icon=":large_orange_diamond:",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": (
            "**AMBER v2.1** — Adaptive Model for Bayesian Estimation of Reliability\n\n"
            "Ceerma - UFPE  |  Engenharia de Confiabilidade\n\n"
            "Registro INPI — Programa de Computador"
        )
    },
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS personalizado  —  paleta AMBER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
[data-testid="stSidebar"] > div:first-child {
    background: #F1EFE8;
    border-right: 1px solid #D3D1C7;
}
.stButton > button {
    background: #185FA5; color: white; border: none;
    border-radius: 6px; font-weight: 600;
    width: 100%; padding: 10px 0;
}
.stButton > button:hover { background: #0C447C; }
.sec-title {
    font-size: 11px; font-weight: 700; color: #2c2c2a;
    letter-spacing: .5px; text-transform: uppercase;
    margin-bottom: 4px; margin-top: 8px;
}
.status-met  { background:#E6F6F1; border:2px solid #1D9E75;
               border-radius:8px; padding:12px 16px; margin:6px 0; }
.status-fail { background:#FDEEE8; border:2px solid #D85A30;
               border-radius:8px; padding:12px 16px; margin:6px 0; }
.status-val-met  { font-size:22px; font-weight:700; color:#1D9E75; }
.status-val-fail { font-size:22px; font-weight:700; color:#D85A30; }
.status-sub  { font-size:12px; margin-top:3px; }
.formula-box {
    background:#0D2B52; color:white; border-radius:6px;
    padding:10px 14px; font-family:monospace; font-size:13px; margin:6px 0;
}
</style>
""",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# Estado da sessao
# Equivalente as variaveis tk.Var do Spyder
# ─────────────────────────────────────────────────────────────────────────────
if "observations" not in st.session_state:
    # 3 linhas de exemplo para o Modo 2
    st.session_state.observations = [
        {"t_obs": 5.0,  "failure": False},
        {"t_obs": 8.5,  "failure": True},
        {"t_obs": 10.0, "failure": False},
    ]

# ─────────────────────────────────────────────────────────────────────────────
# Cabecalho
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
<div style="background:#185FA5;padding:14px 20px;border-radius:0;
            margin:-1rem -1rem 1rem -1rem;display:flex;align-items:center;gap:14px;">
  <span style="font-size:28px;font-weight:700;color:#EF9F27;letter-spacing:2px;">AMBER</span>
  <div>
    <div style="color:white;font-size:13px;font-weight:500;">
      Adaptive Model for Bayesian Estimation of Reliability &nbsp;&middot;&nbsp; v2.1
    </div>
    <div style="color:rgba(255,255,255,.65);font-size:11px;">
      Ceerma - UFPE &nbsp;&middot;&nbsp; Engenharia de Confiabilidade &nbsp;&middot;&nbsp; Registro INPI
    </div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar  —  painel de controles
# Equivalente a _build_panel() do Spyder
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:

    # ── 1. Prior ─────────────────────────────────────────────────────────────
    st.markdown(
        '<div class="sec-title">Prior  Beta(alfa_0, beta_0)</div>',
        unsafe_allow_html=True,
    )

    alpha0 = st.slider(
        "alfa_0  —  parametro de forma",
        min_value=1.0, max_value=200.0, value=45.67, step=0.5,
        key="alpha0",
        help="Equivale a sucessos acumulados no prior. alfa=45.67 -> E[R]=0.91.",
    )
    beta0 = st.slider(
        "beta_0  —  parametro de escala",
        min_value=1.0, max_value=50.0, value=4.52, step=0.5,
        key="beta0",
        help="Equivale a falhas acumuladas no prior. beta=4.52 -> sigma=0.040.",
    )

    st.divider()

    # ── 2. Modelo ─────────────────────────────────────────────────────────────
    st.markdown(
        '<div class="sec-title">Parametros do Modelo</div>',
        unsafe_allow_html=True,
    )

    t_mission = st.slider(
        "T_MISSION (anos)  —  tempo de missao alvo",
        min_value=1.0, max_value=50.0, value=27.0, step=0.5,
        key="t_mission",
        help="Vida util esperada do equipamento. Define o denominador de k=(t/T)^beta.",
    )

    bw_key = st.selectbox(
        "Modo de falha dominante (beta_W Weibull)",
        options=list(BETA_W_LABELS.keys()),
        format_func=lambda k: BETA_W_LABELS[k],
        index=1,
        key="bw_key",
        help="beta=1.0: exponencial | beta=2.0: fadiga (DHSV-i) | beta=3.5: desgaste",
    )

    st.divider()

    # ── 3. Observacoes ────────────────────────────────────────────────────────
    st.markdown(
        '<div class="sec-title">Observacoes de Campo</div>',
        unsafe_allow_html=True,
    )

    mode = st.radio(
        "Modo de entrada",
        options=[1, 2],
        format_func=lambda m: (
            "Modo 1  —  mesmo t_obs para todos"
            if m == 1
            else "Modo 2  —  t_obs individual"
        ),
        horizontal=True,
        key="mode",
        label_visibility="collapsed",
    )

    # ── Modo 1 ────────────────────────────────────────────────────────────────
    if mode == 1:
        n_units = st.slider(
            "n  —  unidades observadas (todas censuradas)",
            min_value=0, max_value=200, value=0, step=1,
            key="n_mode1",
            help="No Modo 1 todas as unidades sao tratadas como censuradas.",
        )
        t_obs_single = st.slider(
            "t_obs  —  tempo de observacao por unidade (anos)",
            min_value=0.5, max_value=float(t_mission),
            value=min(1.0, float(t_mission)),
            step=0.5,
            key="t_obs_single",
        )
        st.caption(
            "i  Modo 1: todas as n unidades sao censuradas. "
            "Para indicar falhas use o Modo 2."
        )
        observations = [(t_obs_single, False)] * n_units

    # ── Modo 2 ────────────────────────────────────────────────────────────────
    else:
        st.caption("Edite a tabela. Marque 'Falha?' para observacoes com falha.")

        # st.data_editor — equivalente a ObservationTable do Spyder
        obs_df = pd.DataFrame(
            st.session_state.observations,
            columns=["t_obs", "failure"],
        )
        obs_df.columns = ["t_obs (anos)", "Falha?"]

        edited = st.data_editor(
            obs_df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "t_obs (anos)": st.column_config.NumberColumn(
                    "t_obs (anos)",
                    min_value=0.01,
                    max_value=float(t_mission),
                    step=0.5,
                    format="%.2f",
                ),
                "Falha?": st.column_config.CheckboxColumn(
                    "Falha?",
                    default=False,
                ),
            },
            hide_index=False,
            key="obs_editor",
        )

        # Sincroniza session_state com o editor
        st.session_state.observations = [
            {"t_obs": float(row["t_obs (anos)"]), "failure": bool(row["Falha?"])}
            for _, row in edited.iterrows()
            if pd.notna(row["t_obs (anos)"])
        ]
        observations = [
            (o["t_obs"], o["failure"])
            for o in st.session_state.observations
        ]

        # Download template / Upload Excel
        col_dl, col_up = st.columns(2)

        with col_dl:
            tmpl_bytes = generate_template(t_mission)
            st.download_button(
                label="Baixar Template",
                data=tmpl_bytes,
                file_name="AMBER_template.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument"
                    ".spreadsheetml.sheet"
                ),
                use_container_width=True,
            )

        with col_up:
            uploaded = st.file_uploader(
                "Carregar Excel",
                type=["xlsx", "xls"],
                label_visibility="collapsed",
                key="excel_upload",
            )
            if uploaded is not None:
                try:
                    obs_parsed = parse_excel(uploaded.read())
                    st.session_state.observations = [
                        {"t_obs": t, "failure": f} for t, f in obs_parsed
                    ]
                    n_fail_up = sum(1 for _, f in obs_parsed if f)
                    st.success(
                        "{n} obs. carregadas ({c} cens., {f} falhas).".format(
                            n=len(obs_parsed),
                            c=len(obs_parsed)-n_fail_up,
                            f=n_fail_up,
                        )
                    )
                    st.rerun()
                except Exception as exc:
                    st.error("Erro ao ler Excel: " + str(exc))

    st.divider()

    # ── Exportacao — fixo na base da sidebar ─────────────────────────────────
    st.markdown(
        '<div class="sec-title">Exportacao</div>',
        unsafe_allow_html=True,
    )
    export_clicked = st.button(
        "Exportar slide PowerPoint",
        key="btn_export",
        use_container_width=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# Calculo do modelo
# Equivalente a _update() do Spyder — roda automaticamente a cada interacao
# ─────────────────────────────────────────────────────────────────────────────
params = {
    "alpha0":       alpha0,
    "beta0":        beta0,
    "t_mission":    t_mission,
    "beta_w_key":   bw_key,
    "mode":         mode,
    "n":            n_units if mode == 1 else 0,
    "t_obs_single": t_obs_single if mode == 1 else 1.0,
    "observations": observations if mode == 2 else [],
}
result = full_analysis(params)

# ─────────────────────────────────────────────────────────────────────────────
# Area principal: grafico + metricas
# ─────────────────────────────────────────────────────────────────────────────
col_chart, col_metrics = st.columns([3.2, 1.0], gap="medium")

# ── Coluna do grafico ─────────────────────────────────────────────────────────
with col_chart:
    fig = render_fig(result, width=9.0, height=4.8)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

# ── Coluna de metricas ────────────────────────────────────────────────────────
with col_metrics:

    # Status P[R >= R*]
    met = result["met"]
    status_cls  = "status-met"      if met else "status-fail"
    status_vcls = "status-val-met"  if met else "status-val-fail"
    status_sub  = (
        "Alvo atingido  (P >= {})".format(P_TARGET)
        if met
        else "Abaixo do alvo  ({} < {})".format(result["p_post"], P_TARGET)
    )
    checkmark = "V" if met else "X"

    st.markdown(
        """
<div class="{cls}">
  <div class="{vcls}">{chk}  P[R >= {rt}]  =  {val}</div>
  <div class="status-sub">{sub}</div>
</div>
""".format(
            cls=status_cls, vcls=status_vcls,
            chk=checkmark, rt=R_TARGET,
            val=result["p_post"], sub=status_sub,
        ),
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Formula do posterior
    st.markdown(
        """
<div class="formula-box">
  Beta(a0+Sk_cens, b0+Sk_falha)<br>
  <small style="color:#B5D4F4;">
    k = (t_obs / {tm:.1f})^{bw:.1f}
  </small>
</div>
""".format(tm=t_mission, bw=BETA_W_OPTS[bw_key]),
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Prior ─────────────────────────────────────────────────────────────────
    st.markdown('<div class="sec-title">Prior</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    c1.metric("alfa_0", "{:.1f}".format(alpha0))
    c2.metric("beta_0", "{:.1f}".format(beta0))
    c1.metric("E[R]|prior",    "{}".format(result["mu_prior"]))
    c2.metric("sigma|prior",   "{}".format(result["sig_prior"]))

    p_pr = result["p_prior"]
    icon = ":green_circle:" if p_pr >= P_TARGET else (":yellow_circle:" if p_pr >= 0.4 else ":red_circle:")
    st.metric("{} P[R>=R*]|prior".format(icon), "{}".format(p_pr))

    st.divider()

    # ── Observacoes ───────────────────────────────────────────────────────────
    st.markdown('<div class="sec-title">Observacoes</div>', unsafe_allow_html=True)
    c3, c4 = st.columns(2)
    c3.metric("Total",     result["n_obs"])
    c4.metric("Censuradas", result["n_surv"])
    c3.metric("Falhas",    result["n_fail"])
    c4.metric("Sk cens.",  "{}".format(result["sum_k_surv"]))
    st.metric("Sk falhas", "{}".format(result["sum_k_fail"]))

    st.divider()

    # ── Posterior ─────────────────────────────────────────────────────────────
    st.markdown('<div class="sec-title">Posterior</div>', unsafe_allow_html=True)
    c5, c6 = st.columns(2)
    c5.metric("alfa post.", "{}".format(result["alpha_p"]))
    c6.metric("beta post.", "{}".format(result["beta_p"]))
    c5.metric("E[R(t)]",   "{}".format(result["mu_post"]))
    c6.metric("sigma post.","{}".format(result["sig_post"]))

# ─────────────────────────────────────────────────────────────────────────────
# Exportacao PowerPoint
# Equivalente a _export() do Spyder
# ─────────────────────────────────────────────────────────────────────────────
if export_clicked:
    with st.spinner("Gerando slide..."):
        try:
            chart_b64  = render_chart_b64(result, width=9.0, height=4.8)
            pptx_bytes = export_pptx(result, chart_b64)
            fname = "AMBER_T{:.0f}a_a{:.0f}_b{:.0f}_n{}.pptx".format(
                t_mission, alpha0, beta0, result["n_obs"]
            )
            st.sidebar.download_button(
                label="Clique aqui para baixar o .pptx",
                data=pptx_bytes,
                file_name=fname,
                mime=(
                    "application/vnd.openxmlformats-officedocument"
                    ".presentationml.presentation"
                ),
                use_container_width=True,
            )
            st.sidebar.success("Slide gerado! Clique no botao acima para baixar.")
        except ImportError:
            st.sidebar.error("python-pptx nao encontrado. Execute: pip install python-pptx")
        except Exception as exc:
            st.sidebar.error("Erro ao gerar PPTX: " + str(exc))

# ─────────────────────────────────────────────────────────────────────────────
# Rodape
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
<hr style="border:none;border-top:1px solid #D3D1C7;margin:20px 0 8px">
<div style="text-align:center;font-size:11px;color:#B4B2A9;">
  <b>AMBER v2.1</b> &nbsp;&middot;&nbsp;
  Adaptive Model for Bayesian Estimation of Reliability &nbsp;&middot;&nbsp;
  Ceerma - UFPE &nbsp;&middot;&nbsp; Departamento de Engenharia de Producao
  &nbsp;&middot;&nbsp; Registro INPI
</div>
""",
    unsafe_allow_html=True,
)
