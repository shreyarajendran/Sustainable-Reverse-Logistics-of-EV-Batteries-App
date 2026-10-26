import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import date

st.set_page_config(page_title="Sustainable Recycling of EV Batteries", page_icon="♻️", layout="wide")

# Editable screening factors. Replace with current, documented factors before formal reporting.
DEFAULT_GRID_EF = 0.72       # kg CO2e/kWh; illustrative project factor, not a verified current factor

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
mode = st.sidebar.radio("Data mode", ["Demo scenario", "Facility data", "Reference & methodology"])
if mode == "Reference & methodology":
    st.title("Reference & calculation methodology")
    st.warning("Demo values are illustrative, not measured plant data. For formal reporting, replace all factors with current, geographically appropriate, documented sources and verify the organizational GHG boundary.")
    st.markdown("""
**Calculation boundaries and formulas**
- Electricity emissions = electricity consumed (kWh) × grid emission factor (kg CO₂e/kWh) × non-renewable share.
- Included operational emissions = purchased electricity adjusted for the entered renewable share, plus any separately measured other process emissions entered by the user.
- Diesel and LPG are excluded from this version because the chosen model boundary assumes electricity-powered recycling operations. If a real facility burns fuel on site, its emissions need to be added in a future expanded boundary.
- Carbon intensity = included emissions (kg CO₂e) ÷ battery input (tonnes).
- Overall mass recovery = recovered output mass (tonnes) ÷ battery input mass (tonnes) × 100.
- Element recovery rate = recovered element mass ÷ estimated element mass present in input × 100. This requires chemistry-specific composition data; the dashboard uses user-entered input composition and recovery rates.
- Process efficiency = good output mass from a stage ÷ stage input mass × 100. Enter stage-specific values from plant records; do not confuse this with metal recovery rate.
- Cost totals are limited to the categories entered by the user. The prototype does not assume revenue or recycling credits.

**Emission factor references for verification**
- Central Electricity Authority (CEA), CO₂ Baseline Database: https://cea.nic.in/cdm-co2-baseline-database/?lang=en
- IPCC 2006 Guidelines, Volume 2 (Energy): https://www.ipcc-nggip.iges.or.jp/public/2006gl/vol2.html
- NITI Aayog battery recycling ecosystem: https://www.niti.gov.in/node/892

**Boundary limitations**: unless the user enters them, the calculation excludes transport, upstream fuel/electricity supply-chain emissions, chemicals/reagents, wastewater, waste treatment, refrigerant leakage, capital equipment, and avoided virgin-material production credits. Do not describe results as a complete lifecycle assessment.
""")
    st.stop()

demo = mode == "Demo scenario"
# Facility & mass flow
st.sidebar.subheader("1 · Facility & material flow")
facility = st.sidebar.text_input("Facility / scenario name", "Illustrative recycling facility" if demo else "")
input_t = st.sidebar.number_input("Battery input (tonnes/year)", 0.0, 100000.0, 5000.0 if demo else 0.0, 100.0)
capacity_t = st.sidebar.number_input("Rated capacity (tonnes/year)", 0.0, 200000.0, 7500.0 if demo else 0.0, 100.0)
batteries_n = st.sidebar.number_input("Batteries processed (units/year)", 0, 10000000, 25000 if demo else 0, 100)
recycled_t = st.sidebar.number_input("Input mass actually recycled (tonnes/year)", 0.0, 100000.0, 4800.0 if demo else 0.0, 100.0)
recovered_t = st.sidebar.number_input("Total recovered material output (tonnes/year)", 0.0, 100000.0, 4500.0 if demo else 0.0, 50.0)
residue_t = st.sidebar.number_input("Residues / non-recovered output (tonnes/year)", 0.0, 100000.0, 500.0 if demo else 0.0, 50.0)

