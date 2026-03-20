import streamlit as st
import pandas as pd
import io
import re

st.set_page_config(page_title="Lista de Corte", layout="wide", page_icon="📋")

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .stDataFrame { font-size: 13px; }
    header[data-testid="stHeader"] { background: #1a3c5e; }
</style>
""", unsafe_allow_html=True)

st.title("📋 Lista de Corte por Materiais")
st.markdown("---")


def parse_csv(content: str) -> pd.DataFrame:
    rows = []
    for line in content.splitlines():
        if not line.strip():
            continue
        cols = line.split(';')
        marca      = cols[0].strip() if len(cols) > 0 else ''
        qtd        = cols[1].strip() if len(cols) > 1 else ''
        conjunto   = cols[2].strip() if len(cols) > 2 else ''
        material   = cols[3].strip() if len(cols) > 3 else ''
        espessura  = cols[4].strip() if len(cols) > 4 else ''
        altura     = cols[5].strip() if len(cols) > 5 else ''
        comprimento= cols[6].strip() if len(cols) > 6 else ''

        # Skip separator and header lines
        if re.match(r'^-{3,}', marca):
            continue
        if marca == 'MARCA':
            continue
        if not marca or not qtd or not qtd.isdigit():
            continue

        rows.append({
            'MARCA':       marca,
            'QTD':         int(qtd),
            'CONJUNTO':    conjunto,
            'MATERIAL':    material,
            'ESPESSURA':   int(espessura)   if espessura.isdigit()   else None,
            'ALTURA':      int(altura)      if altura.isdigit()      else None,
            'COMPRIMENTO': int(comprimento) if comprimento.isdigit() else None,
        })
    return pd.DataFrame(rows)


# ── File upload ──────────────────────────────────────────────────────────────
uploaded = st.file_uploader("Carregar ficheiro CSV (Tekla)", type=["csv", "txt"])

if uploaded:
    content = uploaded.read().decode("utf-8", errors="replace")
    df = parse_csv(content)

    if df.empty:
        st.error("Não foram encontrados dados no ficheiro.")
        st.stop()

    st.success(f"✅ {len(df)} linhas carregadas · {df['QTD'].sum()} unidades no total")
    st.markdown("---")

    # ── Filters ──────────────────────────────────────────────────────────────
    st.subheader("🔽 Filtros")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        materiais = ['Todos'] + sorted(df['MATERIAL'].dropna().unique().tolist())
        mat_sel = st.selectbox("Material", materiais)

    with col2:
        marcas = ['Todas'] + sorted(df['MARCA'].dropna().unique().tolist())
        marca_sel = st.selectbox("Marca", marcas)

    with col3:
        conjuntos = ['Todos'] + sorted(df['CONJUNTO'].dropna().unique().tolist())
        conj_sel = st.selectbox("Conjunto", conjuntos)

    with col4:
        esp_vals = sorted(df['ESPESSURA'].dropna().unique().tolist())
        esp_sel = st.multiselect("Espessura (mm)", esp_vals)

    with col5:
        search = st.text_input("🔍 Pesquisa livre")

    # ── Apply filters ─────────────────────────────────────────────────────────
    filtered = df.copy()

    if mat_sel != 'Todos':
        filtered = filtered[filtered['MATERIAL'] == mat_sel]
    if marca_sel != 'Todas':
        filtered = filtered[filtered['MARCA'] == marca_sel]
    if conj_sel != 'Todos':
        filtered = filtered[filtered['CONJUNTO'] == conj_sel]
    if esp_sel:
        filtered = filtered[filtered['ESPESSURA'].isin(esp_sel)]
    if search:
        mask = filtered.astype(str).apply(
            lambda col: col.str.contains(search, case=False, na=False)
        ).any(axis=1)
        filtered = filtered[mask]

    st.markdown("---")

    # ── Column selector ───────────────────────────────────────────────────────
    st.subheader("📊 Dados Filtrados")
    all_cols = df.columns.tolist()
    sel_cols = st.multiselect("Colunas visíveis", all_cols, default=all_cols)
    if not sel_cols:
        sel_cols = all_cols

    display_df = filtered[sel_cols].reset_index(drop=True)

    # Stats
    total_qty = filtered['QTD'].sum() if 'QTD' in filtered.columns else 0
    st.caption(f"**{len(filtered)}** linhas · **{total_qty}** unidades")

    # ── Table ─────────────────────────────────────────────────────────────────
    st.dataframe(
        display_df,
        use_container_width=True,
        height=500,
        column_config={
            "QTD":         st.column_config.NumberColumn("QTD",         format="%d"),
            "ESPESSURA":   st.column_config.NumberColumn("ESPESSURA",   format="%d mm"),
            "ALTURA":      st.column_config.NumberColumn("ALTURA",      format="%d mm"),
            "COMPRIMENTO": st.column_config.NumberColumn("COMPRIMENTO", format="%d mm"),
        }
    )

    st.markdown("---")

    # ── Export ────────────────────────────────────────────────────────────────
    st.subheader("📤 Exportar")
    ecol1, ecol2 = st.columns(2)

    # Export to Excel
    with ecol1:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            display_df.to_excel(writer, index=False, sheet_name='Filtrado')
            # Auto-width columns
            ws = writer.sheets['Filtrado']
            for col_cells in ws.columns:
                max_len = max(len(str(c.value or '')) for c in col_cells)
                ws.column_dimensions[col_cells[0].column_letter].width = min(max_len + 4, 40)
        buf.seek(0)
        st.download_button(
            "⬇️ Exportar Excel (.xlsx)",
            data=buf,
            file_name="lista_filtrada.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    # Export to CSV
    with ecol2:
        csv_bytes = display_df.to_csv(index=False, sep=';').encode('utf-8-sig')
        st.download_button(
            "⬇️ Exportar CSV (.csv)",
            data=csv_bytes,
            file_name="lista_filtrada.csv",
            mime="text/csv",
            use_container_width=True,
        )

    # ── Summary by material ───────────────────────────────────────────────────
    if 'MATERIAL' in filtered.columns and 'QTD' in filtered.columns:
        st.markdown("---")
        st.subheader("📈 Resumo por Material")
        summary = (
            filtered.groupby('MATERIAL')
            .agg(Linhas=('QTD', 'count'), Total_QTD=('QTD', 'sum'))
            .reset_index()
            .rename(columns={'MATERIAL': 'Material'})
        )
        st.dataframe(summary, use_container_width=True, hide_index=True)

else:
    st.info("👆 Carregue um ficheiro CSV para começar.")
    st.markdown("""
    **Formato esperado:** ficheiro CSV com separador `;` exportado do Tekla Structures.

    Colunas: `MARCA · QTD · CONJUNTO · MATERIAL · ESPESSURA · ALTURA · COMPRIMENTO`
    """)
