import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Page config
st.set_page_config(page_title="UCLA Physical Sciences Retention", layout="wide")

# Load and process data
@st.cache_data
def load_data():
    maj2dept = {
        'atmospheric and oceanic sciences': 'aos',
        'climate science': 'aos',
        'aos/math': 'aos',
        'biochemistry': 'chemistry and biochemistry',
        'chemistry': 'chemistry and biochemistry',
        'materials science': 'chemistry and biochemistry',
        'gen chem for teaching': 'chemistry and biochemistry',
        'geology': 'epss',
        'engineering geology': 'epss',
        'geophysics': 'epss',
        'earth and environmental science': 'epss',
        'mathematics': 'math',
        'applied mathematics': 'math',
        'financial actuarial mathematics': 'math',
        'mathematics/applied science': 'math',
        'mathematics of computation': 'math',
        'mathematics for teaching': 'math',
        'mathematics/economics': 'math',
        'astrophysics': 'physics and astronomy',
        'biophysics': 'physics and astronomy',
        'physics': 'physics and astronomy',
        'physics-ba': 'physics and astronomy',
        'statistics and data science': 'statistics',
        'data theory': 'statistics',
        'environmental science': 'institute of environment and sustainability',
    }

    special_cases = {'no degree': 'no degree', 'undeclared': 'undeclared'}
    maj2dept_and_friends = maj2dept | special_cases

    df = pd.read_csv("raw_data.csv")

    # Data cleaning
    df.rename(columns={'cohort_major_desc': 'start_maj', 'deg_major_desc': 'end_maj', 'freshman_transfer': 'fresh'}, inplace=True)
    for col in ['urm', 'fresh', 'start_maj', 'end_maj']:
        df[col] = df[col].str.strip().str.lower()
    df['cohort'] = df['cohort'].str[:4].astype(int)
    df['urm'] = df['urm'].map({'urm': True, 'non-urm': False})
    df['fresh'] = df['fresh'].map({'freshman': True, 'transfer': False})
    df['start_maj'] = df['start_maj'].replace('general chemistry', 'chemistry').replace('undeclared-physical science', 'undeclared')

    # Track depts
    df['start_dept'] = df['start_maj'].map(maj2dept_and_friends)

    def temp_maj2dept_mapper_that_handles_other_divs(maj):
        return maj2dept_and_friends.get(maj, 'other')

    df['end_dept'] = df['end_maj'].map(temp_maj2dept_mapper_that_handles_other_divs)

    def categorize_outcome(row):
        if row['end_dept'] == 'no degree':
            return 'no degree'
        if row['end_dept'] == row['start_dept']:
            return 'retained'
        else:
            return 'other degree'
    
    df['outcome'] = df.apply(categorize_outcome, axis=1)

    # Expand double majors
    def expand_double_majors(df):
        expanded_rows = []
        
        for _, row in df.iterrows():
            start_majors = row['start_maj'].split('/') if '/' in str(row['start_maj']) else [row['start_maj']]
            end_majors = row['end_maj'].split('/') if '/' in str(row['end_maj']) and pd.notna(row['end_maj']) else [row['end_maj']]
            
            for start_maj in start_majors:
                for end_maj in end_majors:
                    new_row = row.copy()
                    new_row['start_maj'] = start_maj.strip()
                    new_row['end_maj'] = end_maj.strip() if pd.notna(end_maj) else end_maj
                    expanded_rows.append(new_row)
        
        return pd.DataFrame(expanded_rows)

    df = expand_double_majors(df)
    
    return df

df = load_data()

# Header
st.title("📊 UCLA Physical Sciences Retention Analysis")
st.markdown("""
Here are interactive graphs that show the retention rates for each department in UCLA's Division of Physical Sciences. 
They can be subdivided by Freshman vs Transfer admits and URM vs Non-URM students.

All students were classified as either:
1. Getting a degree in the department they were admitted to,
2. Getting a degree in another department (either in the division or elsewhere), or
3. Not getting a degree.

**Key Findings:**
- URM rates are consistently worse than Non-URM rates.
- Transfer rates are consistently better than Freshman rates.
- Rates vary significantly between departments.
- Most undeclared students leave the physical sciences entirely.
""")

with st.expander("ℹ️ Methodological Notes"):
    st.markdown("""
    - I split the double majors into both departments for accurate retention analysis. For example, if there were 5 AOS/Math majors, and they all graduated with AOS/Math degrees, all of those students would count toward the retention rates of both departments.
    - The freshmen in the 2020 cohort are the latest to have graduated. Most people in later cohorts have not graduated, contributing to extremely high "No Degree" rates.
    - The vertical dashed line marks 2020, the last cohort that has fully graduated.
    """)

st.markdown("---")

# Tab selection
tab1, tab2, tab3 = st.tabs(["📈 Per-Department Outcomes Over Time", "📊 Department Retention Comparison", "👤 Undeclared Outcomes"])