st.sidebar.subheader("2 · Energy & emissions")
kwh_total = st.sidebar.number_input("Electricity consumed (kWh/year)", 0.0, 200000000.0, 3500000.0 if demo else 0.0, 50000.0)
renew_pct = st.sidebar.slider("Renewable electricity share (%)", 0, 100, 30 if demo else 0)
other_process_emissions = st.sidebar.number_input("Other measured process emissions (tonnes CO₂e/year)", 0.0, 1000000.0, 0.0, 1.0, help="Optional. Enter a documented estimate for included sources not captured above; do not double count electricity or fuels.")
grid_ef = st.sidebar.number_input("Grid emission factor (kg CO₂e/kWh)", 0.0, 3.0, DEFAULT_GRID_EF, 0.01, format="%.3f")

st.sidebar.subheader("3 · Material composition & recovery")
st.sidebar.caption("Composition values are estimated input element mass fractions; recovery rates should be based on recovered element mass / element mass entering the process.")
materials = ["Lithium", "Nickel", "Cobalt", "Copper", "Aluminium", "Graphite"]
composition_defaults = {"Lithium": 4.0, "Nickel": 12.0, "Cobalt": 5.0, "Copper": 8.0, "Aluminium": 7.0, "Graphite": 18.0}
recovery_defaults = {"Lithium": 70.0, "Nickel": 95.0, "Cobalt": 95.0, "Copper": 95.0, "Aluminium": 90.0, "Graphite": 60.0}
composition, recovery_rates = {}, {}
for m in materials:
    composition[m] = st.sidebar.number_input(f"{m} in input (% by mass)", 0.0, 100.0, composition_defaults[m] if demo else 0.0, 0.5, key=f"comp_{m}")
    recovery_rates[m] = st.sidebar.slider(f"{m} recovery rate (%)", 0, 100, int(recovery_defaults[m] if demo else 0), key=f"rec_{m}")

st.sidebar.subheader("4 · Process-stage performance")
st.sidebar.caption("Good output / stage input × 100. Enter stage-specific measured values where available.")
stage_defaults = {"Discharge & dismantling": 96, "Shredding & separation": 92, "Black-mass preparation": 90, "Material extraction / refining": 88, "Purification & finishing": 95}
stage_eff = {}
for stage, val in stage_defaults.items():
    stage_eff[stage] = st.sidebar.slider(f"{stage} efficiency (%)", 0, 100, val if demo else 0, key=f"stage_{stage}")

st.sidebar.subheader("5 · Cost rates (annual costs are calculated)")
st.sidebar.caption("Enter the unit price or operating cost rate. The app calculates annual costs from the activity data above; do not enter annual totals here. This scenario models electricity-powered recycling and excludes diesel/LPG.")
electricity_rate = st.sidebar.number_input("Electricity tariff (₹/kWh)", 0.0, 1000.0, 8.0 if demo else 0.0, 0.1)
chem_cost_per_t = st.sidebar.number_input("Chemicals / reagents (₹/tonne battery input)", 0.0, 1000000.0, 1600.0 if demo else 0.0, 100.0)
labor_cost_per_t = st.sidebar.number_input("Labour & maintenance (₹/tonne battery input)", 0.0, 1000000.0, 2400.0 if demo else 0.0, 100.0)
waste_cost_per_t = st.sidebar.number_input("Residue handling (₹/tonne residue)", 0.0, 1000000.0, 5000.0 if demo else 0.0, 100.0)
other_cost_per_t = st.sidebar.number_input("Other operating costs (₹/tonne battery input)", 0.0, 1000000.0, 0.0, 100.0)
quality = st.sidebar.selectbox("Overall input data quality", ["Illustrative demo", "Measured", "Estimated", "Allocated", "Literature/reference"])
source_note = st.sidebar.text_area("Evidence / source note", "Illustrative values for demonstration; replace with facility records." if demo else "")

