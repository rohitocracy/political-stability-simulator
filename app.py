import streamlit as st
import numpy as np
import pandas as pd
from itertools import combinations

st.set_page_config(page_title="Political Stability Simulator", layout="wide")

# --- ULTRA-COMPACT CSS ---
st.markdown("""
    <style>
        .block-container { padding-top: 1rem; padding-bottom: 0rem; padding-left: 2rem; padding-right: 2rem; }
        h1 { font-size: 1.6rem !important; margin-bottom: -10px !important; }
        h3 { font-size: 1.1rem !important; margin-top: 0px !important; margin-bottom: 0px !important; }
        p { margin-bottom: 0.3rem !important; font-size: 0.9rem !important; }
        div.stMetric { background-color: #1e1e1e; padding: 6px; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- APP HEADER ---
st.title("🏛️ The Political Stability Simulator")
st.markdown("Exploring the **Political Impossibility Theorem** & **Stability-Dictatorship Dichotomy**.")

# --- SIDEBAR CONFIGURATION ---
st.sidebar.header("Parliament Config")
total_seats = st.sidebar.number_input("Total Seats", min_value=10, max_value=600, value=100, step=1)
q = (total_seats // 2) + 1
tau = st.sidebar.slider("Tolerance ($\tau$)", min_value=1.0, max_value=200.0, value=25.0)

num_parties = st.sidebar.number_input("Parties", min_value=3, max_value=10, value=3, step=1)

default_names = ["Party A", "Party B", "Party C", "Party D", "Party E", "Party F", "Party G", "Party H", "Party I", "Party J"]
default_weights = [40, 40, 20, 0, 0, 0, 0, 0, 0, 0]
default_locs = [20.0, 80.0, 50.0, 10.0, 90.0, 30.0, 70.0, 40.0, 60.0, 50.0]

# Safe collection loop
names, weights, locs = [], [], []
remaining_seats = total_seats

for i in range(num_parties):
    c1, c2 = st.sidebar.columns([2, 1])
    with c1:
        name = st.text_input(f"P{i+1} Name", value=default_names[i], key=f"name_{i}")
        default_w = default_weights[i] if i < len(default_weights) else 0
        w = st.number_input(f"P{i+1} Seats", min_value=0, max_value=total_seats, value=default_w, key=f"w_{i}")
    with c2:
        default_l = default_locs[i] if i < len(default_locs) else 50.0
        l = st.slider(f"P{i+1} Loc", min_value=0.0, max_value=100.0, value=default_l, key=f"l_{i}")
    
    names.append(name)
    weights.append(w)
    locs.append(l)

# Auto-balance seats to match total cleanly
assigned_seats = sum(weights)
if assigned_seats != total_seats:
    diff = total_seats - assigned_seats
    weights[-1] = max(0, weights[-1] + diff)
    assigned_seats = sum(weights)
    st.sidebar.info(f"ℹ️ Seats balanced: '{names[-1]}' adjusted to match Total Seats ({total_seats}).")

# --- BACKEND GAME LOGIC ($v_\tau$) ---
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
    return (get_weight(coalition_indices) >= q) and (get_cost(coalition_indices) <= tau)

indices = list(range(num_parties))
viable_coalitions = []
for r in range(1, num_parties + 1):
    for comb in combinations(indices, r):
        if is_viable(comb):
            viable_coalitions.append(comb)

# --- DASHBOARD LAYOUT ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 System Status")
    mc1, mc2, mc3 = st.columns(3)
    mc1.metric("Total Seats", assigned_seats)
    mc2.metric("Quota ($q$)", f"{q}")
    mc3.metric("Viable Coal.", len(viable_coalitions))
    
    veto_players = []
    for i in range(num_parties):
        is_veto = all(i in c for c in viable_coalitions) if viable_coalitions else False
        if viable_coalitions and is_veto:
            veto_players.append(names[i])
            
    if veto_players:
        st.success(f"🛡️ **Veto Player(s) Detected:** {', '.join(veto_players)}")
        st.info("The Core is **Non-Empty** (Stable, but power is concentrated).")
    else:
        st.warning("⚠️ **No Veto Player Detected!**")
        st.error("The Core is **Empty**! System suffers from **Political Instability**.")

with col2:
    st.subheader("🤝 Test Government Coalition")
    selected_parties = st.multiselect("Select cabinet parties:", options=names, default=names[:min(2, num_parties)])

    if selected_parties:
        sel_indices = [names.index(p) for p in selected_parties]
        w_sum = get_weight(sel_indices)
        cost = get_cost(sel_indices)
        viable = is_viable(sel_indices)
        
        tc1, tc2, tc3 = st.columns(3)
        tc1.metric("Seats", f"{w_sum} / {q}")
        tc2.metric("Ideological Cost", f"{cost:.1f} (max {tau})")
        
        if viable:
            tc3.metric("Status", "VIABLE 🟢")
            st.success(f"Coalition **{', '.join(selected_parties)}** successfully forms a government.")
        else:
            tc3.metric("Status", "BLOCKED 🔴")
            if w_sum < q:
                st.warning("Failure Reason: Seat Shortfall (< Quota $q$).")
            elif cost > tau:
                st.warning("Failure Reason: Ideological Incoherence (> Tolerance $\tau$).")
