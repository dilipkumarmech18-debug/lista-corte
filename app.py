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
    lines = [l for l in content.splitlines() if l.strip()]

    # Auto-detect header row (contains MARCA)
    header_idx = None
    headers = []
    for i, line in enumerate(lines):
        cols = [c.strip() for c in line.split(';')]
        if any('MARCA' in c.upper() for c in cols):
            # Use this line as header — clean up column names
            headers = []
            for c in cols:
                c = c.strip()
                if 'CONJUNTO' in c.upper() or ('MARCA' in c.upper() and len(headers) > 0):
                    headers.append('CONJUNTO')
                elif 'MARCA' in c.upper():
                    headers.append('MARCA')
                elif 'QTD' in c.upper():
                    headers.append('QTD')
                elif 'MATERIAL' in c.upper():
                    headers.append('MATERIAL')
                elif 'ESPESSURA' in c.upper():
                    headers.append('ESPESSURA')
                elif 'ALTURA' in c.upper():
                    headers.append('ALTURA')
                elif 'COMPRIMENTO' in c.upper():
                    headers.append('COMPRIMENTO')
                else:
                    headers.append(c if c else f'COL{len(headers)}')
            header_idx = i
            break

    if header_idx is None or not headers:
        return pd.DataFrame()

    rows = []
    for line in lines[header_idx + 1:]:
        cols = [c.strip() for c in line.split(';')]

        # Skip separator lines and section headers
        if re.match(r'^-{3,}', cols[0]):
            continue
        if not cols[0]:
            continue

        row = {}
        for j, h in enumerate(headers):
            val = cols[j].strip() if j < len(cols) else ''
            if h in ('QTD', 'ESPESSURA', 'ALTURA', 'COMPRIMENTO'):
                row[h] = int(val) if val.isdigit() else None
            else:
                row[h] = val

        # Must have MARCA and valid QTD
        if not row.get('MARCA') or row.get('QTD') is None:
            continue

        rows.append(row)

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
    filtered = df.copy()

    filter_cols = st.columns(5)
    filter_idx = 0
    active_filters = {}

    text_filter_cols = ['MATERIAL', 'MARCA', 'CONJUNTO']
    for col_name in text_filter_cols:
        if col_name in df.columns and filter_idx < 4:
            vals = ['Todos'] + sorted(df[col_name].dropna().unique().tolist())
            sel = filter_cols[filter_idx].selectbox(col_name.capitalize(), vals)
            active_filters[col_name] = sel
            filter_idx += 1

    if 'ESPESSURA' in df.columns and filter_idx < 4:
        esp_vals = sorted(df['ESPESSURA'].dropna().unique().tolist())
        esp_sel = filter_cols[filter_idx].multiselect("Espessura (mm)", esp_vals)
        filter_idx += 1
    else:
        esp_sel = []

    search = filter_cols[4].text_input("🔍 Pesquisa livre")

    for col_name, sel in active_filters.items():
        if sel != 'Todos':
            filtered = filtered[filtered[col_name] == sel]
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