# Core calculations
nonrenewable_kwh = kwh_total * (1 - renew_pct / 100)
electricity_kg = nonrenewable_kwh * grid_ef
included_emissions_kg = electricity_kg + other_process_emissions * 1000
emissions_t = included_emissions_kg / 1000
carbon_intensity = included_emissions_kg / input_t if input_t else 0
capacity_util = input_t / capacity_t * 100 if capacity_t else 0
overall_recycling_eff = recycled_t / input_t * 100 if input_t else 0
overall_recovery_rate = recovered_t / input_t * 100 if input_t else 0
mass_balance_gap = input_t - recovered_t - residue_t
# Annual costs are calculated from measured activity quantities and entered unit rates.
electricity_cost = kwh_total * electricity_rate
chem_cost = input_t * chem_cost_per_t
labor_cost = input_t * labor_cost_per_t
waste_cost = residue_t * waste_cost_per_t
other_cost = input_t * other_cost_per_t
annual_cost = electricity_cost + chem_cost + labor_cost + waste_cost + other_cost
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
    {"Emission source":"Grid electricity", "Activity": f"{kwh_total:,.0f} kWh/year", "Included emissions (t CO₂e/year)": electricity_kg/1000},
    {"Emission source":"Other entered process sources", "Activity": f"{other_process_emissions:,.2f} t CO₂e/year", "Included emissions (t CO₂e/year)": other_process_emissions},
])

# Main tabs
overview, material_tab, process_tab, carbon_tab, improve_tab, gemba_tab, report_tab = st.tabs(["🌱 Overview", "🔋 Material recovery", "⚙️ Process performance", "🌍 Carbon footprint", "💡 Improvement planner", "👷 Gemba board", "📊 Data & report"])

with overview:
    st.subheader("Facility performance at a glance")
    if demo: st.info("Demo scenario: all default figures are illustrative. They are not actual data from a recycling facility.")
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
    st.metric("Capacity utilisation", f"{capacity_util:,.2f}%")
    with st.expander("Optional: annual mass-balance check", expanded=False):
        st.caption("Checks whether input mass is accounted for by recovered output plus residues. Useful for data validation, but not a required headline KPI for every presentation.")
        fig = go.Figure(go.Waterfall(name="Annual mass balance", orientation="v", measure=["absolute","relative","total"], x=["Battery input","Recovered + residue","Unaccounted gap"], y=[input_t,-(recovered_t+residue_t),mass_balance_gap], text=[f"{input_t:,.1f} t",f"-{recovered_t+residue_t:,.1f} t",f"{mass_balance_gap:,.1f} t"], connector={"line":{"color":"#8aa39b"}}))
        fig.update_layout(title="Annual mass-balance check", yaxis_title="Tonnes/year", showlegend=False, margin=dict(l=10,r=10,t=55,b=10))
        st.plotly_chart(fig, use_container_width=True)
    if input_t and abs(mass_balance_gap) > max(1.0, input_t*0.02):
        st.warning(f"Mass balance does not close: input minus recovered output and residues = {mass_balance_gap:,.2f} tonnes/year. Check missing streams, moisture basis, stock changes and weighing records.")
    if capacity_t and capacity_util > 100: st.warning("Annual input exceeds rated capacity. Check reporting period, rated capacity and units.")
    st.caption(f"Data quality: {quality}. Evidence: {source_note or 'Not supplied'}")

with material_tab:
    st.subheader("Material recovery and element-specific rates")
    a,b,c = st.columns(3)
    a.metric("Input mass actually recycled", f"{recycled_t:,.2f} tonnes/year")
    b.metric("Overall recycling efficiency", f"{overall_recycling_eff:,.2f}%")
    c.metric("Overall material recovery rate", f"{overall_recovery_rate:,.2f}%")
    st.caption("Overall recycling efficiency here means input mass actually processed for recycling ÷ battery input. Overall material recovery means total recovered output mass ÷ battery input. These definitions are shown explicitly so they are not confused with element-specific recovery rates.")
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
    st.info("Element output tonnages are estimates calculated from the input mass × entered element content × entered recovery rate. Use lab assays, batch mass balances and product certificates to replace the illustrative composition values.")
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
    if input_t and recycled_t > input_t: issues.append(("error","Mass actually recycled exceeds battery input; verify period and units."))
    if recovered_t > recycled_t and recycled_t > 0: issues.append(("warning","Recovered output exceeds mass recycled; check added reagents, moisture basis, stock changes and definitions."))
    if recovered_t + residue_t > input_t*1.02 and input_t>0: issues.append(("warning",f"Recovered material plus residues exceed input by {recovered_t+residue_t-input_t:,.2f} tonnes/year."))
    if any(v < 70 for v in stage_eff.values()): issues.append(("warning","At least one entered process-stage efficiency is below 70%. Investigate losses, contamination, downtime and measurement basis; this is a screening flag, not an industry standard."))
    if kwh_total and input_t and kwh_total/input_t > 1000: issues.append(("warning",f"Electricity intensity is {kwh_total/input_t:,.1f} kWh/tonne. Review route, meters and process boundary; do not treat this as a universal threshold."))
    if not issues: issues.append(("success","No configured screening rule triggered. This does not prove the process is optimal; verify records and stage-level measurements."))
    for typ,msg in issues:
        getattr(st, typ if typ in ("warning","error","success") else "info")(msg)

