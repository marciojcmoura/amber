"""
amber/utils/model.py
────────────────────
Funções núcleo do modelo matemático AMBER v2.1.
Idêntico à Célula 3 da versão Spyder — sem dependências de GUI.

Modelo:
  Prior:     R(T_MISSION) ~ Beta(α₀, β₀)
  Para cada observação i = (t_obs_i, is_failure_i):
    k_i = min( (t_obs_i / T_MISSION)^β_W , 1.0 )
    Censurado → α_p += k_i
    Falhou    → β_p += k_i
  Posterior: Beta(α₀ + Σk_i[cens], β₀ + Σk_j[falha])
"""
from __future__ import annotations

import numpy as np
from scipy.stats import beta as beta_dist

# Critérios fixos do projeto (não editáveis pelo usuário)
R_TARGET: float = 0.90
P_TARGET: float = 0.80

# Opções de β_W disponíveis na interface
BETA_W_OPTS: dict[str, float] = {
    "exponential": 1.0,   # taxa de falha constante
    "fatigue":     2.0,   # fadiga — modo dominante DHSV-i / HEX-WAB
    "wear":        3.5,   # desgaste no fim de vida
}

BETA_W_LABELS: dict[str, str] = {
    "exponential": "Exponencial  β = 1.0",
    "fatigue":     "Fadiga  β = 2.0  ★",
    "wear":        "Desgaste  β = 3.5",
}


def compute_posterior(
    alpha0:       float,
    beta0:        float,
    t_mission:    float,
    beta_w:       float,
    observations: list[tuple[float, bool]],
) -> tuple[float, float, list[float], int, int]:
    """
    Calcula os parâmetros do posterior Beta v2.1.

    Parâmetros
    ----------
    alpha0       : α do prior
    beta0        : β do prior
    t_mission    : tempo de missão alvo (anos)
    beta_w       : forma Weibull do modo de falha dominante
    observations : lista de (t_obs_i, is_failure_i)

    Retorna
    -------
    alpha_p, beta_p, k_list, n_surv, n_fail
    """
    alpha_p: float       = alpha0
    beta_p:  float       = beta0
    k_list:  list[float] = []
    n_surv:  int         = 0
    n_fail:  int         = 0

    for t_obs_i, is_failure in observations:
        # Fator de eficiência informacional — limitado a 1.0
        k_i = min((t_obs_i / t_mission) ** beta_w, 1.0)
        k_list.append(k_i)
        if is_failure:
            beta_p  += k_i   # evidência contra R alto → aumenta β
            n_fail  += 1
        else:
            alpha_p += k_i   # evidência a favor de R alto → aumenta α
            n_surv  += 1

    return alpha_p, beta_p, k_list, n_surv, n_fail


def metricas_beta(alpha: float, beta: float) -> tuple[float, float, float]:
    """Retorna (E[R], σ, P[R ≥ R_TARGET]) de Beta(alpha, beta)."""
    mean   = alpha / (alpha + beta)
    var    = alpha * beta / ((alpha + beta) ** 2 * (alpha + beta + 1))
    p_abov = 1.0 - beta_dist.cdf(R_TARGET, alpha, beta)
    return mean, var ** 0.5, p_abov


def full_analysis(params: dict) -> dict:
    """
    Executa o modelo completo a partir de um dict de parâmetros
    (extraído do request POST do Django) e retorna todos os resultados.

    Parâmetros esperados em params:
      alpha0, beta0, t_mission, beta_w_key, mode,
      n (Modo 1), t_obs_single (Modo 1),
      observations (Modo 2): lista de (t_obs_i, is_failure_i)
    """
    alpha0    = float(params.get('alpha0',    45.67))
    beta0     = float(params.get('beta0',      4.52))
    t_mission = float(params.get('t_mission', 27.0))
    bw_key    = params.get('beta_w_key', 'fatigue')
    beta_w    = BETA_W_OPTS.get(bw_key, 2.0)
    mode      = int(params.get('mode', 1))

    # Monta lista de observações
    if mode == 1:
        n         = int(params.get('n', 0))
        t_obs_s   = float(params.get('t_obs_single', 1.0))
        obs: list[tuple[float, bool]] = [(t_obs_s, False)] * n
    else:
        obs = params.get('observations', [])
        # obs já deve ser list[(float, bool)] — ver views.py

    # Cálculo
    a_p, b_p, k_list, n_surv, n_fail = compute_posterior(
        alpha0, beta0, t_mission, beta_w, obs
    )
    mu_pr, sig_pr, p_pr = metricas_beta(alpha0, beta0)
    mu_po, sig_po, p_po = metricas_beta(a_p,    b_p)

    sum_k_surv = sum(k for k, (_, f) in zip(k_list, obs) if not f)
    sum_k_fail = sum(k for k, (_, f) in zip(k_list, obs) if f)

    return {
        # Prior
        'alpha0': alpha0, 'beta0': beta0,
        'mu_prior': round(mu_pr, 4), 'sig_prior': round(sig_pr, 4),
        'p_prior':  round(p_pr, 4),
        # Modelo
        't_mission': t_mission, 'beta_w': beta_w, 'bw_key': bw_key,
        # Observações
        'mode': mode, 'n_obs': len(obs),
        'n_surv': n_surv, 'n_fail': n_fail,
        'sum_k_surv': round(sum_k_surv, 5),
        'sum_k_fail': round(sum_k_fail, 5),
        # Posterior
        'alpha_p': round(a_p, 4), 'beta_p': round(b_p, 4),
        'mu_post':  round(mu_po, 4), 'sig_post': round(sig_po, 4),
        'p_post':   round(p_po, 4),
        'met': p_po >= P_TARGET,
        # Internos
        '_obs': obs, '_k_list': k_list,
    }
