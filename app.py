"""
BizPack Interactive Web Playground (Streamlit)
Drag-and-drop spreadsheet cleaner, data health auditor, and business analytics engine.
"""

import io
import os
import streamlit as st
import pandas as pd
import bizpack as bp

# Page configuration
st.set_page_config(
    page_title="BizPack Playground | Intelligent Business Data Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern dark-mode aesthetic
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #58A6FF;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #8B949E;
        margin-bottom: 1.2rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
banner_path = os.path.join(os.path.dirname(__file__), "assets", "banner.png")
if os.path.exists(banner_path):
    st.sidebar.image(banner_path, use_container_width=True)
elif os.path.exists("assets/banner.png"):
    st.sidebar.image("assets/banner.png", use_container_width=True)

st.sidebar.title("⚡ BizPack Controls")
st.sidebar.markdown("Zero-friction spreadsheet cleaning + business math for Python.")

target_curr = st.sidebar.selectbox(
    "🌍 Standardize Currencies To:",
    ["USD", "INR", "EUR", "GBP", "CAD", "AUD"],
    index=0,
)

strip_footers = st.sidebar.checkbox("Remove 'Grand Total' summary footers", value=True)
protect_ids = st.sidebar.checkbox("Protect leading zeros on Account/ZIP IDs", value=True)
dayfirst_opt = st.sidebar.selectbox("Date Parsing Preference:", ["Auto (Two-Tier Inference)", "DD/MM/YYYY", "MM/DD/YYYY"])

dayfirst_val = True if dayfirst_opt == "DD/MM/YYYY" else False if dayfirst_opt == "MM/DD/YYYY" else None

st.sidebar.markdown("---")
st.sidebar.markdown("📦 **PyPI:** `pip install bizpack`")
st.sidebar.markdown("⭐ **GitHub:** [sudheer-050/bizpack](https://github.com/sudheer-050/bizpack)")

# Main Header
st.markdown('<div class="main-title">⚡ BizPack Interactive Playground</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Audit messy spreadsheets, standardize mixed currencies, disambiguate dates, and run Excel business formulas in 1 line.</div>', unsafe_allow_html=True)

# File Uploader & Sample Button
col_upload, col_sample = st.columns([3, 1])

with col_upload:
    uploaded_file = st.file_uploader(
        "Upload any messy CSV or Excel file:",
        type=["csv", "tsv", "xlsx"],
        help="Upload files with mixed currencies ($/€/₹), accounting brackets ($1,200), and mixed dates.",
    )

with col_sample:
    st.write("")
    st.write("")
    use_sample = st.button("🧪 Load Sample Dirty Dataset", use_container_width=True)

df_raw = None

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".xlsx"):
            df_raw = pd.read_excel(uploaded_file)
        else:
            df_raw = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Error reading file: {e}")

if df_raw is None:
    # Try local examples directory paths
    sample_candidates = [
        os.path.join(os.path.dirname(__file__), "examples", "dirty_data.csv"),
        os.path.join("examples", "dirty_data.csv"),
        "dirty_data.csv",
    ]
    for p in sample_candidates:
        if os.path.exists(p):
            try:
                df_raw = pd.read_csv(p)
                break
            except Exception:
                pass

if df_raw is None:
    # Bulletproof in-memory fallback dataset so playground NEVER renders empty
    df_raw = pd.DataFrame({
        "Customer Name / Client ": ["Acme Corp", "Wayne Enterprises", "Massive Dynamic", "Acme Corp", "Soylent Corp", "Hooli Inc", "Pied Piper", "Dunder Mifflin", "Cyberdyne Systems", "Grand Total"],
        " Account # ": ["00124", "00235", "00280", "00243", "00945", "00234", "00058", "00612", "00892", ""],
        "Order Date (UTC)": ["25/03/2024", "03/25/2024", "14.12.2024", "22.02.2024", "05/09/2024", "05/09/2024", "15-Mar-2024", "01/02/2024", "01/02/2024", ""],
        "Region / Territory": ["APAC", "USA", "Europe", "Europe", "India", "North America", "APAC", "India", "USA", ""],
        "Gross Revenue": ["₹ 1,49,670.67", "($ 12,865.27)", "£ 5,306.25", "€ 41.392,35", "₹ 1,17,418.70", "$ 59,426.74", "Rs. 45,000.00", "(₹ 19,424.07)", "49457.81", "$ 500,000.00"],
        "Unit Cost": ["₹ 84,078.93", "$ 8,045.42", "£ 3,494.04", "€ 28.353,26", "₹ 76,087.98", "$ 41,967.12", "Rs. 38,250.00", "₹ 11,167.64", "33685.22", "$ 300,000.00"],
        "Profit Margin %": ["33.3%", "(9.8%)", "22.0%", "17.5%", "17.3%", "51.8%", "(15.0%)", "(29.2%)", "7.5%", ""],
        "Active Subscription?": ["false", "true", "Y", "false", "No", "Yes", "Y", "true", "N", ""],
        "Customer Notes / Log": ["Standard order", "Account upgrade pending", "VIP client priority support", "Fast shipping requested", "N/A", "Quarterly renewal", "Customer asked for discount", "-", "null", ""],
        "Blank Column (Notes)": [None, None, None, None, None, None, None, None, None, None],
    })

