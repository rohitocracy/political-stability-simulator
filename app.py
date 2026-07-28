import streamlit as st
import numpy as np
import plotly.express as px
import pandas as pd
from itertools import combinations

st.set_page_config(page_title="Political Stability Simulator", layout="wide")

# --- ULTRA-COMPACT CSS ---
st.markdown("""
    <style>
        .block-container { padding-top: 0.8rem; padding-bottom: 0rem; padding-left: 1rem; padding-right: 1rem; }
        h1 { font-size: 1.4rem !important; margin-bottom: -10px !important; }
        h3 { font-size: 1.0rem !important; margin-top: 0px !important; margin-bottom: 0px !important; }
        p { margin-bottom: 0.2rem !important; font-size: 0.85rem !important; }
        div.stMetric { background-color: #1e1e1e; padding: 4px; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- APP HEADER ---
st.title("🏛️ The Political Stability Simulator")
st.markdown("Exploring the **Political Impossibility Theorem** & **Stability-Dictatorship Dichotomy**.")

# --- SIDEBAR CONFIGURATION ---
st.sidebar.header("Parliament Config")
total_seats = st.sidebar.number_input("Total Seats", min_value=10, max_value=500, value=100, step=1)
q = (total_seats // 2) + 1
tau = st.sidebar.slider("Tolerance ($\tau$)", min_value=1.0, max_value=200.0, value=25.0)

num_parties = st.sidebar.number_input("Parties", min_value=2, max_value=10, value=3, step=1)

default_names = ["Party A", "Party B", "Party C", "Party D", "Party E", "Party F", "Party G", "Party H", "Party I", "Party J"]
default_weights = [40, 40, 20, 0, 0, 0, 0, 0, 0, 0]
default_locs = [20.0, 80.0, 50.0, 10.0, 90.0, 30.0, 70.0, 40.0, 60.0, 50.0]
default_colors = ["#3366ff", "#ff3333", "#33cc33", "#ff9933", "#9933ff", "#ffff33", "#ff66cc", "#999999", "#666666", "#00ffff"]

names, weights, locs, colors = [], [], [], []
for i in range(num_parties):
    c1, c2, c3 = st.sidebar.columns([2, 1, 1])
    with c1:
        name = st.text_input(f"P{i+1}", value=default_names[i], key=f"name_{i}")
    with c2:
        w = st.number_input(f"Seats", min_value=0, max_value=total_seats, value=default_weights[i], key=f"w_{i}")
    with c3:
        col = st.color_picker(f"Col", value=default_colors[i], key=f"col_{i}")
    l = st.sidebar.slider(f"P{i+1} Ideology", min_value=0.0, max_value=100.0, value=default_locs[i], key=f"l_{i}")
    
    names.append(name)
    weights.append(w)
    locs.append(l)
    colors.append(col)

assigned_seats = sum(weights)

# --- CLEAN RECTANGULAR GRID LAYOUT ENGINE ---
def generate_rectangle_data(party_names, party_weights, party_colors, party_locs):
    total = sum(party_weights)
    if total <= 0:
        return pd.DataFrame(columns=["x", "y", "Party", "Color"])
    
    # Sort parties left-to-right by ideology
    sorted_indices = np.argsort(party_locs)
    s_names = [party_names[i] for i in sorted_indices]
    s_weights = [party_weights[i] for i in sorted_indices]
    s_colors = [party_colors[i] for i in sorted_indices]
    
    # Build a clean grid (e.g., 10 seats per row)
    cols_per_row = 10
    points = []
    
    current_seat = 0
    for name, w, col in zip(s_names, s_weights, s_colors):
        for _ in range(w):
            r = current_seat // cols_per_row
            c = current_seat % cols_per_row
            points.append({
                "x": c,
                "y": -r, # stack downward cleanly in a rectangle
                "Party": name,
                "Color": col
            })
            current_seat += 1
            
    return pd.DataFrame(points)

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
col_left, col_right = st.columns([1.3, 1])

with col_left:
    st.subheader("🏛️ Parliament Grid (Rectangle)")
    df_seats = generate_rectangle_data(names, weights, colors, locs)
    
    if not df_seats.empty:
        color_map = dict(zip(names, colors))
        fig = px.scatter(
            df_seats, x="x", y="y", color="Party",
            color_discrete_map=color_map, height=260
        )
        fig.update_traces(marker=dict(size=14, line=dict(width=0.2, color='white')))
        fig.update_layout(
            xaxis=dict(visible=False, showgrid=False, zeroline=False),
            yaxis=dict(visible=False, showgrid=False, zeroline=False),
            margin=dict(t=10, b=10, l=10, r=10),
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5, font=dict(size=9))
        )
        st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("📊 System Status")
    rc1, rc2 = st.columns(2)
    rc1.metric("Quota ($q$)", f"{q}")
    rc2.metric("Viable Coal.", len(viable_coalitions))
    
    veto_players = []
    for i in range(num_parties):
        is_veto = all(i in c for c in viable_coalitions) if viable_coalitions else False
        if viable_coalitions and is_veto:
            veto_players.append(names[i])
            
    if veto_players:
        st.success(f"🛡️ **Veto:** {', '.join(veto_players)}")
    else:
        st.warning("⚠️ **No Veto! (Empty Core)**")

# --- COALITION TESTER ---
st.markdown("---")
st.subheader("🤝 Test Government Coalition")
selected_parties = st.multiselect("Cabinet parties:", options=names, default=names[:min(2, num_parties)])

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
    else:
        tc3.metric("Status", "BLOCKED 🔴")
