
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

st.set_page_config(
    page_title="Bacterial Cellulose Analytics",
    page_icon="🧬",
    layout="wide"
)

# ---------- DATABASE ----------
@st.cache_data
def load_data():
    import os

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "bacterial_cellulose.db")

    conn = sqlite3.connect(DB_PATH)

    data = pd.read_sql_query(
        "SELECT * FROM cellulose_production", conn
    )

    conn.close()
    return data

df = load_data()

# ---------- DESIGN ----------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #101827, #172b3a);
    color: white;
}
[data-testid="stMetric"] {
    background: #20394a;
    padding: 18px;
    border-radius: 14px;
    border: 1px solid #34576b;
}
h1, h2, h3 {
    color: #70d6d0;
}
</style>
""", unsafe_allow_html=True)

# ---------- TITLE ----------
st.title("🧬 Bacterial Cellulose Production Analytics")
st.caption("Research database • Production conditions • Yield analysis • Material properties")
st.divider()

# ---------- SIDEBAR FILTERS ----------
st.sidebar.title("🔎 Database Filters")

filtered = df.copy()

if "Bacterial_Strain" in df.columns:
    strains = sorted(df["Bacterial_Strain"].dropna().astype(str).unique())
    selected_strain = st.sidebar.multiselect(
        "Select bacterial strain", strains
    )
    if selected_strain:
        filtered = filtered[
            filtered["Bacterial_Strain"].astype(str).isin(selected_strain)
        ]

if "Carbon_Source" in df.columns:
    sources = sorted(df["Carbon_Source"].dropna().astype(str).unique())
    selected_source = st.sidebar.multiselect(
        "Select carbon source", sources
    )
    if selected_source:
        filtered = filtered[
            filtered["Carbon_Source"].astype(str).isin(selected_source)
        ]

if "Culture_Medium" in df.columns:
    media = sorted(df["Culture_Medium"].dropna().astype(str).unique())
    selected_medium = st.sidebar.multiselect(
        "Select culture medium", media
    )
    if selected_medium:
        filtered = filtered[
            filtered["Culture_Medium"].astype(str).isin(selected_medium)
        ]

# ---------- KPI CARDS ----------
st.subheader("📊 Research Overview")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Records", len(filtered))

if "Bacterial_Strain" in filtered.columns:
    c2.metric(
        "Bacterial Strains",
        filtered["Bacterial_Strain"].nunique()
    )
else:
    c2.metric("Bacterial Strains", "N/A")

if "Yield_percent" in filtered.columns:
    yields = pd.to_numeric(filtered["Yield_percent"], errors="coerce")
    highest = yields.max()
    c3.metric(
        "Highest Yield",
        f"{highest:.2f}%" if pd.notna(highest) else "N/A"
    )
    c4.metric(
        "Average Yield",
        f"{yields.mean():.2f}%" if yields.notna().any() else "N/A"
    )
else:
    c3.metric("Highest Yield", "N/A")
    c4.metric("Average Yield", "N/A")

st.divider()

# ---------- GRAPHS ----------
st.subheader("📈 Interactive Research Visualizations")

tab1, tab2, tab3, tab4 = st.tabs([
    "Yield Analysis",
    "Culture Conditions",
    "Material Properties",
    "Research Trends"
])

with tab1:
    if "Yield_percent" in filtered.columns:
        plot_df = filtered.copy()
        plot_df["Yield_percent"] = pd.to_numeric(
            plot_df["Yield_percent"], errors="coerce"
        )
        plot_df = plot_df.dropna(subset=["Yield_percent"])

        if not plot_df.empty:
            if "Bacterial_Strain" in plot_df.columns:
                fig = px.bar(
                    plot_df,
                    x="Bacterial_Strain",
                    y="Yield_percent",
                    color="Carbon_Source" if "Carbon_Source" in plot_df.columns else None,
                    title="Bacterial Cellulose Yield by Strain",
                    text_auto=True,
                    template="plotly_dark"
                )
                st.plotly_chart(fig, use_container_width=True)

            if "Carbon_Source" in plot_df.columns:
                avg = plot_df.groupby(
                    "Carbon_Source", as_index=False
                )["Yield_percent"].mean()

                fig2 = px.pie(
                    avg,
                    names="Carbon_Source",
                    values="Yield_percent",
                    title="Average Yield Contribution by Carbon Source",
                    template="plotly_dark"
                )
                st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No yield values available for the selected filters.")
    else:
        st.info("Yield data is not available.")

with tab2:
    if "Temperature_C" in filtered.columns and "Yield_percent" in filtered.columns:
        temp_df = filtered.copy()
        temp_df["Temperature_C"] = pd.to_numeric(
            temp_df["Temperature_C"], errors="coerce"
        )
        temp_df["Yield_percent"] = pd.to_numeric(
            temp_df["Yield_percent"], errors="coerce"
        )
        temp_df = temp_df.dropna(
            subset=["Temperature_C", "Yield_percent"]
        )

        if not temp_df.empty:
            fig = px.scatter(
                temp_df,
                x="Temperature_C",
                y="Yield_percent",
                color="Culture_Mode" if "Culture_Mode" in temp_df.columns else None,
                hover_data=["Bacterial_Strain"] if "Bacterial_Strain" in temp_df.columns else None,
                title="Effect of Temperature on BC Yield",
                template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True)

    if "Culture_Mode" in filtered.columns:
        mode_counts = filtered["Culture_Mode"].value_counts().reset_index()
        mode_counts.columns = ["Culture Mode", "Records"]

        fig2 = px.bar(
            mode_counts,
            x="Culture Mode",
            y="Records",
            title="Culture Mode Distribution",
            template="plotly_dark"
        )
        st.plotly_chart(fig2, use_container_width=True)

with tab3:
    property_columns = [
        "Crystallinity_percent",
        "Crystallite_Size_nm",
        "Moisture_Content_percent",
        "Thickness_um"
    ]

    available = [col for col in property_columns if col in filtered.columns]

    if available:
        chosen_property = st.selectbox(
            "Choose material property", available
        )

        prop_df = filtered.copy()
        prop_df[chosen_property] = pd.to_numeric(
            prop_df[chosen_property], errors="coerce"
        )
        prop_df = prop_df.dropna(subset=[chosen_property])

        if not prop_df.empty and "Bacterial_Strain" in prop_df.columns:
            fig = px.bar(
                prop_df,
                x="Bacterial_Strain",
                y=chosen_property,
                color="Carbon_Source" if "Carbon_Source" in prop_df.columns else None,
                title=f"{chosen_property} by Bacterial Strain",
                template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No values available for this property.")
    else:
        st.info("Material property columns are not available in this dataset.")

with tab4:
    if "Year" in filtered.columns:
        year_df = filtered.copy()
        year_df["Year"] = pd.to_numeric(year_df["Year"], errors="coerce")
        year_counts = year_df.dropna(subset=["Year"]).groupby(
            "Year"
        ).size().reset_index(name="Number of Records")

        if not year_counts.empty:
            fig = px.line(
                year_counts,
                x="Year",
                y="Number of Records",
                markers=True,
                title="Research Publications by Year",
                template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Year information is not available.")
    else:
        st.info("Year column is not available.")

# ---------- DATA TABLE ----------
st.divider()
st.subheader("📚 Complete Research Database")
st.dataframe(filtered, use_container_width=True, height=400)

csv = filtered.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Download Filtered Research Data",
    data=csv,
    file_name="bacterial_cellulose_research.csv",
    mime="text/csv"
)

st.caption("Bacterial Cellulose Production Database | Research analytics dashboard")
# ---------- BACTERIAL CELLULOSE APPLICATIONS ----------
st.divider()
st.title("🧪 Potential Applications of Bacterial Cellulose")

st.write(
    "Explore potential uses of bacterial cellulose in food, "
    "medical, drug delivery, cosmetics and packaging fields."
)

applications = {
    "Food": {
        "Examples": "Nata de coco, food texture and fibre applications.",
        "Description": "Bacterial cellulose can be used as a food material "
                       "because of its water-holding capacity and texture."
    },
    "Medical / Biomedical": {
        "Examples": "Wound dressings, burn dressings and artificial-skin research.",
        "Description": "Bacterial cellulose is studied as a material for "
                       "wound-care and other biomedical applications."
    },
    "Drug Delivery": {
        "Examples": "Cellulose membranes and drug-loaded cellulose materials.",
        "Description": "Modified bacterial cellulose materials are being "
                       "investigated for controlled drug delivery."
    },
    "Cosmetics": {
        "Examples": "Facial masks and moisture-retaining cosmetic materials.",
        "Description": "Bacterial cellulose can be used in cosmetic "
                       "formulations because it can retain moisture."
    },
    "Packaging": {
        "Examples": "Biodegradable films and food-packaging materials.",
        "Description": "Bacterial cellulose is investigated as a renewable "
                       "material for biodegradable packaging."
    }
}

selected_application = st.selectbox(
    "Select an application area",
    list(applications.keys())
)

st.subheader(f"🔬 {selected_application}")

st.write("*Examples:*")
st.write(applications[selected_application]["Examples"])

st.write("*Potential use:*")
st.write(applications[selected_application]["Description"])

st.info(
    "Important: These are potential applications of bacterial cellulose "
    "as a material. They do not mean that every bacterial strain in this "
    "database is approved or proven for medical or food use."
)

st.subheader("🦠 Bacterial Strains in This Database")

if "Bacterial_Strain" in df.columns:
    strain_list = sorted(
        df["Bacterial_Strain"].dropna().astype(str).unique()
    )

    st.dataframe(
        pd.DataFrame({
            "Bacterial Strain": strain_list,
            "Demonstrated Role": [
                "Bacterial cellulose production; specific end-use "
                "not established by the production data."
                for strain in strain_list
            ]
        }),
        use_container_width=True
    )