with carbon_tab:
    st.subheader("Operational carbon footprint calculation")
    st.write("Included sources: purchased electricity adjusted for renewable electricity share, plus any separately measured other process emissions entered by the user. Transport and reverse-logistics emissions are excluded. Diesel and LPG are not included in this electricity-powered recycling scenario.")
    c1,c2,c3 = st.columns(3)
    c1.metric("Total included emissions", f"{emissions_t:,.2f} tonnes CO₂e/year")
    c2.metric("Carbon intensity", f"{carbon_intensity:,.2f} kg CO₂e/tonne input")
    c3.metric("Grid electricity emissions", f"{electricity_kg/1000:,.2f} tonnes CO₂e/year")
    left,right=st.columns([1.15,1])
    with left:
        st.dataframe(emission_df.style.format({"Included emissions (t CO₂e/year)":"{:,.3f}"}), use_container_width=True, hide_index=True)
        st.latex(r"E_{electricity}=kWh\times(1-renewable\ share)\times EF_{grid}")
        st.latex(r"E_{total}=E_{electricity}+E_{other}")
    with right:
        fig=px.bar(emission_df, x="Included emissions (t CO₂e/year)", y="Emission source", orientation="h", color="Emission source", text=emission_df["Included emissions (t CO₂e/year)"].map(lambda x:f"{x:,.2f} t"), title="Where operational emissions come from")
        fig.update_layout(showlegend=False, margin=dict(l=5,r=5,t=55,b=10))
        st.plotly_chart(fig, use_container_width=True)
    st.warning(f"Screening estimate only. Grid factor entered: {grid_ef:.3f} kg CO₂e/kWh. This version includes electricity and optional measured other process emissions only. It excludes on-site fuel combustion, transport, chemicals/reagents lifecycle emissions, wastewater, waste treatment, upstream energy emissions and lifecycle credits unless separately entered. Verify the grid factor and all inputs before formal reporting.")

