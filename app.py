import streamlit as st
import numpy as np
import plotly.express as px
import pandas as pd
from itertools import combinations

st.set_page_config(page_title="Political Stability Simulator", layout="wide")

# --- CUSTOM CSS FOR COMPACT FIT ---
st.markdown("""
    <style>
        .block-container { padding-top: 1.rem; padding-bottom: 0rem; }
        h1 { font-size: 1.8rem !important; margin-bottom: 0px !important; }
        p { margin-bottom: 0.5rem !important; }
    </style>
""", unsafe_allow_html=True)

# --- APP HEADER ---
st.setTitle = st.title("🏛️ The Political Stability Simulator")
st.markdown("*Exploring the **Political Impossibility Theorem** & **Stability-Dictatorship Dichotomy**.*")

# --- SIDEBAR SETUP ---
st.sidebar.header("Parliament Config")
total_seats = st.sidebar.number_input("Total Seats", min_value=10, max_value=600, value=80, step=1)
q = (total_seats // 2) + 1
tau = st.sidebar.slider("Tolerance ($\tau$)", min_value=1.0, max_value=200.0, value=25.0)

num_parties = st.sidebar.number_input("Parties", min_value=2, max_value=8, value=3, step=1)

default_names = ["Party A", "Party B", "Party C", "Party D", "Party E", "Party F"]
default_weights = [30, 30, 20, 10, 5, 5]
default_locs = [0.0, 50.0, 100.0, 25.0, 75.0, 50.0]
default_colors = ["#ff3333", "#3399ff", "#33cc33", "#ff9933", "#9933ff", "#ffff33"]

names, weights, locs, colors = [], [], [], []
for i in range(num_parties):
    c1, c2, c3 = st.sidebar.columns([2, 1, 1])
    with c1:
        name = st.text_input(f"P{i+1} Name", value=default_names[i], key=f"name_{i}")
    with c2:
        w = st.number_input(f"P{i+1} Seats", min_value=0, max_value=total_seats, value=default_weights[i] if i<3 else 5, key=f"w_{i}")
    with c3:
        col = st.color_picker(f"P{i+1} Col", value=default_colors[i], key=f"col_{i}")
    l = st.sidebar.slider(f"P{i+1} Ideology Loc", min_value=0.0, max_value=100.0, value=default_locs[i], key=f"l_{i}")
    
    names.append(name)
    weights.append(w)
    locs.append(l)
    colors.append(col)

assigned_seats = sum(weights)

# --- TRUE HEMICYCLE GENERATOR (LEFT-TO-RIGHT PARLIAMENT SWEEP) ---
def generate_hemicycle_data(party_names, party_weights, party_colors):
    total = sum(party_weights)
    if total <= 0:
        return pd.DataFrame(columns=["x", "y", "Party", "Color"])
    
    # Flatten seats into a single continuous list in the exact order user inputted them
    seat_party = []
    seat_color = []
    for name, w, col in zip(party_names, party_weights, party_colors):
        for _ in range(w):
            seat_party.append(name)
            seat_color.append(col)
            
    # Calculate concentric arc rows
    num_rows = max(3, int(np.ceil(np.sqrt(total / 2))))
    radii = [4.0 + i * 1.8 for i in range(num_rows)]
    arc_lengths = [r * np.pi for r in radii]
    total_arc = sum(arc_lengths)
    
    seats_per_row = [int(total * (al / total_arc)) for al in arc_lengths]
    diff = total - sum(seats_per_row)
    if num_rows > 0:
        seats_per_row[-1] += diff
        
    points = []
    seat_idx = 0
    # Fill rows from inner-most arc to outer-most arc
    for r_idx, r in enumerate(radii):
        count = seats_per_row[r_idx]
        if count <= 0:
            continue
        # Sweep angle from left (pi) to right (0) so leftmost seats sit on the left flank
        angles = np.linspace(np.pi, 0, count)
        for angle in angles:
            if seat_idx < len(seat_party):
                x = r * np.cos(angle)
                y = r * np.sin(angle)
                points.append({
                    "x": x, "y": y,
                    "Party": seat_party[seat_idx],
                    "Color": seat_color[seat_idx]
                })
                seat_idx += 1
                
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

# --- MAIN DASHBOARD (SINGLE SCREEN LAYOUT) ---
col_left, col_right = st.columns([1.2, 1])

with col_left:
    st.subheader("🏛️ Parliament Chamber")
    df_seats = generate_hemicycle_data(names, weights, colors)
    
    if not df_seats.empty:
        color_map = dict(zip(names, colors))
        fig = px.scatter(
            df_seats, x="x", y="y", color="Party",
            color_discrete_map=color_map, height=300
        )
        fig.update_traces(marker=dict(size=11, line=dict(width=0.4, color='white')))
        fig.update_layout(
            xaxis=dict(visible=False, showgrid=False, zeroline=False),
            yaxis=dict(visible=False, showgrid=False, zeroline=False),
            margin=dict(t=10, b=10, l=10, r=10),
            legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5, font=dict(size=10))
        )
        fig.add_annotation(x=0, y=0.3, text=str(assigned_seats), showarrow=False, font=dict(size=28, family="Arial, bold", color="white"))
        st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("📊 System Status")
    c_m1, c_m2 = st.columns(2)
    c_m1.metric("Quota ($q$)", f"{q}")
    c_m2.metric("Viable Coalitions", len(viable_coalitions))
    
    veto_players = []
    for i in range(num_parties):
        is_veto = all(i in c for c in viable_coalitions) if viable_coalitions else False
        if viable_coalitions and is_veto:
            veto_players.append(names[i])
            
    if veto_players:
        st.success(f"🛡️ **Veto Player:** {', '.join(veto_players)} (Core Non-Empty)")
    else:
        st.warning("⚠️ **No Veto Player!** (Core is **Empty** - Instability)")

# --- COALITION TESTER ---
st.markdown("---")
st.subheader("🤝 Test Government Coalition")
selected_parties = st.multiselect("Select cabinet parties:", options=names, default=names[:min(2, num_parties)])

if selected_parties:
    sel_indices = [names.index(p) for p in selected_parties]
    w_sum = get_weight(sel_indices)
    cost = get_cost(sel_indices)
    viable = is_viable(sel_indices)
    
    rc1, rc2, rc3 = st.columns(3)
    rc1.metric("Seats", f"{w_sum} / {q}")
    rc2.metric("Ideological Cost", f"{cost:.1f} (max {tau})")
    
    if viable:
        rc3.metric("Status", "VIABLE 🟢")
    else:
        rc3.metric("Status", "BLOCKED 🔴")
