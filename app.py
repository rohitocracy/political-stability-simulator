import streamlit as st
import numpy as np
import plotly.express as px
import pandas as pd
from itertools import combinations

st.set_page_config(page_title="Political Stability Simulator", layout="wide")

# --- APP HEADER ---
st.title("🏛️ The Political Stability Simulator")
st.markdown("""
*An interactive exploration of the **Political Impossibility Theorem** and the **Stability-Dictatorship Dichotomy**.*  
Adjust party weights, ideological locations, and tolerance ($\tau$) to see why stable governments are mathematically hard to form.
""")

# --- SIDEBAR: SCENARIO PRESETS & CONTROLS ---
st.sidebar.header("Configuration")
scenario = st.sidebar.selectbox(
    "Choose a Preset Scenario",
    [
        "Custom Sandbox",
        "1. The Impossibility Theorem (3-Player Symmetric)",
        "2. The Cordon Sanitaire (Extremist Penalty)",
        "3. Centrist Veto Block"
    ]
)

if scenario == "1. The Impossibility Theorem (3-Player Symmetric)":
    default_names = ["Party A", "Party B", "Party C"]
    default_weights = [1, 1, 1]
    default_locs = [0.0, 0.0, 0.0]
    default_q = 2
    default_tau = 1.0
elif scenario == "2. The Cordon Sanitaire (Extremist Penalty)":
    default_names = ["Centrist A", "Centrist B", "Extremist C"]
    default_weights = [30, 30, 40]
    default_locs = [0.0, 15.0, 100.0]
    default_q = 51
    default_tau = 20.0
elif scenario == "3. Centrist Veto Block":
    default_names = ["Party A", "Party B", "Party C"]
    default_weights = [40, 30, 30]
    default_locs = [0.0, 50.0, 100.0]
    default_q = 51
    default_tau = 10.0
else:
    default_names = ["Party A", "Party B", "Party C"]
    default_weights = [30, 30, 20]
    default_locs = [10.0, 30.0, 90.0]
    default_q = 51
    default_tau = 25.0

# Parliament Parameters
n_parties = len(default_names)
st.sidebar.subheader("Parliament Rules")
q = st.sidebar.slider("Majority Quota ($q$)", min_value=1, max_value=100, value=default_q)
tau = st.sidebar.slider("Ideological Tolerance ($\tau$)", min_value=1.0, max_value=100.0, value=default_tau)

st.sidebar.subheader("Party Details")
names, weights, locs = [], [], []
for i in range(n_parties):
    col1, col2, col3 = st.sidebar.columns(3)
    with col1:
        name = st.text_input(f"Name {i+1}", value=default_names[i], key=f"name_{i}")
    with col2:
        w = st.number_input(f"Seats {i+1}", min_value=1, max_value=100, value=default_weights[i], key=f"w_{i}")
    with col3:
        l = st.number_input(f"Loc {i+1}", min_value=-50.0, max_value=150.0, value=default_locs[i], key=f"l_{i}")
    names.append(name)
    weights.append(w)
    locs.append(l)

# --- BACKEND MATHEMATICAL LOGIC ($v_\tau$ game) ---
total_seats = sum(weights)

def get_cost(coalition_indices):
    if not coalition_indices:
        return 0.0
    sub_locs = [locs[i] for i in coalition_indices]
    return max(sub_locs) - min(sub_locs)

def get_weight(coalition_indices):
    return sum(weights[i] for i in coalition_indices)

def is_viable(coalition_indices):
    if not coalition_indices:
        return False
    w_sum = get_weight(coalition_indices)
    cost = get_cost(coalition_indices)
    return (w_sum >= q) and (cost <= tau)

# Find all subsets
indices = list(range(n_parties))
viable_coalitions = []
for r in range(1, n_parties + 1):
    for comb in combinations(indices, r):
        if is_viable(comb):
            viable_coalitions.append(comb)

has_grand = is_viable(tuple(indices))

# --- VISUALIZATION DASHBOARD ---
col_left, col_right = st.columns([1.5, 1])

with col_left:
    st.subheader("🗺️ Ideological Spectrum & Seat Weights")
    df_parties = pd.DataFrame({
        "Party": names,
        "Seats": weights,
        "Location": locs
    })
    
    # Plotly Visualisation of Parliament
    fig = px.scatter(
        df_parties, x="Location", y=[1]*n_parties, size="Seats", color="Party",
        text="Party", range_x=[-10, 110], height=250,
        labels={"Location": "Ideological Axis (Left to Right)", "y": ""}
    )
    fig.update_traces(textposition='top center', marker=dict(opacity=0.8))
    fig.update_yaxes(visible=False, showticklabels=False)
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("📊 Parliament Status")
    st.metric("Total Seats", total_seats)
    st.metric("Viable Coalitions Found", len(viable_coalitions))
    
    # Check Veto Players
    veto_players = []
    for i in range(n_parties):
        is_veto = True
        for c in viable_coalitions:
            if i not in c:
                is_veto = False
                break
        if viable_coalitions and is_veto:
            veto_players.append(names[i])
            
    if veto_players:
        st.success(f"🛡️ **Veto Player(s) Detected:** {', '.join(veto_players)}")
        st.info("Because a veto player exists, the Core is **Non-Empty** (Stable, but power is concentrated).")
    else:
        st.warning("⚠️ **No Veto Player Detected!**")
        st.error("The Core is **Empty**! This system suffers from **Political Instability** (Theorem 4.1).")

st.markdown("---")

# --- COALITION EXPLORER ---
st.subheader("🤝 Test a Proposed Government Coalition")
selected_parties = st.multiselect("Select parties to form a government:", options=names, default=names[:min(2, n_parties)])

if selected_parties:
    sel_indices = [names.index(p) for p in selected_parties]
    w_sum = get_weight(sel_indices)
    cost = get_cost(sel_indices)
    viable = is_viable(sel_indices)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Coalition Weight", f"{w_sum} / {q} required")
    c2.metric("Ideological Cost", f"{cost:.1f} (max tol: {tau})")
    
    if viable:
        c3.metric("Status", "VIABLE 🟢", delta="Government Formed")
        st.success(f"The coalition **{', '.join(selected_parties)}** meets both Majority Rule and Ideological Coherence!")
    else:
        c3.metric("Status", "FAILED 🔴", delta="Blocked", delta_color="inverse")
        if w_sum < q:
            st.warning("Reason for failure: **Seat Shortfall** (Does not meet majority quota $q$).")
        elif cost > tau:
            st.warning("Reason for failure: **Ideological Incoherence** (Cost exceeds tolerance $\tau$).")
