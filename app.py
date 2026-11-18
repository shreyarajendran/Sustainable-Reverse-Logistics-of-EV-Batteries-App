import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import date

st.set_page_config(page_title="Sustainable Recycling of EV Batteries", page_icon="♻️", layout="wide", initial_sidebar_state="expanded")

# Editable screening factors. Replace with current, documented factors before formal reporting.
# Demo scenario uses 0.720 kg CO2/kWh as requested. Verify the applicable
# CEA reporting-year factor before using this value for formal reporting.
DEFAULT_GRID_EF = 0.720
DEFAULT_DIESEL_EF = 2.68   # kg CO2/litre, direct combustion screening factor
DEFAULT_LPG_EF = 2.985     # kg CO2/kg, direct combustion screening factor

st.markdown("""
<style>
.block-container{max-width:1600px;padding-top:1.2rem;padding-bottom:2rem}
.hero{padding:1.7rem 2rem;border-radius:22px;margin:.2rem 0 1rem;background:linear-gradient(115deg,#092f2a,#087f68 58%,#79c99b);color:white;box-shadow:0 12px 32px rgba(0,70,55,.16)}
.hero h1{font-size:2.25rem;margin:.3rem 0 .45rem;color:white}.hero p{font-size:1.02rem;margin:0;color:#e4fff1}
.eyebrow{font-size:.75rem;letter-spacing:.15rem;font-weight:750;color:#b7f4d2}
div[data-testid="stMetric"]{background:linear-gradient(145deg,rgba(21,150,105,.10),rgba(21,150,105,.035));border:1px solid rgba(21,150,105,.2);padding:15px 17px;border-radius:16px;min-height:120px}
div[data-testid="stMetric"]{min-width:0;overflow:hidden;box-sizing:border-box}
div[data-testid="stMetricLabel"]{font-weight:650;white-space:normal;overflow-wrap:anywhere;word-break:normal;text-overflow:clip;line-height:1.25}
div[data-testid="stMetricValue"]{font-size:clamp(1rem,1.6vw,1.45rem);white-space:normal;overflow-wrap:anywhere;word-break:break-word;line-height:1.2;text-overflow:clip;min-width:0}
div[data-testid="stMetricValue"] > div{white-space:normal;overflow-wrap:anywhere;word-break:break-word;text-overflow:clip;overflow:visible;min-width:0}
div[data-testid="stMetricDelta"]{white-space:normal;overflow-wrap:anywhere}
[data-testid="stHorizontalBlock"]{align-items:stretch}
.stDataFrame, [data-testid="stDataFrame"]{max-width:100%;min-width:0}

.stTabs [data-baseweb="tab-list"]{gap:8px}.stTabs [data-baseweb="tab"]{border-radius:10px 10px 0 0;padding:10px 14px}
[data-testid="stDataFrame"]{border-radius:12px;overflow:hidden}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero"><div class="eyebrow">CIRCULAR ECONOMY • MATERIAL RECOVERY • CARBON & COST CONTROL</div><h1>♻️ Sustainable Recycling of EV Batteries</h1><p>A practical facility dashboard for recycling throughput, recovery yield, process performance, operational emissions, cost drivers and Gemba improvements.</p></div>', unsafe_allow_html=True)
st.caption("Scope: recycling and material recovery operations only. Transport and reverse-logistics calculations are excluded.")


st.sidebar.title("♻️ Facility inputs")
mode = st.sidebar.radio("View", ["Facility data", "Reference & methodology"])
if mode == "Reference & methodology":
    st.title("Reference & calculation methodology")
    st.markdown("""
**Calculation boundary and formulas**
- Purchased electricity (location-based) = total purchased kWh × applicable CEA grid factor. Renewable share is displayed separately and is NOT deducted from location-based emissions.
- On-site diesel emissions = litres consumed × diesel combustion factor.
- On-site LPG emissions = kg consumed × LPG combustion factor.
- Total included emissions = electricity + diesel + LPG + other separately measured process emissions.
- Carbon intensity = included emissions (kg CO₂e) ÷ battery input (tonnes).
- Overall mass recovery = recovered output mass ÷ battery input mass × 100.
- Element recovery = recovered element mass ÷ estimated element entering the process × 100.
- Process efficiency values must be based on each stage's good output ÷ that stage's input.

**Emission factor references**
- India electricity: Central Electricity Authority (CEA), CO₂ Baseline Database: https://cea.nic.in/cdm-co2-baseline-database/?lang=en
- Fuel combustion: IPCC 2006 Guidelines, Volume 2, Energy: https://www.ipcc-nggip.iges.or.jp/public/2006gl/vol2.html
- GHG accounting guidance: GHG Protocol Scope 2 Guidance: https://ghgprotocol.org/scope-2-guidance

**Factor-year warning:** the demo scenario uses 0.720 kg CO₂/kWh as a user-specified assumption. It is NOT certified as the latest CEA factor for the reporting period. Before formal reporting, verify and use the CEA factor applicable to that reporting year. Diesel and LPG values are direct-combustion screening factors; use fuel- and year-specific factors and include CH₄/N₂O where required by the chosen inventory method.

**Limitations:** This is an operational screening dashboard, not a verified GHG inventory or full lifecycle assessment. Unless entered, it excludes transport, upstream fuel/electricity supply chain, chemical/reagent lifecycle emissions, wastewater, waste treatment, refrigerant leakage, capital goods and avoided virgin-material credits.
""")
    st.stop()

# Reported facility inputs from the supplied tables. Versioned keys ensure the new
# values appear even if Streamlit retained widget state from an older app version.
st.sidebar.subheader("Reported facility data (supplied tables)")
received_t = st.sidebar.number_input("Annual EV-battery material received for recycling (tonnes/year)", 0.0, 100000.0, 3000.0, 10.0, key="received_t_v3")
ev_share_pct = st.sidebar.number_input("EV-battery share of total battery-recycling input (%)", 0.0, 100.0, 60.0, 1.0, key="ev_share_v3")
lfp_pct = st.sidebar.number_input("LFP share of EV-battery chemistry (%)", 0.0, 100.0, 20.0, 1.0, key="lfp_share_v3")
nmc_pct = st.sidebar.number_input("NMC share of EV-battery chemistry (%)", 0.0, 100.0, 80.0, 1.0, key="nmc_share_v3")
recycling_technology = st.sidebar.selectbox("Recycling technology used", ["Hydrometallurgical", "Pyrometallurgical", "Direct recycling", "Other"], index=0, key="technology_v3")
processed_pct = st.sidebar.number_input("Received EV-battery material successfully processed (%)", 0.0, 100.0, 90.0, 1.0, key="processed_pct_v3")
reported_capacity_util = st.sidebar.number_input("Reported current capacity utilisation (%)", 0.0, 100.0, 50.0, 1.0, key="reported_capacity_util_v3")
capacity_basis = st.sidebar.selectbox("Reported capacity basis", ["Installed capacity", "Nameplate capacity", "Other"], index=0, key="capacity_basis_v3")
energy_mass_t = st.sidebar.number_input("EV-battery mass processed during energy/fuel data year (tonnes/year)", 0.0, 100000.0, 1500.0, 10.0, key="energy_mass_v3")
reported_energy_intensity = st.sidebar.number_input("Reported energy consumption per tonne processed (kWh/tonne)", 0.0, 100000.0, 7000.0, 100.0, key="reported_intensity_v3")
major_energy_activities = st.sidebar.text_area("Major energy-consuming activities", "Discharge/deactivation; dismantling; separation; black-mass production; metal recovery; refining", key="energy_activities_v3")

# 1 · Facility & mass flow
st.sidebar.subheader("1 · Facility & material flow")
input_t = st.sidebar.number_input("Actual EV-battery throughput in latest full year (tonnes/year)", 0.0, 100000.0, 2000.0, 10.0, key="actual_throughput_v3")
capacity_t = st.sidebar.number_input("Annual EV-battery recycling capacity (tonnes/year)", 0.0, 200000.0, 5000.0, 10.0, key="annual_capacity_v3")
batteries_n = st.sidebar.number_input("Batteries processed (units/year)", 0, 10000000, 0, 100, key="batteries_processed_v3")
recycled_t = st.sidebar.number_input("Input mass actually recycled (tonnes/year)", 0.0, 100000.0, 1800.0, 10.0, key="actual_recycled_mass_v5")
recovered_t = st.sidebar.number_input("Annual recycled/recovered material produced (tonnes/year)", 0.0, 100000.0, 500.0, 10.0, key="recovered_output_v3")
residue_t = st.sidebar.number_input("Residues / non-recovered output (tonnes/year)", 0.0, 100000.0, 0.0, 50.0, key="residue_output_v3")

# 2 · Energy & emissions
st.sidebar.subheader("2 · Energy & emissions")
kwh_total = st.sidebar.number_input("Annual electricity consumed for EV-battery recycling (kWh/year)", 0.0, 200000000.0, 3400000.0, 10000.0, key="electricity_kwh_v3")
renew_pct = st.sidebar.slider("Renewable electricity share (%)", 0, 100, 0,
    help="Shown for disclosure. Not deducted from location-based grid emissions.")
grid_ef = st.sidebar.number_input("CEA grid factor (kg CO₂/kWh)", 0.0, 3.0, DEFAULT_GRID_EF, 0.001, format="%.3f",
    help="Demo scenario assumption. Verify and replace with the applicable CEA reporting-year factor before formal reporting.")
diesel_l = st.sidebar.number_input("Annual diesel consumed for EV-battery recycling (litres/year)", 0.0, 100000000.0, 300000.0, 100.0, key="diesel_litres_v3")
diesel_ef = st.sidebar.number_input("Diesel combustion factor (kg CO₂/litre)", 0.0, 10.0, DEFAULT_DIESEL_EF, 0.001, format="%.3f")
lpg_kg = st.sidebar.number_input("On-site LPG consumed (kg/year)", 0.0, 100000000.0, 0.0, 100.0)
lpg_ef = st.sidebar.number_input("LPG combustion factor (kg CO₂/kg)", 0.0, 10.0, DEFAULT_LPG_EF, 0.001, format="%.3f")
other_process_emissions = st.sidebar.number_input("Other measured process emissions (tonnes CO₂e/year)", 0.0, 1000000.0, 0.0, 1.0,
    help="Optional documented CO₂e estimate for other sources. Do not double count electricity or fuels.")

# 3 · Material composition & recovery
st.sidebar.subheader("3 · Material composition & recovery")
st.sidebar.caption("Enter chemistry-specific input composition and measured element recovery rates.")
materials = ["Lithium", "Nickel", "Cobalt", "Copper", "Aluminium", "Graphite"]
composition, recovery_rates = {}, {}
for m in materials:
    composition_default = {"Lithium": 3.5, "Nickel": 10.0, "Cobalt": 3.0}.get(m, 0.0)
    composition[m] = st.sidebar.number_input(f"{m} in input (% by mass)", 0.0, 100.0, composition_default, 0.5, key=f"comp_{m}")
    recovery_default = {"Lithium": 85, "Nickel": 95, "Cobalt": 95}.get(m, 0)
    recovery_rates[m] = st.sidebar.slider(f"{m} recovery rate (%)", 0, 100, recovery_default, key=f"rec_{m}")

# 4 · Process-stage performance
st.sidebar.subheader("4 · Process-stage performance")
st.sidebar.caption("Enter measured good output / stage input × 100.")
stage_eff = {}
for stage in ["Discharge & dismantling", "Shredding & separation", "Black-mass preparation", "Material extraction / refining", "Purification & finishing"]:
    stage_default = {"Discharge & dismantling": 95, "Shredding & separation": 90, "Black-mass preparation": 90, "Material extraction / refining": 85}.get(stage, 0)
    stage_eff[stage] = st.sidebar.slider(f"{stage} efficiency (%)", 0, 100, stage_default, key=f"stage_{stage}")

# 5 · Operating cost rates
st.sidebar.subheader("5 · Operating cost rates")
st.sidebar.caption("Annual costs are calculated from activity × entered unit rate.")
electricity_rate = st.sidebar.number_input("Electricity tariff (₹/kWh)", 0.0, 1000.0, 8.0, 0.1)
diesel_rate = st.sidebar.number_input("Diesel price (₹/litre)", 0.0, 1000.0, 0.0, 0.1)
lpg_rate = st.sidebar.number_input("LPG price (₹/kg)", 0.0, 1000.0, 0.0, 0.1)
chem_cost_per_t = st.sidebar.number_input("Chemicals / reagents (₹/tonne battery input)", 0.0, 1000000.0, 1500.0, 100.0)
labor_cost_per_t = st.sidebar.number_input("Labour & maintenance (₹/tonne battery input)", 0.0, 1000000.0, 2500.0, 100.0)
waste_cost_per_t = st.sidebar.number_input("Residue handling (₹/tonne residue)", 0.0, 1000000.0, 0.0, 100.0)
other_cost_per_t = st.sidebar.number_input("Other operating costs (₹/tonne battery input)", 0.0, 1000000.0, 0.0, 100.0)
quality = st.sidebar.selectbox("Overall input data quality", ["Measured", "Estimated", "Allocated", "Literature/reference"], index=1)
source_note = st.sidebar.text_area("Evidence / source note", "Illustrative demo scenario. Inputs are assumptions for dashboard demonstration and are not verified facility operating records.")

# Core calculations
# Location-based Scope 2 electricity: renewable share is reported separately, not deducted.
electricity_kg = kwh_total * grid_ef
diesel_kg = diesel_l * diesel_ef
lpg_kg_co2 = lpg_kg * lpg_ef
included_emissions_kg = electricity_kg + diesel_kg + lpg_kg_co2 + other_process_emissions * 1000
emissions_t = included_emissions_kg / 1000
carbon_intensity = included_emissions_kg / input_t if input_t else 0
capacity_util = input_t / capacity_t * 100 if capacity_t else 0
# Compare recycled mass with the annual material received for recycling. The
# latest-full-year throughput is a separately reported figure and may use a
# different reporting boundary/period; discrepancies are shown as warnings.
recycling_reference_mass_t = received_t if received_t > 0 else input_t
overall_recycling_eff = recycled_t / recycling_reference_mass_t * 100 if recycling_reference_mass_t else 0
overall_recovery_rate = recovered_t / input_t * 100 if input_t else 0
mass_balance_gap = input_t - recovered_t - residue_t
# Annual costs from actual activity and user-entered unit prices.
electricity_cost = kwh_total * electricity_rate
diesel_cost = diesel_l * diesel_rate
lpg_cost = lpg_kg * lpg_rate
chem_cost = input_t * chem_cost_per_t
labor_cost = input_t * labor_cost_per_t
waste_cost = residue_t * waste_cost_per_t
other_cost = input_t * other_cost_per_t
annual_cost = electricity_cost + diesel_cost + lpg_cost + chem_cost + labor_cost + waste_cost + other_cost
cost_per_t = annual_cost / input_t if input_t else 0
cost_per_recovered_t = annual_cost / recovered_t if recovered_t else 0
material_rows = []
for m in materials:
    input_element_t = input_t * composition[m] / 100
    recovered_element_t = input_element_t * recovery_rates[m] / 100
    material_rows.append({"Material": m, "Estimated input content (t/y)": input_element_t, "Recovery rate (%)": recovery_rates[m], "Estimated recovered element (t/y)": recovered_element_t})
material_df = pd.DataFrame(material_rows)
stage_df = pd.DataFrame([{"Process stage": k, "Process efficiency (%)": v, "Gap to 100% (percentage points)": 100-v} for k,v in stage_eff.items()])
emission_df = pd.DataFrame([
    {"Emission source":"Purchased grid electricity", "Activity":f"{kwh_total:,.0f} kWh/year", "Included emissions (t CO₂e/year)":electricity_kg/1000},
    {"Emission source":"On-site diesel combustion", "Activity":f"{diesel_l:,.0f} litres/year", "Included emissions (t CO₂e/year)":diesel_kg/1000},
    {"Emission source":"On-site LPG combustion", "Activity":f"{lpg_kg:,.0f} kg/year", "Included emissions (t CO₂e/year)":lpg_kg_co2/1000},
    {"Emission source":"Other entered process sources", "Activity":f"{other_process_emissions:,.2f} t CO₂e/year", "Included emissions (t CO₂e/year)":other_process_emissions},
])

processed_from_received_t = received_t * processed_pct / 100
implied_total_battery_input_t = received_t / (ev_share_pct / 100) if ev_share_pct else 0
calculated_energy_intensity = kwh_total / energy_mass_t if energy_mass_t else 0
facility_inputs_df = pd.DataFrame([
    {"Parameter":"Annual EV-battery material received for recycling", "Data value":received_t, "Unit":"tonnes/year", "Basis":"Reported input"},
    {"Parameter":"EV-battery share of total battery-recycling input", "Data value":ev_share_pct, "Unit":"%", "Basis":"Reported input"},
    {"Parameter":"Implied total battery-recycling input", "Data value":implied_total_battery_input_t, "Unit":"tonnes/year", "Basis":"Calculated: received EV material / EV share"},
    {"Parameter":"LFP chemistry share", "Data value":lfp_pct, "Unit":"%", "Basis":"Reported input"},
    {"Parameter":"NMC chemistry share", "Data value":nmc_pct, "Unit":"%", "Basis":"Reported input"},
    {"Parameter":"Recycling technology used", "Data value":recycling_technology, "Unit":"—", "Basis":"Reported input"},
    {"Parameter":"Received EV-battery material successfully processed", "Data value":processed_pct, "Unit":"%", "Basis":"Reported input"},
    {"Parameter":"Estimated mass processed from received material", "Data value":processed_from_received_t, "Unit":"tonnes/year", "Basis":"Received mass × processing rate"},
    {"Parameter":"Actual EV-battery throughput in latest full year", "Data value":input_t, "Unit":"tonnes/year", "Basis":"Reported input"},
    {"Parameter":"Annual EV-battery recycling capacity", "Data value":capacity_t, "Unit":"tonnes/year", "Basis":"Reported input"},
    {"Parameter":"Calculated capacity utilisation", "Data value":capacity_util, "Unit":"%", "Basis":"Throughput / capacity × 100"},
    {"Parameter":"Reported current capacity utilisation", "Data value":reported_capacity_util, "Unit":"%", "Basis":f"Reported input; {capacity_basis}"},
    {"Parameter":"Annual electricity consumed", "Data value":kwh_total, "Unit":"kWh/year", "Basis":"Reported input"},
    {"Parameter":"Annual diesel consumed", "Data value":diesel_l, "Unit":"litres/year", "Basis":"Reported input"},
    {"Parameter":"Mass processed during energy/fuel data year", "Data value":energy_mass_t, "Unit":"tonnes/year", "Basis":"Reported input"},
    {"Parameter":"Calculated energy intensity", "Data value":calculated_energy_intensity, "Unit":"kWh/tonne", "Basis":"Electricity / energy-year mass"},
    {"Parameter":"Reported energy intensity", "Data value":reported_energy_intensity, "Unit":"kWh/tonne", "Basis":"Reported input"},
    {"Parameter":"Major energy-consuming activities", "Data value":major_energy_activities, "Unit":"—", "Basis":"Reported input"},
])

# Main tabs
overview, material_tab, process_tab, carbon_tab, improve_tab, gemba_tab, report_tab = st.tabs(["🌱 Overview", "🔋 Material recovery", "⚙️ Process performance", "🌍 Carbon footprint", "💡 Improvement planner", "👷 Gemba board", "📊 Data & report"])

with overview:
    st.subheader("Facility performance at a glance")
    st.caption(f"Technology: {recycling_technology} | Chemistry: LFP {lfp_pct:.0f}% / NMC {nmc_pct:.0f}% | EV share of total battery-recycling input: {ev_share_pct:.0f}%")
    st.caption(f"Received material: {received_t:,.0f} tonnes/year | Latest-year EV throughput: {input_t:,.0f} tonnes/year | Successfully processed: {processed_pct:.0f}% (reported)")
    k1,k2,k3,k4 = st.columns(4)
    k1.metric("Battery input", f"{input_t:,.0f} tonnes/year")
    k2.metric("Batteries processed", f"{batteries_n:,} units/year")
    k3.metric("Overall material recovery", f"{overall_recovery_rate:,.2f}%")
    k4.metric("Included carbon footprint", f"{emissions_t:,.2f} t CO₂e/year")
    k1,k2,k3,k4 = st.columns(4)
    k1.metric("Mass actually recycled", f"{recycled_t:,.0f} tonnes/year")
    k2.metric("Material recovered", f"{recovered_t:,.0f} tonnes/year")
    k3.metric("Carbon intensity", f"{carbon_intensity:,.2f} kg CO₂e/tonne")
    k4.metric("Annual operating cost", f"₹{annual_cost:,.0f}/year")
    k1,k2,k3,k4 = st.columns(4)
    k1.metric("Capacity utilisation", f"{capacity_util:,.2f}%")
    k2.metric("Electricity consumed", f"{kwh_total:,.0f} kWh/year")
    k3.metric("Operating cost per input tonne", f"₹{cost_per_t:,.2f}/tonne")
    k4.metric("Cost per recovered tonne", f"₹{cost_per_recovered_t:,.2f}/tonne")
    st.metric("Reported capacity utilisation", f"{reported_capacity_util:,.2f}%", f"Calculated from throughput/capacity: {capacity_util:,.2f}%")
    e1, e2, e3 = st.columns(3)
    e1.metric("Reported energy intensity", f"{reported_energy_intensity:,.0f} kWh/tonne")
    e2.metric("Calculated energy intensity", f"{calculated_energy_intensity:,.1f} kWh/tonne")
    e3.metric("Energy-data processing mass", f"{energy_mass_t:,.0f} tonnes/year")
    with st.expander("Supplied facility inputs and reported values", expanded=False):
        st.dataframe(facility_inputs_df, use_container_width=True, hide_index=True)
    with st.expander("Optional: annual mass-balance check", expanded=False):
        st.caption("Checks whether input mass is accounted for by recovered output plus residues. Useful for data validation, but not a required headline KPI for every presentation.")
        fig = go.Figure(go.Waterfall(name="Annual mass balance", orientation="v", measure=["absolute","relative","total"], x=["Battery input","Recovered + residue","Unaccounted gap"], y=[input_t,-(recovered_t+residue_t),mass_balance_gap], text=[f"{input_t:,.1f} t",f"-{recovered_t+residue_t:,.1f} t",f"{mass_balance_gap:,.1f} t"], connector={"line":{"color":"#8aa39b"}}))
        fig.update_layout(title="Annual mass-balance check", yaxis_title="Tonnes/year", showlegend=False, margin=dict(l=10,r=10,t=55,b=10))
        st.plotly_chart(fig, use_container_width=True)
    if input_t and abs(mass_balance_gap) > max(1.0, input_t*0.02):
        st.warning(f"Mass balance does not close: input minus recovered output and residues = {mass_balance_gap:,.2f} tonnes/year. Check missing streams, moisture basis, stock changes and weighing records.")
    if capacity_t and capacity_util > 100: st.warning("Annual input exceeds rated capacity. Check reporting period, rated capacity and units.")
    if abs(lfp_pct + nmc_pct - 100) > 0.5:
        st.warning(f"LFP and NMC chemistry shares total {lfp_pct+nmc_pct:.1f}%, not 100%. Check whether other chemistries are included.")

with material_tab:
    st.subheader("Material recovery and element-specific rates")
    a,b,c = st.columns(3)
    a.metric("Input mass actually recycled", f"{recycled_t:,.2f} tonnes/year")
    b.metric("Overall recycling efficiency", f"{overall_recycling_eff:,.2f}%")
    c.metric("Overall material recovery rate", f"{overall_recovery_rate:,.2f}%")
    st.caption("Overall recycling efficiency here means input mass actually recycled ÷ annual EV-battery material received for recycling. Overall material recovery means total recovered output mass ÷ latest-full-year EV-battery throughput. These use the stated reference masses; the supplied figures may cover different reporting periods, so discrepancies are flagged rather than silently reconciled.")
    mleft,mright = st.columns([1.2,1])
    with mleft:
        fig = px.bar(material_df, x="Material", y="Recovery rate (%)", color="Recovery rate (%)", color_continuous_scale="Tealgrn", text=material_df["Recovery rate (%)"].map(lambda x:f"{x:.0f}%"), title="Element-specific recovery rate")
        fig.update_layout(yaxis_range=[0,100], coloraxis_showscale=False, margin=dict(l=5,r=5,t=55,b=10))
        st.plotly_chart(fig, use_container_width=True)
    with mright:
        fig = px.treemap(material_df, path=["Material"], values="Estimated recovered element (t/y)", color="Recovery rate (%)", color_continuous_scale="Tealgrn", title="Estimated recovered element mass")
        fig.update_traces(texttemplate="%{label}<br>%{value:,.1f} t/y")
        fig.update_layout(margin=dict(l=5,r=5,t=55,b=5))
        st.plotly_chart(fig, use_container_width=True)
    st.dataframe(material_df.style.format({"Estimated input content (t/y)":"{:,.2f}","Recovery rate (%)":"{:.1f}%","Estimated recovered element (t/y)":"{:,.2f}"}), use_container_width=True, hide_index=True)
    st.download_button("Download material recovery data (CSV)", material_df.to_csv(index=False).encode("utf-8"), "ev_battery_material_recovery.csv", "text/csv")

with process_tab:
    st.subheader("Process efficiency by recycling stage")
    st.caption("The stage values are editable assumptions in the sidebar. In a real facility, calculate each from that stage's own input and good output mass; avoid multiplying stage efficiencies unless the process boundaries are sequential and compatible.")
    fig = go.Figure()
    fig.add_trace(go.Bar(y=stage_df["Process stage"], x=stage_df["Process efficiency (%)"], orientation="h", name="Process efficiency", marker={"color":["#0B3D2E","#146B50","#238B68","#55A987","#9AD8B7"][:len(stage_df)], "line":{"color":"#FFFFFF","width":1}}, text=stage_df["Process efficiency (%)"].map(lambda x:f"{x:.0f}%"), textposition="outside"))
    fig.update_layout(title="Stage performance scorecard", xaxis_title="Efficiency (%)", xaxis_range=[0,110], yaxis_title="", showlegend=False, height=390, margin=dict(l=10,r=35,t=55,b=10))
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(stage_df.style.format({"Process efficiency (%)":"{:.1f}%","Gap to 100% (percentage points)":"{:.1f} pp"}), use_container_width=True, hide_index=True)
    st.markdown("#### Diagnostic checks")
    issues=[]
    if received_t and recycled_t > received_t: issues.append(("error","Mass actually recycled exceeds annual EV-battery material received; verify period and units."))
    if input_t and recycled_t > input_t: issues.append(("warning",f"Mass actually recycled ({recycled_t:,.0f} t/y) is greater than latest-full-year throughput ({input_t:,.0f} t/y). These may use different reporting periods or boundaries; verify before formal reporting."))
    if recovered_t > recycled_t and recycled_t > 0: issues.append(("warning","Recovered output exceeds mass recycled; check added reagents, moisture basis, stock changes and definitions."))
    if recovered_t + residue_t > input_t*1.02 and input_t>0: issues.append(("warning",f"Recovered material plus residues exceed input by {recovered_t+residue_t-input_t:,.2f} tonnes/year."))
    if kwh_total and energy_mass_t and kwh_total/energy_mass_t > 1000: issues.append(("warning",f"Calculated electricity intensity for the energy-data year is {kwh_total/energy_mass_t:,.1f} kWh/tonne. Reported intensity is {reported_energy_intensity:,.0f} kWh/tonne; reconcile the difference before formal reporting."))
    if not issues: issues.append(("success","No configured screening rule triggered. This does not prove the process is optimal; verify records and stage-level measurements."))
    for typ,msg in issues:
        getattr(st, typ if typ in ("warning","error","success") else "info")(msg)

with carbon_tab:
    st.subheader("Operational carbon footprint calculation")
    st.write("Included sources: purchased grid electricity (location-based), on-site diesel, on-site LPG and optional separately measured process emissions. Renewable electricity share is disclosed separately and is not deducted from location-based grid emissions. Transport and reverse logistics are excluded.")
    st.caption(f"Energy/fuel data-year mass basis: {energy_mass_t:,.0f} tonnes. Major energy-consuming activities: {major_energy_activities}")
    c1,c2,c3 = st.columns(3)
    c1.metric("Total included emissions", f"{emissions_t:,.2f} tonnes CO₂e/year")
    c2.metric("Carbon intensity", f"{carbon_intensity:,.2f} kg CO₂e/tonne input")
    c3.metric("Grid electricity emissions", f"{electricity_kg/1000:,.2f} tonnes CO₂e/year")
    left,right=st.columns([1.15,1])
    with left:
        st.dataframe(emission_df.style.format({"Included emissions (t CO₂e/year)":"{:,.3f}"}), use_container_width=True, hide_index=True)
        st.latex(r"E_{electricity}=kWh\times EF_{grid}")
        st.latex(r"E_{total}=E_{electricity}+E_{other}")
    with right:
        fig=px.bar(emission_df, x="Included emissions (t CO₂e/year)", y="Emission source", orientation="h", color="Emission source", text=emission_df["Included emissions (t CO₂e/year)"].map(lambda x:f"{x:,.2f} t"), title="Where operational emissions come from")
        fig.update_layout(showlegend=False, margin=dict(l=5,r=5,t=55,b=10))
        st.plotly_chart(fig, use_container_width=True)

with improve_tab:
    st.subheader("Improvement planner: facility-specific options")
    st.write("Options below are triggered by the facility values entered in the sidebar. The comparisons are screening estimates, not guaranteed savings; confirm feasibility, quotations and trial results before investment.")
    options = []
    # Conservative screening scenarios. Benefits are tied to relevant input metrics, not user-adjustable sliders.
    if kwh_total > 0 and input_t > 0:
        intensity = kwh_total / energy_mass_t if energy_mass_t else 0
        if intensity >= 500:
            options.append({"Improvement option":"Sub-meter and optimise shredding/separation loads", "Why it appears":f"Electricity intensity is {intensity:,.0f} kWh per input tonne; stage-level loads are not separated.", "Practical action":"Install/check sub-meters on shredder, conveyor and separation line; compare kWh per batch, remove idle running, inspect blade wear and review feed rate.", "basis":"Electricity", "saving_pct":0.08, "capex_pct":0.12})
        else:
            options.append({"Improvement option":"Batch scheduling and idle shutdown controls", "Why it appears":f"Electricity intensity is {intensity:,.0f} kWh per input tonne; verify whether equipment runs unloaded between batches.", "Practical action":"Introduce batch-based start/stop checklist, interlocks where safe, and weekly idle-load checks before considering major equipment replacement.", "basis":"Electricity", "saving_pct":0.04, "capex_pct":0.015})
        if renew_pct < 15:
            options.append({"Improvement option":"Reduce purchased electricity through process-load management", "Why it appears":f"Renewable share entered is {renew_pct}% and electricity is a modelled emissions source.", "Practical action":"First identify the highest kWh-per-tonne stage using temporary meters; schedule high-load equipment efficiently and correct avoidable idle operation. This option does not assume solar procurement.", "basis":"Electricity", "saving_pct":0.05, "capex_pct":0.025})
    if stage_eff.get("Shredding & separation",100) < 90:
        options.append({"Improvement option":"Tune separator settings and inspect wear parts", "Why it appears":f"Shredding & separation efficiency is {stage_eff.get('Shredding & separation',0):.0f}%.", "Practical action":"Run a controlled batch trial: check screen size, feed rate, blade/screen wear and separator settings; weigh and sample outputs before/after.", "basis":"Yield", "saving_pct":0.0, "capex_pct":0.04})
    if stage_eff.get("Black-mass preparation",100) < 90:
        options.append({"Improvement option":"Improve black-mass handling and contamination control", "Why it appears":f"Black-mass preparation efficiency is {stage_eff.get('Black-mass preparation',0):.0f}%.", "Practical action":"Separate material by chemistry and batch, prevent spillage, standardise sieve/collection checks and record moisture/contamination on a consistent basis.", "basis":"Yield", "saving_pct":0.0, "capex_pct":0.02})
    if input_t > 0 and mass_balance_gap > max(1.0, input_t*0.02):
        options.append({"Improvement option":"Reconcile weighing and inventory before process investment", "Why it appears":f"Mass-balance gap is {mass_balance_gap:,.1f} tonnes/year, above the app's 2% screening tolerance.", "Practical action":"Check calibrated scales, reporting periods, work-in-progress, moisture basis and whether all residue/output streams are recorded. Do not infer process losses until records reconcile.", "basis":"Data", "saving_pct":0.0, "capex_pct":0.002})
    if residue_t > 0 and input_t > 0 and residue_t / input_t >= 0.25:
        options.append({"Improvement option":"Characterise and segregate residue streams", "Why it appears":f"Residues are {residue_t/input_t*100:.1f}% of input mass.", "Practical action":"Weigh residues by stream, sample composition, identify recoverable fractions and obtain quotations from authorised downstream handlers; retain compliant disposal for hazardous fractions.", "basis":"Residue", "saving_pct":0.08, "capex_pct":0.015})
    if input_t > 0 and waste_cost > 0 and residue_t > 0 and residue_t / input_t < 0.25:
        options.append({"Improvement option":"Tender residue handling by segregated stream", "Why it appears":"Residue handling has a non-zero annual cost and residue share is below the high-residue screening trigger.", "Practical action":"Separate streams by hazard and composition, compare authorised vendor quotations and track cost per tonne by stream.", "basis":"Residue", "saving_pct":0.05, "capex_pct":0.005})
    if stage_eff.get("Discharge & dismantling",100) < 90:
        options.append({"Improvement option":"Standardise dismantling sequence and batch records", "Why it appears":f"Discharge & dismantling efficiency is {stage_eff.get('Discharge & dismantling',0):.0f}%.", "Practical action":"Review work instructions, tool condition, training and component weighing; test one change at a time with the site's safety lead.", "basis":"Yield", "saving_pct":0.0, "capex_pct":0.01})
    if not options:
        options.append({"Improvement option":"Run a short energy-and-mass measurement study", "Why it appears":"Current entered values do not trigger a specific screening flag.", "Practical action":"Collect batch-level input/output weights and kWh readings for each major stage over representative operating shifts, then re-enter the measured values to unlock targeted recommendations.", "basis":"Measurement", "saving_pct":0.0, "capex_pct":0.002})

    results=[]
    for o in options:
        capex = 0.0  # entered as a quotation/engineering estimate below
        elec_saved_kwh = kwh_total * o["saving_pct"] if o["basis"] == "Electricity" else 0.0
        carbon_saved_t = elec_saved_kwh * grid_ef / 1000
        cost_saved = elec_saved_kwh * electricity_rate
        if o["basis"] == "Residue":
            cost_saved = waste_cost * o["saving_pct"]
        elif o["basis"] == "Yield":
            # No unverified carbon or revenue credit is assigned to yield changes.
            cost_saved = 0.0
        elif o["basis"] in ("Data", "Measurement"):
            cost_saved = 0.0
            carbon_saved_t = 0.0
        scenario_emissions = max(0.0, emissions_t - carbon_saved_t)
        results.append({"Improvement option":o["Improvement option"],"Why it appears":o["Why it appears"],"Practical implementation":o["Practical action"],"Estimated one-time cost (₹)":capex,"Potential annual cost saving (₹/year)":cost_saved,"Potential carbon reduction (t CO2e/year)":carbon_saved_t,"Potential carbon reduction (%)":(carbon_saved_t / emissions_t * 100) if emissions_t > 0 else 0.0,"Scenario emissions (t CO₂e/year)":scenario_emissions,"Simple payback (years)":capex/cost_saved if cost_saved>0 else None,"Estimate basis":o["basis"]})
    result_df=pd.DataFrame(results)
    st.caption("Only options relevant to entered values are shown. Savings percentages are screening assumptions, not guaranteed outcomes. Enter a quotation or engineering estimate for one-time cost; the app does not invent CAPEX from annual operating cost.")
    capex_input = result_df[["Improvement option", "Estimated one-time cost (₹)"]].copy()
    capex_input = st.data_editor(capex_input, use_container_width=True, hide_index=True,
        column_config={"Estimated one-time cost (₹)": st.column_config.NumberColumn("Quoted / estimated one-time cost (₹)", min_value=0.0, step=10000.0, format="₹%.0f")},
        key="improvement_capex_editor")
    result_df["Estimated one-time cost (₹)"] = capex_input["Estimated one-time cost (₹)"].fillna(0.0)
    result_df["Simple payback (years)"] = result_df.apply(
        lambda r: r["Estimated one-time cost (₹)"] / r["Potential annual cost saving (₹/year)"]
        if r["Potential annual cost saving (₹/year)"] > 0 else None, axis=1)
    st.dataframe(result_df.style.format({"Estimated one-time cost (₹)":"₹{:,.0f}","Potential annual cost saving (₹/year)":"₹{:,.0f}","Potential carbon reduction (t CO2e/year)":"{:,.2f}","Scenario emissions (t CO₂e/year)":"{:,.2f}","Simple payback (years)":lambda x:"Not quantifiable" if pd.isna(x) else f"{x:.2f}"}),use_container_width=True,hide_index=True)
    c1,c2=st.columns(2)
    with c1:
        fig=px.bar(result_df,x="Potential carbon reduction (t CO2e/year)",y="Improvement option",orientation="h",color="Potential carbon reduction (t CO2e/year)",color_continuous_scale="Tealgrn",title="Potential annual carbon reduction")
        fig.update_layout(coloraxis_showscale=False,margin=dict(l=5,r=15,t=55,b=10))
        st.plotly_chart(fig,use_container_width=True)
    with c2:
        fig=px.bar(result_df,x="Potential annual cost saving (₹/year)",y="Improvement option",orientation="h",color="Potential annual cost saving (₹/year)",color_continuous_scale="Blues",title="Potential annual operating-cost saving")
        fig.update_layout(coloraxis_showscale=False,margin=dict(l=5,r=15,t=55,b=10))
        st.plotly_chart(fig,use_container_width=True)
    st.download_button("Download improvement comparison (CSV)",result_df.to_csv(index=False).encode("utf-8"),"ev_battery_improvement_scenarios.csv","text/csv")

with gemba_tab:
    st.subheader("Gemba visual management board")
    st.write("Use this board during a walk at the actual work area. Record observed evidence, assign a countermeasure and follow up. Default prompts are not claims about the facility.")
    st.info("Gemba is direct observation where the work happens. This board supports continuous improvement; it is not an automated safety or regulatory certification.")
    default_rows=pd.DataFrame([
        {"Process stage":"Receiving & identification","Status":"Not checked","Priority":"High","Evidence / observation":"Confirm battery ID, chemistry, condition and intake weight are logged.","Waste / risk type":"Traceability / safety","Countermeasure":"Standard intake checklist and quarantine criteria","Owner":"Operations","Due date":""},
        {"Process stage":"Safe discharge & dismantling","Status":"Not checked","Priority":"Critical","Evidence / observation":"Verify isolation, PPE, damaged-battery handling and emergency readiness.","Waste / risk type":"Safety / energy","Countermeasure":"Review SOP, competency and emergency response","Owner":"EHS","Due date":""},
        {"Process stage":"Shredding & mechanical separation","Status":"Not checked","Priority":"High","Evidence / observation":"Check dust controls, downtime, separation losses and stage energy meter.","Waste / risk type":"Energy / material loss","Countermeasure":"Track kWh per batch and inspect separator settings","Owner":"Maintenance","Due date":""},
        {"Process stage":"Black-mass preparation","Status":"Not checked","Priority":"Medium","Evidence / observation":"Check weighing, moisture, contamination and batch traceability.","Waste / risk type":"Yield / quality","Countermeasure":"Reconcile black-mass output and assay results","Owner":"Quality","Due date":""},
        {"Process stage":"Extraction / refining","Status":"Not checked","Priority":"High","Evidence / observation":"Review reagent use, temperature, energy, yield and effluent controls.","Waste / risk type":"Chemical / carbon","Countermeasure":"Review dosing and batch performance with process engineer","Owner":"Process","Due date":""},
        {"Process stage":"Purification & finishing","Status":"Not checked","Priority":"Medium","Evidence / observation":"Verify product purity, rejected batches and rework quantities.","Waste / risk type":"Quality / rework","Countermeasure":"Use quality feedback to adjust upstream process parameters","Owner":"Quality","Due date":""},
        {"Process stage":"Residues & recovered materials","Status":"Not checked","Priority":"High","Evidence / observation":"Check output weights, residue segregation and documented destinations.","Waste / risk type":"Recovery / disposal cost","Countermeasure":"Complete weekly mass-balance and residue-cost review","Owner":"Environment","Due date":""},
    ])
    edited=st.data_editor(default_rows,use_container_width=True,hide_index=True,num_rows="dynamic",column_config={
        "Process stage":st.column_config.TextColumn("Process stage",required=True),
        "Status":st.column_config.SelectboxColumn("Status",options=["Not checked","Observed - good","Action required","In progress","Closed","Not applicable"],required=True),
        "Priority":st.column_config.SelectboxColumn("Priority",options=["Critical","High","Medium","Low"],required=True),
        "Evidence / observation":st.column_config.TextColumn("Evidence / observation",width="large"),
        "Waste / risk type":st.column_config.TextColumn("Waste / risk type"),
        "Countermeasure":st.column_config.TextColumn("Countermeasure",width="large"),
        "Owner":st.column_config.TextColumn("Owner"),"Due date":st.column_config.TextColumn("Due date")},key="gemba_editor_v2")
    total=len(edited)
    actions=int(edited["Status"].isin(["Action required","In progress"]).sum()) if total else 0
    closed=int((edited["Status"]=="Closed").sum()) if total else 0
    critical=int((edited["Priority"]=="Critical").sum()) if total else 0
    checked=int(edited["Status"].isin(["Observed - good","Action required","In progress","Closed","Not applicable"]).sum()) if total else 0
    a,b,c,d=st.columns(4)
    a.metric("Checks in board",f"{total:,}")
    b.metric("Reviewed",f"{checked:,}",f"{checked/total*100:.0f}% reviewed" if total else None)
    c.metric("Open / in-progress actions",f"{actions:,}")
    d.metric("Critical-priority items",f"{critical:,}")
    left,right=st.columns([1.1,1])
    with left:
        if total:
            counts=edited["Status"].value_counts().rename_axis("Status").reset_index(name="Checks")
            fig=px.bar(counts.sort_values("Checks",ascending=True),x="Checks",y="Status",orientation="h",text="Checks",color="Status",title="Gemba board — observations by status",color_discrete_sequence=["#0B6E5B","#43A982","#9AD8B7","#E6B655","#C96B5C","#7C8C89"])
            fig.update_traces(textposition="outside",cliponaxis=False)
            fig.update_layout(showlegend=False,xaxis_title="Number of observations",yaxis_title="",margin=dict(l=5,r=25,t=55,b=10),height=340)
            st.plotly_chart(fig,use_container_width=True)
    with right:
        if total:
            counts=edited.groupby(["Priority","Status"]).size().reset_index(name="Count")
            fig=px.bar(counts,x="Priority",y="Count",color="Status",barmode="stack",category_orders={"Priority":["Critical","High","Medium","Low"]},title="Action load by priority")
            fig.update_layout(margin=dict(l=5,r=5,t=55,b=10))
            st.plotly_chart(fig,use_container_width=True)
    st.markdown("#### Action register — what needs attention first?")
    if total:
        open_items=edited[edited["Status"].isin(["Action required","In progress","Not checked"])].copy()
        order={"Critical":0,"High":1,"Medium":2,"Low":3}
        if len(open_items):
            open_items["_sort"]=open_items["Priority"].map(order).fillna(4)
            open_items=open_items.sort_values("_sort").drop(columns="_sort")
            st.dataframe(open_items,use_container_width=True,hide_index=True)
        else: st.success("No open items are currently marked in the Gemba board. Confirm all stages were reviewed before concluding.")
    st.download_button("Download Gemba log (CSV)",edited.to_csv(index=False).encode("utf-8"),"ev_battery_gemba_log.csv","text/csv")

with report_tab:
    st.subheader("Data & reports — complete facility record")
    st.markdown("This is the consolidated reporting area: all supplied facility-table inputs, throughput, batteries recycled, recycling efficiency, recovered material, chemistry, technology, process efficiency, electricity and fuel use, carbon footprint, operating costs, unit costs and improvement scenarios. Expand each section below to inspect the values and download CSVs or the full report.")
    st.info("Annual costs are calculated automatically from activity × unit rate. Includes purchased electricity, on-site diesel, on-site LPG and entered other process emissions. Check factors and GHG boundary before formal reporting.")
    calculated_energy_intensity = kwh_total / energy_mass_t if energy_mass_t else 0
    st.caption(f"Table-value check: electricity ÷ energy/fuel mass basis = {calculated_energy_intensity:,.1f} kWh/tonne, while the supplied table reports approximately {reported_energy_intensity:,.0f} kWh/tonne. These are retained separately as reported values; verify the underlying period/boundary.")
    if capacity_t and abs(capacity_util - reported_capacity_util) > 0.1:
        st.warning(f"Capacity check: throughput ÷ stated capacity calculates to {capacity_util:,.1f}%, while the supplied table reports {reported_capacity_util:,.1f}%. Both values are retained; verify the capacity denominator/reporting basis.")
    # Detailed tables use explicit units in column names so exports remain understandable outside the app.
    overview_df = pd.DataFrame([
        {"Metric":"Annual EV-battery material received for recycling", "Value":received_t, "Unit":"tonnes/year", "Basis":quality},
        {"Metric":"EV-battery share of total battery-recycling input", "Value":ev_share_pct, "Unit":"%", "Basis":quality},
        {"Metric":"LFP chemistry share", "Value":lfp_pct, "Unit":"%", "Basis":quality},
        {"Metric":"NMC chemistry share", "Value":nmc_pct, "Unit":"%", "Basis":quality},
        {"Metric":"Recycling technology used", "Value":recycling_technology, "Unit":"—", "Basis":quality},
        {"Metric":"Received EV-battery material successfully processed", "Value":processed_pct, "Unit":"%", "Basis":quality},
        {"Metric":"Reported current capacity utilisation", "Value":reported_capacity_util, "Unit":"%", "Basis":quality},
        {"Metric":"Reported capacity basis", "Value":capacity_basis, "Unit":"—", "Basis":quality},
        {"Metric":"Mass processed during energy/fuel data year", "Value":energy_mass_t, "Unit":"tonnes/year", "Basis":quality},
        {"Metric":"Reported energy consumption per tonne processed", "Value":reported_energy_intensity, "Unit":"kWh/tonne", "Basis":quality},
        {"Metric":"Major energy-consuming activities", "Value":major_energy_activities, "Unit":"—", "Basis":quality},
                {"Metric":"Battery input", "Value":input_t, "Unit":"tonnes/year", "Basis":quality},
        {"Metric":"Batteries processed", "Value":batteries_n, "Unit":"batteries/year", "Basis":quality},
        {"Metric":"Input mass actually recycled", "Value":recycled_t, "Unit":"tonnes/year", "Basis":quality},
        {"Metric":"Overall recycling efficiency", "Value":overall_recycling_eff, "Unit":"% of annual material received", "Basis":"Calculated: recycled mass / annual EV-battery material received × 100"},
        {"Metric":"Total recovered material output", "Value":recovered_t, "Unit":"tonnes/year", "Basis":quality},
        {"Metric":"Overall mass recovery rate", "Value":overall_recovery_rate, "Unit":"% of battery input mass", "Basis":"Calculated: recovered output / input mass × 100"},
        {"Metric":"Residues / non-recovered output", "Value":residue_t, "Unit":"tonnes/year", "Basis":quality},
        {"Metric":"Mass-balance gap", "Value":mass_balance_gap, "Unit":"tonnes/year", "Basis":"Input − recovered output − residues; investigate non-zero gap"},
        {"Metric":"Rated processing capacity", "Value":capacity_t, "Unit":"tonnes/year", "Basis":quality},
        {"Metric":"Capacity utilisation", "Value":capacity_util, "Unit":"% of rated capacity", "Basis":"Calculated: input / rated capacity × 100"},
    ])
    cost_df = pd.DataFrame([
        {"Cost category":"Electricity", "Activity basis":"kWh/year × ₹/kWh", "Unit rate (₹/unit)":electricity_rate, "Annual cost (₹/year)":electricity_cost},
        {"Cost category":"Diesel", "Activity basis":"litres/year × ₹/litre", "Unit rate (₹/unit)":diesel_rate, "Annual cost (₹/year)":diesel_cost},
        {"Cost category":"LPG", "Activity basis":"kg/year × ₹/kg", "Unit rate (₹/unit)":lpg_rate, "Annual cost (₹/year)":lpg_cost},
        {"Cost category":"Chemicals / reagents", "Activity basis":"tonnes input/year × ₹/tonne", "Unit rate (₹/unit)":chem_cost_per_t, "Annual cost (₹/year)":chem_cost},
        {"Cost category":"Labour & maintenance", "Activity basis":"tonnes input/year × ₹/tonne", "Unit rate (₹/unit)":labor_cost_per_t, "Annual cost (₹/year)":labor_cost},
        {"Cost category":"Residue / waste handling", "Activity basis":"tonnes residue/year × ₹/tonne", "Unit rate (₹/unit)":waste_cost_per_t, "Annual cost (₹/year)":waste_cost},
        {"Cost category":"Other operating costs", "Activity basis":"tonnes input/year × ₹/tonne", "Unit rate (₹/unit)":other_cost_per_t, "Annual cost (₹/year)":other_cost},
        {"Cost category":"TOTAL OPERATING COST", "Activity basis":"Sum of calculated annual categories", "Unit rate (₹/unit)":None, "Annual cost (₹/year)":annual_cost},
    ])
    energy_df = pd.DataFrame([
        {"Energy / emission parameter":"Electricity consumed", "Value":kwh_total, "Unit":"kWh/year", "Calculation / note":"User-entered purchased electricity"},
        {"Energy / emission parameter":"Electricity intensity", "Value":(kwh_total / input_t if input_t else 0), "Unit":"kWh/tonne incoming batteries", "Calculation / note":"Purchased electricity ÷ annual battery input"},
        {"Energy / emission parameter":"Renewable electricity share", "Value":renew_pct, "Unit":"%", "Calculation / note":"Disclosed separately; not deducted from location-based emissions"},
        {"Energy / emission parameter":"Grid emission factor", "Value":grid_ef, "Unit":"kg CO₂/kWh", "Calculation / note":"User-specified demo assumption; verify applicable CEA reporting-year factor before formal reporting"},
        {"Energy / emission parameter":"Electricity emissions", "Value":electricity_kg/1000, "Unit":"tonnes CO₂/year", "Calculation / note":"Total purchased kWh × grid factor / 1,000"},
        {"Energy / emission parameter":"Diesel consumed", "Value":diesel_l, "Unit":"litres/year", "Calculation / note":"User-entered on-site combustion"},
        {"Energy / emission parameter":"Diesel factor", "Value":diesel_ef, "Unit":"kg CO₂/litre", "Calculation / note":"Direct combustion screening factor; check fuel-specific source"},
        {"Energy / emission parameter":"Diesel emissions", "Value":diesel_kg/1000, "Unit":"tonnes CO₂/year", "Calculation / note":"Litres × factor / 1,000"},
        {"Energy / emission parameter":"LPG consumed", "Value":lpg_kg, "Unit":"kg/year", "Calculation / note":"User-entered on-site combustion"},
        {"Energy / emission parameter":"LPG factor", "Value":lpg_ef, "Unit":"kg CO₂/kg", "Calculation / note":"Direct combustion screening factor; check fuel-specific source"},
        {"Energy / emission parameter":"LPG emissions", "Value":lpg_kg_co2/1000, "Unit":"tonnes CO₂/year", "Calculation / note":"kg consumed × factor / 1,000"},
        {"Energy / emission parameter":"Other process emissions", "Value":other_process_emissions, "Unit":"tonnes CO₂e/year", "Calculation / note":"Optional user-entered value; avoid double counting"},
        {"Energy / emission parameter":"TOTAL INCLUDED OPERATIONAL FOOTPRINT", "Value":emissions_t, "Unit":"tonnes (mixed CO₂ / CO₂e) per year", "Calculation / note":"Sum of included sources; see factor/GWP limitations"},
        {"Energy / emission parameter":"Carbon intensity", "Value":carbon_intensity, "Unit":"kg included emissions/tonne battery input", "Calculation / note":"Included emissions in kg / input tonnes"},
        {"Energy / emission parameter":"Mass processed during energy/fuel data year", "Value":energy_mass_t, "Unit":"tonnes/year", "Calculation / note":"Reported facility input; denominator for energy-year intensity"},
        {"Energy / emission parameter":"Calculated energy intensity", "Value":calculated_energy_intensity, "Unit":"kWh/tonne", "Calculation / note":"Electricity / mass processed during energy/fuel data year"},
        {"Energy / emission parameter":"Reported energy intensity", "Value":reported_energy_intensity, "Unit":"kWh/tonne", "Calculation / note":"Reported input; differs from calculated intensity and requires reconciliation"},
    ])
    with st.expander("1 · Supplied facility inputs (Tables 1–17)", expanded=True):
        st.dataframe(facility_inputs_df, use_container_width=True, hide_index=True)
        st.download_button("Download supplied facility inputs (CSV)", facility_inputs_df.to_csv(index=False).encode("utf-8"), "ev_recycling_supplied_facility_inputs.csv", "text/csv")
    with st.expander("2 · Facility throughput and recycling KPIs", expanded=True):
        st.dataframe(overview_df, use_container_width=True, hide_index=True)
        st.download_button("Download throughput & KPI data (CSV)", overview_df.to_csv(index=False).encode("utf-8"), "ev_recycling_throughput_kpis.csv", "text/csv")
    with st.expander("3 · Element-by-element recovery data", expanded=True):
        material_report_df = material_df.copy()
        material_report_df["Input composition (%)"] = [composition[m] for m in material_report_df["Material"]]
        material_report_df["Estimated element present in input (tonnes/year)"] = material_report_df["Material"].map(lambda m: input_t * composition[m] / 100)
        material_report_df["Estimated element recovered (tonnes/year)"] = material_report_df["Material"].map(lambda m: input_t * composition[m] / 100 * recovery_rates[m] / 100)
        material_report_df = material_report_df[["Material", "Input composition (%)", "Estimated element present in input (tonnes/year)", "Recovery rate (%)", "Estimated element recovered (tonnes/year)"]]
        st.dataframe(material_report_df.style.format({"Input composition (%)":"{:,.2f}%", "Estimated element present in input (tonnes/year)":"{:,.3f}", "Recovery rate (%)":"{:,.2f}%", "Estimated element recovered (tonnes/year)":"{:,.3f}"}), use_container_width=True, hide_index=True)
        st.caption("Element quantities are estimates based on the composition percentages and recovery rates entered in the sidebar. Validate with battery chemistry records and assays.")
        st.download_button("Download material recovery data (CSV)", material_report_df.to_csv(index=False).encode("utf-8"), "ev_recycling_material_recovery.csv", "text/csv")
    with st.expander("4 · Process-stage efficiency", expanded=True):
        st.dataframe(stage_df.style.format({"Process efficiency (%)":"{:,.2f}%", "Gap to 100% (percentage points)":"{:,.2f} pp"}), use_container_width=True, hide_index=True)
        st.caption("The sidebar efficiencies are entered values, not independently calculated stage yields unless the facility has provided each stage's good output and stage input mass.")
        st.download_button("Download process efficiency data (CSV)", stage_df.to_csv(index=False).encode("utf-8"), "ev_recycling_process_efficiency.csv", "text/csv")
    with st.expander("5 · Energy and carbon footprint calculation", expanded=True):
        st.dataframe(energy_df.style.format({"Value":lambda v: f"{v:,.3f}" if isinstance(v,(int,float)) else str(v)}), use_container_width=True, hide_index=True)
        fig_carbon = px.bar(emission_df, x="Emission source", y="Included emissions (t CO₂e/year)", color="Emission source", text="Included emissions (t CO₂e/year)", title="Annual included operational emissions by source")
        fig_carbon.update_traces(texttemplate="%{text:,.3f} t", textposition="outside", cliponaxis=False)
        fig_carbon.update_layout(showlegend=False, yaxis_title="tonnes CO₂e/year", xaxis_title="", margin=dict(l=10,r=10,t=65,b=10))
        st.plotly_chart(fig_carbon, use_container_width=True)
        st.download_button("Download energy & carbon data (CSV)", energy_df.to_csv(index=False).encode("utf-8"), "ev_recycling_energy_carbon.csv", "text/csv")
    with st.expander("6 · Operating cost breakdown", expanded=True):
        st.dataframe(cost_df.style.format({"Unit rate (₹/unit)":lambda v:"—" if pd.isna(v) else f"₹{v:,.2f}","Annual cost (₹/year)":"₹{:,.2f}"}), use_container_width=True, hide_index=True)
        fig_cost = px.pie(cost_df[cost_df["Cost category"] != "TOTAL OPERATING COST"], names="Cost category", values="Annual cost (₹/year)", hole=0.48, title="Annual operating-cost composition", hover_data={"Annual cost (₹/year)":":,.2f"})
        fig_cost.update_traces(textposition="inside", texttemplate="%{percent:.1%}", hovertemplate="%{label}<br>₹%{value:,.2f}/year<extra></extra>")
        st.plotly_chart(fig_cost, use_container_width=True)
        st.metric("Cost per tonne of battery input", f"₹{cost_per_t:,.2f}/tonne")
        st.metric("Cost per tonne of recovered material", f"₹{cost_per_recovered_t:,.2f}/tonne")
        st.download_button("Download operating cost data (CSV)", cost_df.to_csv(index=False).encode("utf-8"), "ev_recycling_operating_costs.csv", "text/csv")
    with st.expander("7 · Carbon and cost improvement scenarios", expanded=True):
        st.dataframe(result_df.style.format({"Estimated one-time cost (₹)":"₹{:,.2f}", "Potential annual cost saving (₹/year)":"₹{:,.2f}", "Potential carbon reduction (t CO2e/year)":"{:,.3f} t", "Potential carbon reduction (%)":"{:,.2f}%", "Simple payback (years)":lambda x:"Not available" if pd.isna(x) else f"{x:,.2f} years", "Scenario emissions (t CO₂e/year)":"{:,.3f} t"}), use_container_width=True, hide_index=True)
        st.download_button("Download improvement scenarios (CSV)", result_df.to_csv(index=False).encode("utf-8"), "ev_recycling_improvement_scenarios.csv", "text/csv")
    # Full report combines all core sections and preserves units and calculation caveats.
    report = [
        "SUSTAINABLE RECYCLING OF EV BATTERIES — FACILITY DATA REPORT",
        f"Generated date: {date.today().isoformat()}", f"Data quality: {quality}", f"Evidence / source note: {source_note or 'Not supplied'}", "",
        "1. SUPPLIED FACILITY INPUTS (TABLES 1–17)",
    ]
    for _, row in facility_inputs_df.iterrows(): report.append(f"{row['Parameter']}: {row['Data value']} {row['Unit']} | Basis: {row['Basis']}")
    report += ["", "2. FACILITY THROUGHPUT AND KPIs"]
    for _, row in overview_df.iterrows(): report.append(f"{row['Metric']}: {row['Value']} {row['Unit']} | Basis: {row['Basis']}")
    report += ["", "2. MATERIAL RECOVERY BY ELEMENT"]
    for _, row in material_report_df.iterrows(): report.append(f"{row['Material']}: input composition {row['Input composition (%)']:.2f}%; estimated element present {row['Estimated element present in input (tonnes/year)']:,.3f} tonnes/year; recovery rate {row['Recovery rate (%)']:.2f}%; estimated recovered {row['Estimated element recovered (tonnes/year)']:,.3f} tonnes/year")
    report += ["", "3. PROCESS-STAGE PERFORMANCE"]
    for _, row in stage_df.iterrows(): report.append(f"{row['Process stage']}: {row['Process efficiency (%)']:.2f}% efficiency; {row['Gap to 100% (percentage points)']:.2f} percentage points below 100%")
    report += ["", "4. ENERGY AND CARBON FOOTPRINT"]
    for _, row in energy_df.iterrows(): report.append(f"{row['Energy / emission parameter']}: {row['Value']:,.4f} {row['Unit']} | {row['Calculation / note']}")
    report += ["", "5. OPERATING COSTS"]
    for _, row in cost_df.iterrows(): report.append(f"{row['Cost category']}: ₹{row['Annual cost (₹/year)']:,.2f}/year")
    report += ["", "6. IMPROVEMENT SCENARIOS"]
    for _, row in result_df.iterrows():
        report.append(f"{row['Improvement option']}: potential carbon reduction {row['Potential carbon reduction (t CO2e/year)']:,.3f} tonnes CO2e/year ({row['Potential carbon reduction (%)']:.2f}%); potential annual cost saving ₹{row['Potential annual cost saving (₹/year)']:,.2f}; estimated implementation cost ₹{row['Estimated one-time cost (₹)']:,.2f}; simple payback {row['Simple payback (years)'] if pd.notna(row['Simple payback (years)']) else 'not available'} years")
    report += ["", "7. CARBON BOUNDARY AND LIMITATIONS", "Included: location-based purchased electricity, on-site diesel, on-site LPG and optional other entered process emissions. Renewable share is disclosed separately and not deducted from location-based electricity.", "Excluded unless separately measured/entered: transport, chemical/reagent lifecycle emissions, wastewater treatment, residue treatment, upstream fuel supply, capital goods and avoided virgin-material production credits.", "The 0.720 kg CO₂/kWh electricity factor used in this demo is a user-specified scenario assumption, not verified as the applicable CEA factor for the reporting year. Diesel/LPG defaults are direct-combustion screening factors; include CH₄/N₂O where required. This report is not a verified GHG inventory or full lifecycle assessment.", "Mass-balance gap = battery input − recovered output − residues. A non-zero result requires reconciliation; definitions and boundaries may differ by facility."]
    st.download_button("Download complete facility report (TXT)", "\n".join(report).encode("utf-8"), "sustainable_ev_battery_recycling_full_report.txt", "text/plain")
    st.caption("Every report section is downloadable separately as CSV. The complete TXT report consolidates throughput, element recovery, process efficiency, energy/emissions, cost and improvement estimates with units and limitations.")
