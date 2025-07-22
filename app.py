import os
import streamlit as st
import pandas as pd
import altair as alt

# ─── Resolve paths relative to this script’s folder ───
BASE = os.path.dirname(__file__)
QCSV = os.path.join(BASE, "data", "GEBV_quality_global_16traits_10k_FIN.csv")
ACSV = os.path.join(BASE, "data", "GEBVs_global_13_agronomic_traits_avg.csv")

# ─── 1) App title ─────────────────────────────────────
st.title("🧬 GEBV Explorer for the Capsicum Global Collection 🌍")

# ─── 2) Load and merge data ──────────────────────────
df_q = pd.read_csv(QCSV)   # ← use QCSV here
df_a = pd.read_csv(ACSV)   # ← and ACSV here

if "Group" in df_a.columns and "Group" in df_q.columns:
    df = pd.merge(df_q, df_a, on=["Line", "Group"], how="inner")
else:
    df = pd.merge(df_q, df_a, on="Line", how="inner")

# ─── 3) Sidebar sliders (initialize full range) ──────
trait_cols = [c for c in df.columns if c.startswith("GEBV_")]
st.sidebar.header("Thresholds")
thresholds = {}
for col in trait_cols:
    lo, hi = float(df[col].min()), float(df[col].max())
    thresholds[col] = st.sidebar.slider(
        label=col,
        min_value=lo,
        max_value=hi,
        value=(lo, hi),
        help=f"Select {col} between {lo:.2f} and {hi:.2f}"
    )

# ─── 4) Apply filter ──────────────────────────────────
mask = pd.Series(True, index=df.index)
for col, (lo, hi) in thresholds.items():
    mask &= df[col].between(lo, hi)
filtered = df[mask]

# ─── 5) Display filtered table ───────────────────────
st.write(f"Lines passing all thresholds: **{len(filtered)}**")
st.dataframe(filtered)

# ─── 6) All-lines expander ───────────────────────────
with st.expander("Show all lines (unfiltered)"):
    st.dataframe(df)

# ─── 7) Scatter plot layering ────────────────────────
st.write("---")
st.subheader("Scatter plot of two traits")

default_x = trait_cols.index("GEBV_fruitno_x") if "GEBV_fruitno_x" in trait_cols else 0
default_y = trait_cols.index("GEBV_yield_y") if "GEBV_yield_y" in trait_cols else 1

col1, col2 = st.columns(2)
with col1:
    x_sel = st.selectbox("X-axis trait", trait_cols, index=default_x)
with col2:
    y_sel = st.selectbox("Y-axis trait", trait_cols, index=default_y)

if x_sel and y_sel:
    base = (
        alt.Chart(df)
        .mark_circle(size=60, color="lightgray")
        .encode(
            x=alt.X(x_sel, type="quantitative"),
            y=alt.Y(y_sel, type="quantitative"),
            tooltip=["Line", x_sel, y_sel]
        )
    )
    highlight = (
        alt.Chart(filtered)
        .mark_circle(size=60, color="red")
        .encode(
            x=alt.X(x_sel, type="quantitative"),
            y=alt.Y(y_sel, type="quantitative"),
            tooltip=["Line", x_sel, y_sel]
        )
    )
    st.altair_chart(alt.layer(base, highlight).interactive(),
                    use_container_width=True)

# ─── 8) Download filtered CSV ─────────────────────────
st.write("---")
st.download_button(
    "Download filtered CSV",
    filtered.to_csv(index=False).encode("utf-8"),
    file_name="filtered_lines_combined.csv",
    mime="text/csv",
)