# TAB 1: Per-Department Outcomes
with tab1:
    st.subheader("Student Outcomes by Department Over Time")
    
    col1, col2, col3 = st.columns(3)

    departments = sorted([d for d in df['start_dept'].dropna().unique() if d != 'undeclared'])
    
    with col1:
        department = st.selectbox('Select Department', options=departments, index=0, key='dept_tab1')
    
    with col2:
        urm_status = st.selectbox('URM Status', options=['All', 'URM', 'Non-URM'], index=0, key='urm_tab1')
    
    with col3:
        student_type = st.selectbox('Student Type', options=['All', 'Freshman', 'Transfer'], index=0, key='student_tab1')
    
    # Filter data
    def categorize_outcome_display(row):
        if row['end_dept'] == 'no degree':
            return 'No Degree'
        elif row['start_dept'] == row['end_dept']:
            return 'Stayed in Department'
        else:
            return 'Other Department'
    
    df['outcome_display'] = df.apply(categorize_outcome_display, axis=1)
    
    filtered = df[df['start_dept'] == department].copy()
    
    if urm_status != 'All':
        filtered = filtered[filtered['urm'] == (urm_status == 'URM')]
    
    if student_type != 'All':
        filtered = filtered[filtered['fresh'] == (student_type == 'Freshman')]
    
    # Group and calculate percentages
    grouped = filtered.groupby(['cohort', 'outcome_display'])['headcount'].sum().reset_index()
    totals = filtered.groupby('cohort')['headcount'].sum().reset_index()
    totals.rename(columns={'headcount': 'total'}, inplace=True)
    
    grouped = grouped.merge(totals, on='cohort')
    grouped['percentage'] = (grouped['headcount'] / grouped['total']) * 100
    
    # Pivot
    pivot = grouped.pivot(index='cohort', columns='outcome_display', values='percentage').fillna(0)
    
    # Create figure
    fig1 = go.Figure()
    
    outcomes = ['Stayed in Department', 'Other Department', 'No Degree']
    colors = ['#268bd2', '#859900', '#dc322f']
    
    for i, outcome in enumerate(outcomes):
        if outcome in pivot.columns:
            fig1.add_trace(go.Scatter(
                x=pivot.index,
                y=pivot[outcome],
                name=outcome,
                stackgroup='one',
                fillcolor=colors[i],
                line=dict(width=0.5, color=colors[i]),
                hovertemplate='%{y:.1f}%<extra></extra>'
            ))
    
    # Update layout
    title = f'Student Outcomes for {department.title()} Department'
    if urm_status != 'All':
        title += f' ({urm_status})'
    if student_type != 'All':
        title += f' ({student_type})'
    
    fig1.update_layout(
        title=title,
        xaxis_title='Cohort Year',
        yaxis_title='Percentage (%)',
        hovermode='x unified',
        height=500,
        yaxis=dict(range=[0, 100]),
        xaxis=dict(tickmode='linear', tick0=2010, dtick=1),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5
        ),
        shapes=[
            dict(
                type='line',
                x0=2020,
                x1=2020,
                y0=0,
                y1=100,
                line=dict(color='#657b83', width=2, dash='dash'),
                opacity=0.5
            )
        ]
    )
    
    st.plotly_chart(fig1, use_container_width=True)
    
    # Summary stats
    st.subheader("Summary Statistics (2010-2020 Cohorts)")
    scol1, scol2 = st.columns(2)
    
    filtered_cohorts = filtered[(filtered['cohort'] >= 2010) & (filtered['cohort'] <= 2020)]
    total_students = filtered_cohorts['headcount'].sum()
    retained = filtered_cohorts[filtered_cohorts['outcome_display'] == 'Stayed in Department']['headcount'].sum()
    retention_rate = (retained / total_students * 100) if total_students > 0 else 0
    
    scol1.metric("Total Students", f"{int(total_students)}")
    scol2.metric("Retention Rate", f"{retention_rate:.1f}%")

