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
        font-size: 2.4rem;
        font-weight: 700;
        color: #58A6FF;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #8B949E;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    .badge {
        display: inline-block;
        padding: 0.25em 0.6em;
        font-size: 80%;
        font-weight: 700;
        border-radius: 4px;
        color: #fff;
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
    "🌍 Target Currency for Standardization:",
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
elif use_sample or df_raw is None:
    sample_path = os.path.join(os.path.dirname(__file__), "examples", "dirty_data.csv")
    if not os.path.exists(sample_path):
        sample_path = os.path.join("examples", "dirty_data.csv")
    if os.path.exists(sample_path):
        df_raw = bp.read_csv(sample_path, clean=False)
        st.info("Loaded realistic 100-row sample dataset containing mixed currencies (₹, $, €, £), two-tier dates, accounting brackets, and empty columns.")

if df_raw is not None:
    # 1. Health Audit Section
    st.markdown("### 🏥 1. Pre-Cleaning Health Diagnostic (Raw Input File)")
    st.caption("Diagnosing hidden defects, multi-currency conflicts, and date ambiguities in the raw input file:")
    report = bp.audit(df_raw, print_report=False)
    
    score_col, status_col, rows_col, comp_col = st.columns(4)
    with score_col:
        st.metric("Raw Health Score", f"{report.score} / 100")
    with status_col:
        rating_color = "🔴" if report.score < 50 else "🟡" if report.score < 80 else "🟢"
        st.metric("Raw Status Rating", f"{rating_color} {report.rating}")
    with rows_col:
        st.metric("Records Analyzed", f"{report.stats['rows']} rows × {report.stats['cols']} cols")
    with comp_col:
        st.metric("Data Completeness", f"{report.stats['completeness_pct']:.1f}%")

    with st.expander(f"🔍 View {len(report.issues)} Issue(s) Detected in Raw Input", expanded=(report.score < 80)):
        st.warning(f"**Diagnostic Summary:** {report.recommendation}")
        for issue in report.issues:
            icon = "🚨" if issue["severity"] == "HIGH" else "⚠️" if issue["severity"] == "MEDIUM" else "ℹ️"
            st.write(f"{icon} **[{issue['severity']}] {issue['column']}**: {issue['message']}")

    # 2. Perform BizPack cleaning
    clean_df = bp.clean(
        df_raw,
        target_currency=target_curr,
        totals=strip_footers,
        dayfirst=dayfirst_val,
        prompt_currency=False,
    )

    clean_report = bp.audit(clean_df, print_report=False)

    # 3. Side-by-Side Comparison
    st.markdown("---")
    st.markdown("### 🔄 2. Transformation: Raw Input vs. Pristine BizPack Output")

    # Health Improvement Banner
    score_diff = clean_report.score - report.score
    st.success(f"✨ **BizPack Health Upgrade:** Dataset health jumped from **{report.score}/100 ({report.rating})** ➔ **{clean_report.score}/100 ({clean_report.rating})** (+{score_diff} pts improvement)!")

    col_raw, col_clean = st.columns(2)

    with col_raw:
        st.subheader("❌ Before: Raw Dirty Spreadsheet")
        st.caption(f"Health: {report.score}/100 ({report.rating}) • Contains string currencies, mixed dates, empty columns.")
        st.dataframe(df_raw.head(10), use_container_width=True, height=350)

    with col_clean:
        st.subheader(f"✅ After: Cleaned ({target_curr})")
        st.caption(f"Health: {clean_report.score}/100 ({clean_report.rating}) • Standardized to {target_curr}, types cast, zero NaT rows.")
        st.dataframe(clean_df.head(10), use_container_width=True, height=350)

    # 3. Currency Audit Trail Expander
    if "currency_conversions" in clean_df.attrs and clean_df.attrs["currency_conversions"]:
        with st.expander("🌍 Multi-Currency Audit Trail & Conversion Transparency", expanded=True):
            conv_data = clean_df.attrs["currency_conversions"]
            for col_name, info in conv_data.items():
                st.write(f"**Column `{col_name}` converted to `{info['target_currency']}`:**")
                st.write(f"- Currencies standardized: `{dict(info['counts'])}`")
                st.write(f"- Conversion rates applied: `{info['rates_applied']}`")

    # 4. Business Analytics Section (Pareto & Growth)
    st.markdown("---")
    st.markdown("### 📈 3. Instant Pythonic Business Analytics")

    num_cols = clean_df.select_dtypes(include=["number"]).columns.tolist()
    str_cols = clean_df.select_dtypes(include=["object", "string"]).columns.tolist()
    date_cols = [c for c in clean_df.columns if "date" in c.lower()]

    tab1, tab2, tab3 = st.tabs(["📊 Pareto (80/20 Rule)", "📅 Period Growth", "👔 Boardroom Display"])

    with tab1:
        if str_cols and num_cols:
            p_dim = st.selectbox("Dimension (Category):", str_cols, index=0)
            p_metric = st.selectbox("Metric (Value):", num_cols, index=0)
            
            pareto_df = bp.pareto(clean_df, dim_col=p_dim, metric_col=p_metric, top_pct=0.80)
            st.info(pareto_df.attrs.get("summary", "Pareto calculation complete."))
            
            # Bar chart of top contributors
            top_contributors = pareto_df[pareto_df["cumulative_pct"] <= 0.85]
            st.bar_chart(data=top_contributors.set_index(p_dim)[p_metric])
        else:
            st.write("No numeric or category columns found for Pareto analysis.")

    with tab2:
        if date_cols and num_cols:
            d_col = date_cols[0]
            g_metric = num_cols[0]
            try:
                growth_df = bp.growth(clean_df, date_col=d_col, metric_col=g_metric, freq="M")
                st.dataframe(growth_df, use_container_width=True)
            except Exception as e:
                st.write(f"Could not calculate growth: {e}")
        else:
            st.write("Ensure your dataset has at least one date column for growth trends.")

    with tab3:
        st.write("Convert calculation floats back into boardroom-ready formatted strings (`$`, `₹`, `€`, `%`, `()`):")
        display_df = bp.format_for_display(clean_df)
        st.dataframe(display_df.head(10), use_container_width=True)

    # 5. Export / Download
    st.markdown("---")
    st.markdown("### 💾 4. Download & Reproduce")

    col_dl, col_code = st.columns([1, 2])

    with col_dl:
        csv_buffer = io.StringIO()
        clean_df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="⬇️ Download Cleaned CSV",
            data=csv_buffer.getvalue(),
            file_name="bizpack_clean.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col_code:
        st.code(f"""
# Reproduce this in your own Python script or Jupyter Notebook:
import bizpack as bp

df = bp.clean_file('dirty_data.csv', target_currency='{target_curr}')
pareto_df = bp.pareto(df, dim_col='{str_cols[0] if str_cols else 'category'}', metric_col='{num_cols[0] if num_cols else 'revenue'}')
""", language="python")