with improve_tab:
    st.subheader("Improvement planner: facility-specific options")
    st.write("Options below are triggered by the facility values entered in the sidebar. The comparisons are screening estimates, not guaranteed savings; confirm feasibility, quotations and trial results before investment.")
    options = []
    # Conservative screening scenarios. Benefits are tied to relevant input metrics, not user-adjustable sliders.
    if kwh_total > 0 and input_t > 0:
        intensity = kwh_total / input_t
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
        capex = annual_cost * o["capex_pct"]
        elec_saved_kwh = kwh_total * o["saving_pct"] if o["basis"] == "Electricity" else 0.0
        carbon_saved_t = elec_saved_kwh * (1-renew_pct/100) * grid_ef / 1000
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
    st.caption("Only options relevant to entered values are shown. Electricity savings use conservative screening percentages and the entered tariff/grid factor. Yield, residue and data-quality actions are not assigned carbon savings without measured evidence. Implementation costs are rough planning allowances derived from a small percentage of entered annual operating cost—not vendor quotations.")
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
    st.markdown("This is the consolidated reporting area: facility throughput, batteries recycled, recycling efficiency, recovered material, element-specific recovery, process efficiency, electricity use, carbon footprint, calculated annual operating costs, unit costs, and improvement scenarios. Expand each section below to inspect the values and download CSVs or the full report.")
    st.info("Annual costs are calculated automatically from activity × unit rate. This version models electricity-powered recycling and excludes diesel/LPG from both emissions and costs. If the facility uses on-site fuel, its boundary should be expanded and the fuel data added before using this as a full operational inventory.")
    if demo:
        st.warning("This is an illustrative demo scenario, not verified facility data. Replace every assumption with site records before reporting results.")

    # Detailed tables use explicit units in column names so exports remain understandable outside the app.
    overview_df = pd.DataFrame([
        {"Metric":"Facility / scenario", "Value":facility or "Not supplied", "Unit":"name", "Basis":quality},
        {"Metric":"Battery input", "Value":input_t, "Unit":"tonnes/year", "Basis":quality},
        {"Metric":"Batteries processed", "Value":batteries_n, "Unit":"batteries/year", "Basis":quality},
        {"Metric":"Input mass actually recycled", "Value":recycled_t, "Unit":"tonnes/year", "Basis":quality},
        {"Metric":"Overall recycling efficiency", "Value":overall_recycling_eff, "Unit":"% of battery input mass", "Basis":"Calculated: recycled mass / input mass × 100"},
        {"Metric":"Total recovered material output", "Value":recovered_t, "Unit":"tonnes/year", "Basis":quality},
        {"Metric":"Overall mass recovery rate", "Value":overall_recovery_rate, "Unit":"% of battery input mass", "Basis":"Calculated: recovered output / input mass × 100"},
        {"Metric":"Residues / non-recovered output", "Value":residue_t, "Unit":"tonnes/year", "Basis":quality},
        {"Metric":"Mass-balance gap", "Value":mass_balance_gap, "Unit":"tonnes/year", "Basis":"Input − recovered output − residues; investigate non-zero gap"},
        {"Metric":"Rated processing capacity", "Value":capacity_t, "Unit":"tonnes/year", "Basis":quality},
        {"Metric":"Capacity utilisation", "Value":capacity_util, "Unit":"% of rated capacity", "Basis":"Calculated: input / rated capacity × 100"},
    ])
    cost_df = pd.DataFrame([
        {"Cost category":"Electricity", "Activity basis":"kWh/year × ₹/kWh", "Unit rate (₹/unit)":electricity_rate, "Annual cost (₹/year)":electricity_cost},
        {"Cost category":"Chemicals / reagents", "Activity basis":"tonnes input/year × ₹/tonne", "Unit rate (₹/unit)":chem_cost_per_t, "Annual cost (₹/year)":chem_cost},
        {"Cost category":"Labour & maintenance", "Activity basis":"tonnes input/year × ₹/tonne", "Unit rate (₹/unit)":labor_cost_per_t, "Annual cost (₹/year)":labor_cost},
        {"Cost category":"Residue / waste handling", "Activity basis":"tonnes residue/year × ₹/tonne", "Unit rate (₹/unit)":waste_cost_per_t, "Annual cost (₹/year)":waste_cost},
        {"Cost category":"Other operating costs", "Activity basis":"tonnes input/year × ₹/tonne", "Unit rate (₹/unit)":other_cost_per_t, "Annual cost (₹/year)":other_cost},
        {"Cost category":"TOTAL OPERATING COST", "Activity basis":"Sum of calculated annual categories", "Unit rate (₹/unit)":None, "Annual cost (₹/year)":annual_cost},
    ])
    energy_df = pd.DataFrame([
        {"Energy / emission parameter":"Electricity consumed", "Value":kwh_total, "Unit":"kWh/year", "Calculation / note":"User-entered facility activity"},
        {"Energy / emission parameter":"Renewable electricity share", "Value":renew_pct, "Unit":"%", "Calculation / note":"User-entered share; non-renewable electricity is used in grid calculation"},
        {"Energy / emission parameter":"Non-renewable electricity modelled", "Value":nonrenewable_kwh, "Unit":"kWh/year", "Calculation / note":"Total electricity × (1 − renewable share)"},
        {"Energy / emission parameter":"Grid emission factor", "Value":grid_ef, "Unit":"kg CO₂e/kWh", "Calculation / note":"User editable; verify with applicable CEA factor and reporting boundary"},
        {"Energy / emission parameter":"Electricity emissions", "Value":electricity_kg/1000, "Unit":"tonnes CO₂e/year", "Calculation / note":"Non-renewable kWh × grid factor / 1,000"},
        {"Energy / emission parameter":"Other process emissions", "Value":other_process_emissions, "Unit":"tonnes CO₂e/year", "Calculation / note":"Optional user-entered value; avoid double counting"},
        {"Energy / emission parameter":"TOTAL INCLUDED OPERATIONAL FOOTPRINT", "Value":emissions_t, "Unit":"tonnes CO₂e/year", "Calculation / note":"Sum of the included sources above"},
        {"Energy / emission parameter":"Carbon intensity", "Value":carbon_intensity, "Unit":"kg CO₂e/tonne battery input", "Calculation / note":"Included emissions in kg CO₂e / input tonnes"},
    ])
    with st.expander("1 · Facility throughput and recycling KPIs", expanded=True):
        st.dataframe(overview_df, use_container_width=True, hide_index=True)
        st.download_button("Download throughput & KPI data (CSV)", overview_df.to_csv(index=False).encode("utf-8"), "ev_recycling_throughput_kpis.csv", "text/csv")
    with st.expander("2 · Element-by-element recovery data", expanded=True):
        material_report_df = material_df.copy()
        material_report_df["Input composition (%)"] = [composition[m] for m in material_report_df["Material"]]
        material_report_df["Estimated element present in input (tonnes/year)"] = material_report_df["Material"].map(lambda m: input_t * composition[m] / 100)
        material_report_df["Estimated element recovered (tonnes/year)"] = material_report_df["Material"].map(lambda m: input_t * composition[m] / 100 * recovery_rates[m] / 100)
        material_report_df = material_report_df[["Material", "Input composition (%)", "Estimated element present in input (tonnes/year)", "Recovery rate (%)", "Estimated element recovered (tonnes/year)"]]
        st.dataframe(material_report_df.style.format({"Input composition (%)":"{:,.2f}%", "Estimated element present in input (tonnes/year)":"{:,.3f}", "Recovery rate (%)":"{:,.2f}%", "Estimated element recovered (tonnes/year)":"{:,.3f}"}), use_container_width=True, hide_index=True)
        st.caption("Element quantities are estimates based on the composition percentages and recovery rates entered in the sidebar. Validate with battery chemistry records and assays.")
        st.download_button("Download material recovery data (CSV)", material_report_df.to_csv(index=False).encode("utf-8"), "ev_recycling_material_recovery.csv", "text/csv")
    with st.expander("3 · Process-stage efficiency", expanded=True):
        st.dataframe(stage_df.style.format({"Process efficiency (%)":"{:,.2f}%", "Gap to 100% (percentage points)":"{:,.2f} pp"}), use_container_width=True, hide_index=True)
        st.caption("The sidebar efficiencies are entered values, not independently calculated stage yields unless the facility has provided each stage's good output and stage input mass.")
        st.download_button("Download process efficiency data (CSV)", stage_df.to_csv(index=False).encode("utf-8"), "ev_recycling_process_efficiency.csv", "text/csv")
    with st.expander("4 · Energy and carbon footprint calculation", expanded=True):
        st.dataframe(energy_df.style.format({"Value":lambda v: f"{v:,.3f}" if isinstance(v,(int,float)) else str(v)}), use_container_width=True, hide_index=True)
        fig_carbon = px.bar(emission_df, x="Emission source", y="Included emissions (t CO₂e/year)", color="Emission source", text="Included emissions (t CO₂e/year)", title="Annual included operational emissions by source")
        fig_carbon.update_traces(texttemplate="%{text:,.3f} t", textposition="outside", cliponaxis=False)
        fig_carbon.update_layout(showlegend=False, yaxis_title="tonnes CO₂e/year", xaxis_title="", margin=dict(l=10,r=10,t=65,b=10))
        st.plotly_chart(fig_carbon, use_container_width=True)
        st.download_button("Download energy & carbon data (CSV)", energy_df.to_csv(index=False).encode("utf-8"), "ev_recycling_energy_carbon.csv", "text/csv")
    with st.expander("5 · Operating cost breakdown", expanded=True):
        st.dataframe(cost_df.style.format({"Unit rate (₹/unit)":lambda v:"—" if pd.isna(v) else f"₹{v:,.2f}","Annual cost (₹/year)":"₹{:,.2f}"}), use_container_width=True, hide_index=True)
        fig_cost = px.pie(cost_df[cost_df["Cost category"] != "TOTAL OPERATING COST"], names="Cost category", values="Annual cost (₹/year)", hole=0.48, title="Annual operating-cost composition", hover_data={"Annual cost (₹/year)":":,.2f"})
        fig_cost.update_traces(textposition="inside", texttemplate="%{percent:.1%}", hovertemplate="%{label}<br>₹%{value:,.2f}/year<extra></extra>")
        st.plotly_chart(fig_cost, use_container_width=True)
        st.metric("Cost per tonne of battery input", f"₹{cost_per_t:,.2f}/tonne")
        st.metric("Cost per tonne of recovered material", f"₹{cost_per_recovered_t:,.2f}/tonne")
        st.download_button("Download operating cost data (CSV)", cost_df.to_csv(index=False).encode("utf-8"), "ev_recycling_operating_costs.csv", "text/csv")
    with st.expander("6 · Carbon and cost improvement scenarios", expanded=True):
        st.dataframe(result_df.style.format({"Estimated one-time cost (₹)":"₹{:,.2f}", "Potential annual cost saving (₹/year)":"₹{:,.2f}", "Potential carbon reduction (t CO2e/year)":"{:,.3f} t", "Potential carbon reduction (%)":"{:,.2f}%", "Simple payback (years)":lambda x:"Not available" if pd.isna(x) else f"{x:,.2f} years", "Scenario emissions (t CO₂e/year)":"{:,.3f} t"}), use_container_width=True, hide_index=True)
        st.download_button("Download improvement scenarios (CSV)", result_df.to_csv(index=False).encode("utf-8"), "ev_recycling_improvement_scenarios.csv", "text/csv")
    # Full report combines all core sections and preserves units and calculation caveats.
    report = [
        "SUSTAINABLE RECYCLING OF EV BATTERIES — FACILITY DATA REPORT",
        f"Generated date: {date.today().isoformat()}", f"Facility / scenario: {facility or 'Not supplied'}", f"Data quality: {quality}", f"Evidence / source note: {source_note or 'Not supplied'}", "",
        "1. FACILITY THROUGHPUT AND KPIs",
    ]
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
    report += ["", "7. CARBON BOUNDARY AND LIMITATIONS", "Included: grid electricity adjusted for entered renewable share and optional other process emissions entered by the user. This version excludes on-site fuel combustion.", "Excluded unless separately measured/entered: transport, chemical/reagent lifecycle emissions, wastewater treatment, residue treatment, upstream fuel supply, capital goods and avoided virgin-material production credits.", "The electricity factor and default fuel factors are screening assumptions and must be checked against current, documented, location-appropriate sources. This report is not a verified GHG inventory or full lifecycle assessment.", "Mass-balance gap = battery input − recovered output − residues. A non-zero result requires reconciliation; definitions and boundaries may differ by facility."]
    st.download_button("Download complete facility report (TXT)", "\n".join(report).encode("utf-8"), "sustainable_ev_battery_recycling_full_report.txt", "text/plain")
    st.caption("Every report section is downloadable separately as CSV. The complete TXT report consolidates throughput, element recovery, process efficiency, energy/emissions, cost and improvement estimates with units and limitations.")
