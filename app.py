import streamlit as st
import numpy as np
import plotly.express as px
import pandas as pd
from itertools import combinations

st.set_page_config(page_title="Political Stability Simulator", layout="wide")

# --- APP HEADER ---
st.title("🏛️ The Political Stability Simulator & Hemicycle")
st.markdown("""
*An interactive exploration of the **Political Impossibility Theorem** and the **Stability-Dictatorship Dichotomy**.*  
Adjust parliament structure, party seats, colors, and ideological tolerance ($\tau$) to simulate chamber dynamics and core stability.
""")

# --- SIDEBAR: CONFIGURATION ---
st.sidebar.header("Parliament Structure")
total_seats = st.sidebar.number_input("Total Parliament Seats", min_value=10, max_value=600, value=80, step=1)
q = (total_seats // 2) + 1
st.sidebar.metric("Calculated Majority Quota ($q$)", f"{q} (Strict Majority)")
tau = st.sidebar.slider("Ideological Tolerance ($\tau$)", min_value=1.0, max_value=200.0, value=25.0)

st.sidebar.header("Political Parties Setup")
num_parties = st.sidebar.number_input("Number of Parties", min_value=2, max_value=10, value=3, step=1)

default_names = ["Party A", "Party B", "Party C", "Party D", "Party E", "Party F", "Party G", "Party H", "Party I", "Party J"]
default_weights = [30, 30, 20, 10, 5, 5, 5, 5, 5, 5]
default_locs = [0.0, 30.0, 90.0, 45.0, 10.0, 70.0, 20.0, 60.0, 80.0, 100.0]
default_colors = ["#ff3333", "#ff9933", "#3399ff", "#33cc33", "#9933ff", "#ffff33", "#ff66cc", "#999999", "#666666", "#000000"]

names, weights, locs, colors = [], [], [], []
for i in range(num_parties):
    st.sidebar.markdown(f"**Party {i+1}**")
    c1, c2 = st.sidebar.columns(2)
    with c1:
        name = st.text_input(f"Name {i+1}", value=default_names[i], key=f"name_{i}")
        w = st.number_input(f"Seats {i+1}", min_value=0, max_value=total_seats, value=default_weights[i] if i < 3 else 5, key=f"w_{i}")
    with c2:
        l = st.number_input(f"Loc {i+1}", min_value=-50.0, max_value=150.0, value=default_locs[i], key=f"l_{i}")
        col = st.color_picker(f"Color {i+1}", value=default_colors[i], key=f"col_{i}")
    
    names.append(name)
    weights.append(w)
    locs.append(l)
    colors.append(col)

assigned_seats = sum(weights)
if assigned_seats != total_seats:
    st.sidebar.warning(f"⚠️ Assigned seats sum to **{assigned_seats}**, but Total Parliament Seats is **{total_seats}**.")

# --- PROPER LEFT-TO-RIGHT HEMICYCLE GENERATOR ---
def generate_hemicycle_data(party_names, party_weights, party_colors, party_locs):
    """Sorts parties left-to-right by ideology and arranges seats cleanly along arcs."""
    # 1. Sort parties by ideological location (Left to Right)
    sorted_indices = np.argsort(party_locs)
    sorted_names = [party_names[i] for i in sorted_indices]
    sorted_weights = [party_weights[i] for i in sorted_indices]
    sorted_colors = [party_colors[i] for i in sorted_indices]
    
    total = sum(sorted_weights)
    if total <= 0:
        return pd.DataFrame(columns=["x", "y", "Party", "Color"])
    
    # 2. Design concentric rows for the hemicycle
    num_rows = max(3, int(np.ceil(np.sqrt(total / 2))))
    radii = [5.0 + i * 2.0 for i in range(num_rows)]
    arc_lengths = [r * np.pi for r in radii]
    total_arc = sum(arc_lengths)
    
    seats_per_row = [int(total * (al / total_arc)) for al in arc_lengths]
    diff = total - sum(seats_per_row)
    if num_rows > 0:
        seats_per_row[-1] += diff
        
    # Build continuous list of seats ordered from political Left to Right
    seat_party = []
    seat_color = []
    for name, w, col in zip(sorted_names, sorted_weights, sorted_colors):
        for _ in range(w):
            seat_party.append(name)
            seat_color.append(col)
            
    # Place seats along arcs from left angle (pi) to right angle (0)
    points = []
    seat_idx = 0
    for r_idx, r in enumerate(radii):
        count = seats_per_row[r_idx]
        if count <= 0:
            continue
        angles = np.linspace(np.pi, 0, count) # Left to right sweep
        for angle in angles:
            if seat_idx < len(seat_party):
                x = r * np.cos(angle)
                y = r * np.sin(angle)
                points.append({
                    "x": x,
                    "y": y,
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
    w_sum = get_weight(coalition_indices)
    cost = get_cost(coalition_indices)
    return (w_sum >= q) and (cost <= tau)

indices = list(range(num_parties))
viable_coalitions = []
for r in range(1, num_parties + 1):
    for comb in combinations(indices, r):
        if is_viable(comb):
            viable_coalitions.append(comb)

# --- LAYOUT DASHBOARD ---
col_left, col_right = st.columns([1.5, 1])

with col_left:
    st.subheader("🏛️ Parliamentary Hemicycle Chamber (Left to Right)")
    df_seats = generate_hemicycle_data(names, weights, colors, locs)
    
    if not df_seats.empty:
        color_map = dict(zip(names, colors))
        fig = px.scatter(
            df_seats, x="x", y="y", color="Party",
            color_discrete_map=color_map,
            hover_name="Party", height=400
        )
        fig.update_traces(marker=dict(size=13, line=dict(width=0.6, color='white')))
        fig.update_layout(
            xaxis=dict(visible=False, showgrid=False, zeroline=False),
            yaxis=dict(visible=False, showgrid=False, zeroline=False),
            margin=dict(t=20, b=20, l=20, r=20),
            legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5)
        )
        fig.add_annotation(x=0, y=0.5, text=str(assigned_seats), showarrow=False, font=dict(size=32, family="Arial, bold", color="white"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Assign seats to render the hemicycle chamber.")

with col_right:
    st.subheader("📊 Parliament Stability Status")
    st.metric("Total Seats Assigned", assigned_seats)
    st.metric("Viable Government Coalitions", len(viable_coalitions))
    
    # Check Veto Players
    veto_players = []
    for i in range(num_parties):
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
selected_parties = st.multiselect("Select parties to form a cabinet coalition:", options=names, default=names[:min(2, num_parties)])

if selected_parties:
    sel_indices = [names.index(p) for p in selected_parties]
    w_sum = get_weight(sel_indices)
    cost = get_cost(sel_indices)
    viable = is_viable(sel_indices)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Coalition Seats", f"{w_sum} / {q} required")
    c2.metric("Ideological Cost", f"{cost:.1f} (max tol: {tau})")
    
    if viable:
        c3.metric("Status", "VIABLE 🟢", delta="Government Formed")
        st.success(f"The coalition **{', '.join(selected_parties)}** successfully meets both Majority Rule ($W(S) \ge q$) and Ideological Coherence ($Cost(S) \le \tau$)!")
    else:
        c3.metric("Status", "FAILED 🔴", delta="Blocked", delta_color="inverse")
        if w_sum < q:
            st.warning("Reason for failure: **Seat Shortfall** (Does not meet majority quota $q$).")
        elif cost > tau:
            st.warning("Reason for failure: **Ideological Incoherence** (Cost exceeds tolerance $\tau$). Parties are too far apart on the political spectrum.")
