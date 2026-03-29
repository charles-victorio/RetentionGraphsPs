import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# --- Fake data ---
data = pd.DataFrame([
    ("Math",       "Physics",     "Math & Physics",   "STEM", "Physics",     "Physics",     "Math & Physics",   "STEM", 12),
    ("Math",       "Physics",     "Math & Physics",   "STEM", "Math",        "Physics",     "Math & Physics",   "STEM", 40),
    ("Math",       "Physics",     "Math & Physics",   "STEM", "Chemistry",   "Chemistry",   "Natural Sciences", "STEM", 8),
    ("Math",       "Physics",     "Math & Physics",   "STEM", "English",     "Humanities",  "Arts & Letters",   "Non-STEM", 5),
    ("Physics",    "Physics",     "Math & Physics",   "STEM", "Math",        "Physics",     "Math & Physics",   "STEM", 15),
    ("Physics",    "Physics",     "Math & Physics",   "STEM", "CS",          "CS",          "Engineering",      "STEM", 20),
    ("Chemistry",  "Chemistry",   "Natural Sciences", "STEM", "Biology",     "Biology",     "Natural Sciences", "STEM", 18),
    ("Chemistry",  "Chemistry",   "Natural Sciences", "STEM", "Chemistry",   "Chemistry",   "Natural Sciences", "STEM", 30),
    ("Biology",    "Biology",     "Natural Sciences", "STEM", "Chemistry",   "Chemistry",   "Natural Sciences", "STEM", 10),
    ("Biology",    "Biology",     "Natural Sciences", "STEM", "Nursing",     "Health Sci",  "Health",           "STEM", 22),
    ("CS",         "CS",          "Engineering",      "STEM", "Math",        "Physics",     "Math & Physics",   "STEM", 6),
    ("CS",         "CS",          "Engineering",      "STEM", "CS",          "CS",          "Engineering",      "STEM", 50),
    ("English",    "Humanities",  "Arts & Letters",   "Non-STEM", "English", "Humanities",  "Arts & Letters",   "Non-STEM", 35),
    ("English",    "Humanities",  "Arts & Letters",   "Non-STEM", "History", "Humanities",  "Arts & Letters",   "Non-STEM", 10),
    ("History",    "Humanities",  "Arts & Letters",   "Non-STEM", "English", "Humanities",  "Arts & Letters",   "Non-STEM", 8),
    ("History",    "Humanities",  "Arts & Letters",   "Non-STEM", "Poli Sci","Social Sci",  "Social Sciences",  "Non-STEM", 14),
    ("Poli Sci",   "Social Sci",  "Social Sciences",  "Non-STEM", "History", "Humanities",  "Arts & Letters",   "Non-STEM", 7),
    ("Poli Sci",   "Social Sci",  "Social Sciences",  "Non-STEM", "Poli Sci","Social Sci",  "Social Sciences",  "Non-STEM", 28),
    ("Economics",  "Social Sci",  "Social Sciences",  "Non-STEM", "Math",    "Physics",     "Math & Physics",   "STEM", 9),
    ("Economics",  "Social Sci",  "Social Sciences",  "Non-STEM", "Economics","Social Sci", "Social Sciences",  "Non-STEM", 33),
], columns=[
    "start_major", "start_dept", "start_division", "start_stem",
    "end_major",   "end_dept",   "end_division",   "end_stem",
    "count"
])

LEVELS = ["Major", "Department", "Division", "STEM/Non-STEM"]
level_to_col = {
    "start": {"Major": "start_major", "Department": "start_dept", "Division": "start_division", "STEM/Non-STEM": "start_stem"},
    "end":   {"Major": "end_major",   "Department": "end_dept",   "Division": "end_division",   "STEM/Non-STEM": "end_stem"},
}

# --- UI ---
st.title("Major Retention Flow")

# Grouping controls
col1, col2 = st.columns(2)
with col1:
    left_level = st.selectbox("Group starting majors by", LEVELS, index=1)
with col2:
    right_level = st.selectbox("Group ending majors by", LEVELS, index=1)

st.divider()

# Cascading filter in sidebar
st.sidebar.header("Filter starting from...")

all_colleges = sorted(data["start_division"].unique())
selected_division = st.sidebar.selectbox("Division", ["All"] + all_colleges)

filtered = data.copy()
if selected_division != "All":
    filtered = filtered[filtered["start_division"] == selected_division]
    all_depts = sorted(filtered["start_dept"].unique())
    selected_dept = st.sidebar.selectbox("Department", ["All"] + all_depts)
    if selected_dept != "All":
        filtered = filtered[filtered["start_dept"] == selected_dept]
        all_majors = sorted(filtered["start_major"].unique())
        selected_major = st.sidebar.selectbox("Major", ["All"] + all_majors)
        if selected_major != "All":
            filtered = filtered[filtered["start_major"] == selected_major]

# Min flow threshold
min_count = st.sidebar.slider("Min students in flow", 1, 30, 5)
filtered = filtered[filtered["count"] >= min_count]

# --- Build Sankey ---
src_col = level_to_col["start"][left_level]
tgt_col = level_to_col["end"][right_level]

grouped = filtered.groupby([src_col, tgt_col])["count"].sum().reset_index()
grouped.columns = ["source", "target", "value"]

# Deduplicate nodes (prefix to avoid collisions between left/right)
src_nodes = [f"FROM: {s}" for s in grouped["source"]]
tgt_nodes = [f"TO: {t}"   for t in grouped["target"]]
all_nodes = list(dict.fromkeys(src_nodes + tgt_nodes))
node_idx  = {n: i for i, n in enumerate(all_nodes)}

sources = [node_idx[s] for s in src_nodes]
targets = [node_idx[t] for t in tgt_nodes]
values  = grouped["value"].tolist()

if not values:
    st.warning("No data matches the current filters.")
else:
    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(
            label=[n.replace("FROM: ", "").replace("TO: ", "") for n in all_nodes],
            pad=20,
            thickness=20,
            color="#5b8dee",
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color="rgba(91,141,238,0.25)",
        ),
    ))
    fig.update_layout(
        margin=dict(l=10, r=10, t=30, b=10),
        height=500,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.caption(f"Showing {filtered['count'].sum():.0f} students across {len(grouped)} flows.")