if df_raw is not None:
    # 1. Clean the dataset immediately with BizPack
    clean_df = bp.clean(
        df_raw,
        target_currency=target_curr,
        totals=strip_footers,
        dayfirst=dayfirst_val,
        prompt_currency=False,
    )

    # 2. Run Health Audits on both
    raw_report = bp.audit(df_raw, print_report=False)
    clean_report = bp.audit(clean_df, print_report=False)
    score_diff = clean_report.score - raw_report.score

    # 3. Prominent Health Upgrade Banner
    st.success(
        f"✨ **BizPack Upgrade Complete:** Dataset Health jumped from "
        f"**{raw_report.score}/100 ({raw_report.rating})** ➔ **{clean_report.score}/100 ({clean_report.rating})** "
        f"(+{score_diff} pts improvement! All currencies standardized to {target_curr}, dates disambiguated, footers removed)."
    )

    # 4. KPI Metrics Bar
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Raw Health (Before)", f"{raw_report.score} / 100", help="Quality score of the raw uncleaned input")
    with m2:
        st.metric("Clean Health (After)", f"{clean_report.score} / 100", delta=f"+{score_diff} pts", help="Quality score after BizPack cleaning")
    with m3:
        st.metric("Records Cleaned", f"{clean_df.shape[0]} rows × {clean_df.shape[1]} cols")
    with m4:
        st.metric("Target Currency", target_curr)

    # 5. Core View Tabs (Cleaned Output is Tab 1, Business Analytics is Tab 2)
    tab_clean, tab_analytics, tab_side, tab_audit = st.tabs([
        "✅ 1. Cleaned Output (After Clean)",
        "📈 2. Business Analytics (Pareto & Growth)",
        "🔄 3. Side-by-Side Comparison",
        "🏥 4. Health Diagnostic Details",
    ])

    with tab_clean:
        st.markdown(f"#### ✅ Cleaned & Standardized DataFrame (`{target_curr}`)")
        st.caption("All mixed currencies standardized, accounting deficits converted to true negatives, leading zero IDs protected, footers removed.")
        
        # Action Bar (Download + Quick Stats)
        dl_col, note_col = st.columns([1, 3])
        with dl_col:
            csv_buf = io.StringIO()
            clean_df.to_csv(csv_buf, index=False)
            st.download_button(
                label="⬇️ Download Cleaned CSV",
                data=csv_buf.getvalue(),
                file_name=f"bizpack_clean_{target_curr.lower()}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with note_col:
            st.info(f"Showing top 25 rows of {len(clean_df)} cleaned records. All types cast to float64, boolean, and ISO date.")

        st.dataframe(clean_df.head(25), use_container_width=True, height=480)

        # Currency Conversion Audit Log
        if "currency_conversions" in clean_df.attrs and clean_df.attrs["currency_conversions"]:
            with st.expander("🌍 Multi-Currency Audit Trail & Exchange Rates Applied", expanded=False):
                for col_name, info in clean_df.attrs["currency_conversions"].items():
                    st.write(f"**Column `{col_name}` standardized to `{info.get('target_currency', target_curr)}`:**")
                    st.write(f"- Currencies detected: `{info.get('detected_currencies', [])}`")
                    rates_used = info.get("effective_rates_to_target", {})
                    if rates_used:
                        st.write(f"- Conversion factors applied: `{rates_used}`")
                    st.write(f"- Rows converted: `{info.get('rows_converted', 0)}` of `{info.get('total_rows', len(clean_df))}`")

    with tab_analytics:
        st.markdown("#### 📈 Instant Pythonic Business Analytics")
        st.caption("Run Pareto 80/20 driver analysis, period growth trends, and boardroom display formatting in 1 line.")
        
        num_cols = clean_df.select_dtypes(include=["number"]).columns.tolist()
        str_cols = clean_df.select_dtypes(include=["object", "string"]).columns.tolist()
        date_cols = [c for c in clean_df.columns if "date" in c.lower() or pd.api.types.is_datetime64_any_dtype(clean_df[c])]
        if not date_cols:
            date_cols = [c for c in clean_df.columns if any(k in c.lower() for k in ["time", "day", "period", "year", "month"])]

        tool_choice = st.radio(
            "Select Analysis Tool:",
            ["📊 Pareto 80/20 Rule", "📅 Period Growth Trends", "👔 Boardroom Display Formatting"],
            horizontal=True,
            key="analytics_tool_choice",
        )

        if tool_choice == "📊 Pareto 80/20 Rule":
            st.markdown("##### 📊 Pareto 80/20 Rule Analysis")
            if str_cols and num_cols:
                p_col1, p_col2 = st.columns(2)
                with p_col1:
                    p_dim = st.selectbox("Dimension (Category):", str_cols, index=0, key="pareto_dim")
                with p_col2:
                    p_metric = st.selectbox("Metric (Value):", num_cols, index=0, key="pareto_metric")
                pareto_df = bp.pareto(clean_df, dim_col=p_dim, metric_col=p_metric, top_pct=0.80)
                st.info(pareto_df.attrs.get("summary", "Pareto calculation complete."))
                
                # Identify top drivers safely
                top_flag = f"is_top_{int(0.80 * 100)}"
                if top_flag in pareto_df.columns and pareto_df[top_flag].any():
                    top_contrib = pareto_df[pareto_df[top_flag]]
                elif "cumulative_share" in pareto_df.columns:
                    top_contrib = pareto_df[pareto_df["cumulative_share"] <= 0.85]
                    if top_contrib.empty:
                        top_contrib = pareto_df.head(5)
                else:
                    top_contrib = pareto_df.head(10)
                
                st.markdown("**Top Contributors Bar Chart:**")
                if not top_contrib.empty and p_dim in top_contrib.columns and p_metric in top_contrib.columns:
                    st.bar_chart(data=top_contrib.set_index(p_dim)[p_metric])
                
                st.markdown("**Full Pareto Calculation Table:**")
                st.dataframe(pareto_df, use_container_width=True)
            else:
                st.write("No numeric or category columns found for Pareto analysis.")

        elif tool_choice == "📅 Period Growth Trends":
            st.markdown("##### 📅 Period-over-Period Growth Analysis")
            if date_cols and num_cols:
                col_g1, col_g2, col_g3 = st.columns(3)
                with col_g1:
                    d_col = st.selectbox("Date Column:", date_cols, index=0, key="growth_date")
                with col_g2:
                    g_metric = st.selectbox("Metric Column:", num_cols, index=0, key="growth_metric")
                with col_g3:
                    freq_choice = st.selectbox("Frequency:", ["Monthly (M)", "Quarterly (Q)", "Yearly (Y)"], index=0, key="growth_freq")
                    freq_code = "M" if "Monthly" in freq_choice else "Q" if "Quarterly" in freq_choice else "Y"
                try:
                    growth_df = bp.growth(clean_df, date_col=d_col, metric_col=g_metric, freq=freq_code)
                    if f"current_{g_metric}" in growth_df.columns and "period" in growth_df.columns and not growth_df.empty:
                        st.markdown(f"**{freq_choice.split()[0]} {g_metric} Trend:**")
                        st.line_chart(data=growth_df.set_index("period")[f"current_{g_metric}"])
                    st.markdown("**Period Growth Summary Table:**")
                    st.dataframe(growth_df, use_container_width=True)
                except Exception as e:
                    st.warning(f"Could not calculate growth: {e}")
            else:
                st.write("Ensure your dataset has at least one date column for growth trends.")

        elif tool_choice == "👔 Boardroom Display Formatting":
            st.markdown("##### 👔 Boardroom Display Formatting")
            st.write("Convert calculation floats back into boardroom-ready formatted strings (`$`, `₹`, `€`, `%`, `()`):")
            try:
                display_df = bp.format_for_display(clean_df)
                st.dataframe(display_df.head(25), use_container_width=True)
            except Exception as e:
                st.dataframe(clean_df.head(25), use_container_width=True)

    with tab_side:
        st.markdown("#### 🔄 Side-by-Side Direct Comparison")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.markdown("**❌ Before: Raw Dirty Input**")
            st.dataframe(df_raw.head(20), use_container_width=True, height=450)
        with col_s2:
            st.markdown(f"**✅ After: Cleaned ({target_curr})**")
            st.dataframe(clean_df.head(20), use_container_width=True, height=450)

    with tab_audit:
        st.markdown("#### 🏥 Pre-Cleaning Health Diagnostic Scorecard")
        st.caption("Detailed breakdown of issues detected in the raw input file:")
        
        if raw_report.issues:
            for issue in raw_report.issues:
                icon = "🚨" if issue["severity"] == "HIGH" else "⚠️" if issue["severity"] == "MEDIUM" else "ℹ️"
                st.write(f"{icon} **[{issue['severity']}] {issue['column']}**: {issue['message']}")
        else:
            st.success("🎉 No data defects detected in input.")
        st.warning(f"**Diagnostic Summary:** {raw_report.recommendation}")
