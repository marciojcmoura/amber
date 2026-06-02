# AMBER v2.1 — Streamlit

**Adaptive Model for Bayesian Estimation of Reliability**  
Ceerma – UFPE  |  Engenharia de Confiabilidade  |  Registro INPI

---

## Rodar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

Acesse `http://localhost:8501` no navegador.

---

## Publicar no site do Ceerma

### Opção 1 — Streamlit Community Cloud (recomendada, gratuita)

1. Suba o projeto para um repositório **GitHub público**:
   ```bash
   git init && git add . && git commit -m "AMBER v2.1"
   git remote add origin https://github.com/ceerma/amber.git
   git push -u origin main
   ```

2. Acesse [share.streamlit.io](https://share.streamlit.io)

3. **"New app"** → selecione o repositório → branch `main` → `app.py`

4. Clique em **Deploy** — URL pública gerada automaticamente:
   `https://ceerma-amber.streamlit.app`

5. No site do Ceerma, adicione um link ou incorpore via `<iframe>`:
   ```html
   <iframe src="https://ceerma-amber.streamlit.app"
           width="100%" height="800px" frameborder="0">
   </iframe>
   ```

### Opção 2 — Servidor próprio (VPS/Docker)

```bash
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```bash
docker build -t amber-app .
docker run -p 8501:8501 amber-app
```

Configure o Nginx para fazer proxy reverso para a porta 8501.

---

## Estrutura do projeto

```
amber_streamlit/
├── app.py                   ← interface principal (único arquivo a editar)
├── requirements.txt
├── .streamlit/
│   └── config.toml          ← tema e configurações
└── utils/
    ├── model.py             ← modelo matemático (idêntico ao Spyder)
    ├── charts.py            ← geração do gráfico f[R(t)]
    ├── excel_helpers.py     ← template e leitura de Excel
    └── pptx_export.py       ← exportação PowerPoint
```

---

## Correspondência com o Spyder v2.1

| Spyder v2.1         | Streamlit                   |
|---------------------|-----------------------------|
| `Célula 3`          | `utils/model.py`            |
| `Célula 4`          | `utils/excel_helpers.py`    |
| `Célula 8 (_draw)`  | `utils/charts.py`           |
| `Célula 9 (_export)`| `utils/pptx_export.py`      |
| `Células 6/7 (UI)`  | `app.py` (sidebar + layout) |
| `tk.Scale`          | `st.slider()`               |
| `ttk.Combobox`      | `st.selectbox()`            |
| `tk.Radiobutton`    | `st.radio()`                |
| `ObservationTable`  | `st.data_editor()`          |
| `_schedule_update`  | automático (Streamlit reroda a cada interação) |
| `_toggle_mode`      | `if mode == 1: / else:`     |
| `filedialog`        | `st.file_uploader()`        |
| `messagebox`        | `st.success()` / `st.error()` |

---

## Modelo matemático

```
Prior:     R(T_MISSION) ~ Beta(α₀, β₀)

Para cada observação i = (t_obs_i, is_failure_i):
  k_i = min( (t_obs_i / T_MISSION)^β_W, 1.0 )
  Censurado → α_p += k_i
  Falhou    → β_p += k_i

Posterior: Beta( α₀ + Σk_i[cens.], β₀ + Σk_j[falhas] )

Critério:  P[R(T_MISSION) ≥ 0.90] ≥ 0.80
```