# TAB 2: Retention Comparison
with tab2:
    st.subheader("Average Department Retention Rates (2010-2020 Cohorts)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        urm_status_2 = st.selectbox('URM Status', options=['All', 'URM', 'Non-URM'], index=0, key='urm_tab2')
    
    with col2:
        student_type_2 = st.selectbox('Student Type', options=['All', 'Freshman', 'Transfer'], index=0, key='student_tab2')
    
    # Filter cohort range
    df_filtered = df[(df['cohort'] >= 2010) & (df['cohort'] <= 2020)].copy()
    
    # Apply filters
    if urm_status_2 != 'All':
        df_filtered = df_filtered[df_filtered['urm'] == (urm_status_2 == 'URM')]
    
    if student_type_2 != 'All':
        df_filtered = df_filtered[df_filtered['fresh'] == (student_type_2 == 'Freshman')]
    
    # Calculate retention per department
    retention_rates = []
    
    departments_list = sorted([d for d in df_filtered['start_dept'].dropna().unique() if d != 'undeclared'])
    
    for dept in departments_list:
        dept_df = df_filtered[df_filtered['start_dept'] == dept]
        
        total = dept_df['headcount'].sum()
        retained = dept_df[dept_df['outcome_display'] == 'Stayed in Department']['headcount'].sum()
        
        retention_rate = (retained / total * 100) if total > 0 else 0
        
        retention_rates.append({
            'dept': dept,
            'retention_rate': retention_rate,
            'total': total
        })
    
    retention_df = pd.DataFrame(retention_rates).dropna()
    retention_df = retention_df.sort_values('retention_rate', ascending=True)
    
    # Create Plotly figure
    fig2 = go.Figure()
    
    fig2.add_trace(go.Bar(
        x=retention_df['retention_rate'],
        y=retention_df['dept'].str.title(),
        orientation='h',
        text=[f"{v:.1f}%" for v in retention_df['retention_rate']],
        textposition='outside',
        marker=dict(color='#2E86AB'),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Retention: %{x:.1f}%<br>"
            "Total students: %{customdata}<extra></extra>"
        ),
        customdata=retention_df['total']
    ))
    
    # Dynamic title
    title = "Average Department Retention Rates (2010–2020 Cohorts)"
    if urm_status_2 != 'All':
        title += f" ({urm_status_2})"
    if student_type_2 != 'All':
        title += f" ({student_type_2})"
    
    fig2.update_layout(
        title=title,
        xaxis_title='Retention Rate (%)',
        yaxis_title='Department',
        xaxis=dict(range=[0, 100]),
        height=600,
        margin=dict(l=200, r=40, t=80, b=60),
        template='plotly_white'
    )
    
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    st.subheader("Undeclared Student Outcomes")

    # Define physical sciences departments
    phys_sci_depts = {'aos', 'chemistry and biochemistry', 'epss', 
                    'institute of environment and sustainability', 'math', 
                    'physics and astronomy', 'statistics'}

    # Filter for undeclared students
    undeclared = df[df['start_dept'] == 'undeclared'].copy()

    # Categorize outcomes
    def categorize_undeclared_outcome(row):
        if row['end_dept'] == 'no degree':
            return 'No Degree'
        elif row['end_dept'] in phys_sci_depts:
            return 'Stayed in Physical Sciences'
        else:
            return 'Other Degree'

    undeclared['outcome'] = undeclared.apply(categorize_undeclared_outcome, axis=1)

    # Group and calculate percentages
    grouped = undeclared.groupby(['cohort', 'outcome'])['headcount'].sum().reset_index()
    totals = undeclared.groupby('cohort')['headcount'].sum().reset_index()
    totals.rename(columns={'headcount': 'total'}, inplace=True)

    grouped = grouped.merge(totals, on='cohort')
    grouped['percentage'] = (grouped['headcount'] / grouped['total']) * 100

    # Pivot
    pivot = grouped.pivot(index='cohort', columns='outcome', values='percentage').fillna(0)

    # Create figure
    fig = go.Figure()

    outcomes = ['Stayed in Physical Sciences', 'Other Degree', 'No Degree']
    colors = ['#268bd2', '#859900', '#dc322f']

    for i, outcome in enumerate(outcomes):
        if outcome in pivot.columns:
            fig.add_trace(go.Scatter(
                x=pivot.index,
                y=pivot[outcome],
                name=outcome,
                stackgroup='one',
                fillcolor=colors[i],
                line=dict(width=0.5, color=colors[i]),
                hovertemplate='%{y:.1f}%<extra></extra>'
            ))

    fig.update_layout(
        title='Undeclared Student Outcomes',
        xaxis_title='Cohort Year',
        yaxis_title='Percentage (%)',
        hovermode='x unified',
        height=500,
        yaxis=dict(range=[0, 100]),
        xaxis=dict(tickmode='linear', tick0=2010, dtick=1),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5
        ),
        shapes=[
            dict(
                type='line',
                x0=2020,
                x1=2020,
                y0=0,
                y1=100,
                line=dict(color='#657b83', width=2, dash='dash'),
                opacity=0.5
            )
        ]
    )

    st.plotly_chart(fig, use_container_width=True)

    # Summary stats
    scol1, scol2 = st.columns(2)

    filtered_cohorts = undeclared[(undeclared['cohort'] >= 2010) & (undeclared['cohort'] <= 2020)]
    total_students = filtered_cohorts['headcount'].sum()
    stayed = filtered_cohorts[filtered_cohorts['outcome'] == 'Stayed in Physical Sciences']['headcount'].sum()
    retention_rate = (stayed / total_students * 100) if total_students > 0 else 0

    scol1.metric("Total Undeclared Students (2010-2020)", f"{int(total_students)}")
    scol2.metric("Stayed in Physical Sciences (2010-2020)", f"{retention_rate:.1f}%")


# Footer
st.markdown("---")
st.markdown("*Data source: UCLA Division of Physical Sciences*")
