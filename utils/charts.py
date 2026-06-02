"""
utils/charts.py  (versão Streamlit)
─────────────────────────────────────
Gera a figura Matplotlib para exibição via st.pyplot().
Diferença em relação à versão Django:
  - retorna o objeto fig diretamente (não base64)
  - também exporta render_chart_b64() para uso no exportador PowerPoint
"""
from __future__ import annotations

import base64
import io

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from scipy.stats import beta as beta_dist

from .model import R_TARGET

C_AMBER = '#EF9F27'; C_BLUE  = '#378ADD'; C_DARK  = '#2c2c2a'
C_GRAY  = '#73726c'; C_LINE  = '#D3D1C7'; C_THR   = '#854F0B'
C_PRIOR = '#B4B2A9'; C_BG    = '#FFFFFF'
A800    = '#633806'; B800    = '#0C447C'


def _build_fig(result: dict, width: float, height: float) -> plt.Figure:
    a0, b0 = result['alpha0'], result['beta0']
    a_p, b_p = result['alpha_p'], result['beta_p']
    p_post, mu_po = result['p_post'], result['mu_post']
    n_surv, n_fail = result['n_surv'], result['n_fail']
    beta_w, tm = result['beta_w'], result['t_mission']

    R = np.linspace(0.001, 0.999, 900)
    pdf_pr = np.nan_to_num(beta_dist.pdf(R, a0,  b0),  nan=0, posinf=0)
    pdf_po = np.nan_to_num(beta_dist.pdf(R, a_p, b_p), nan=0, posinf=0)
    ymax = max(pdf_pr.max(), pdf_po.max()) * 1.14
    if not np.isfinite(ymax) or ymax <= 0: ymax = 5.0

    fig, ax = plt.subplots(figsize=(width, height))
    fig.patch.set_facecolor(C_BG); ax.set_facecolor('white')

    ml, mr = R <= R_TARGET, R >= R_TARGET
    ax.plot(R, pdf_pr, color=C_PRIOR, lw=1.5, ls='--', alpha=0.70)
    ax.fill_between(R[ml], pdf_po[ml], alpha=0.38, color=C_AMBER)
    ax.fill_between(R[mr], pdf_po[mr], alpha=0.28, color=C_BLUE)

    lbl = (f"Posterior  (↑{n_surv} cens."
           + (f", ✗{n_fail} falha{'s' if n_fail!=1 else ''}" if n_fail else "")
           + f",  β={beta_w:.1f},  T={tm:.1f}a)")
    ax.plot(R, pdf_po, color=C_DARK, lw=2.0, label=lbl)
    ax.axvline(R_TARGET, color=C_THR,  lw=1.6, ls='--')
    ax.axvline(mu_po,    color=C_GRAY, lw=1.0, ls=':')

    y_top = ymax * 0.965
    ax.text(R_TARGET-0.01, y_top, f'R* = {R_TARGET:.2f}',
            ha='right', va='top', fontsize=10.5, color=C_THR, fontweight='500')
    ax.text(mu_po+0.01,    y_top, f'E[R] = {mu_po:.3f}',
            ha='left',  va='top', fontsize=10.5, color=C_GRAY)

    p_below = 1 - p_post
    for mask, val, tc in [(ml, p_below, A800), (mr, p_post, B800)]:
        sub = mask & (pdf_po > ymax * 0.025)
        if sub.any():
            cx = float(np.average(R[sub], weights=pdf_po[sub]))
            cy = float(beta_dist.pdf(cx, a_p, b_p)) * 0.40
            if np.isfinite(cy) and cy > 0:
                ax.text(cx, cy, f'{val:.2f}', ha='center', va='center',
                        fontsize=13, fontweight='bold', color=tc)

    handles = [
        mpatches.Patch(color=C_PRIOR, alpha=0.8, label=f'Prior  Beta({a0:.1f}, {b0:.1f})'),
        mpatches.Patch(color=C_DARK,  label=lbl),
        mpatches.Patch(color=C_AMBER, alpha=0.6, label=f'P[R < {R_TARGET}]  =  {p_below:.3f}'),
        mpatches.Patch(color=C_BLUE,  alpha=0.5, label=f'P[R ≥ {R_TARGET}]  =  {p_post:.3f}'),
    ]
    ax.legend(handles=handles, fontsize=9.5, loc='upper left',
              framealpha=0.92, edgecolor=C_LINE)
    ax.set_xlabel('R(t)', fontsize=11, color=C_DARK)
    ax.set_ylabel('f [R(t)]', fontsize=11, color=C_DARK)
    ax.set_xlim(0.0, 1.0); ax.set_ylim(0, ymax)
    ax.grid(True, alpha=0.08, lw=0.5)
    for sp in ('top','right'):  ax.spines[sp].set_visible(False)
    for sp in ('left','bottom'): ax.spines[sp].set_color(C_LINE)
    ax.tick_params(colors=C_GRAY, labelsize=10.5)
    fig.tight_layout(pad=1.6)
    return fig


def render_fig(result: dict, width: float = 8.5, height: float = 4.6) -> plt.Figure:
    """Retorna objeto Figure para st.pyplot()."""
    return _build_fig(result, width, height)


def render_chart_b64(result: dict, width: float = 9.0,
                     height: float = 4.8) -> str:
    """Retorna base64 PNG — usado pelo exportador PowerPoint."""
    fig = _build_fig(result, width, height)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor=C_BG)
    buf.seek(0); plt.close(fig)
    return base64.b64encode(buf.read()).decode('utf-8')
