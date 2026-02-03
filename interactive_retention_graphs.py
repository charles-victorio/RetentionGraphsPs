# %% [markdown]
# # Per-Department Retention Graphs
# 
# <img src="ucla_ps_box.png" alt="UCLA Physical Sciences" width="200"/>
# 
# Here are interactive graphs that show the retention rates for each department in UCLA's Division of Physical Sciences. They can be subdivided in Freshman vs Transfer admits and URM vs Non-URM students.
# 
# All students were classified as either:
# 1. getting a degree in the department they were admitted to,
# 2. getting a degree in another department (either in the division or elsewhere), or
# 3. not getting a degree.
# 
# URM rates are consistently worse than Non-URM rates. Transfer rates are consistently better than Freshman rates. Rates vary significantly between departments.
# 
# #### Methodological Notes
# I split the double majors into both departments for accurate retention analysis. For example, if there were 5 aos/math majors, and they all graduated with aos/math degrees, all of those students would count toward the retention rates of both departments.
# 
# The freshman in the 2021 cohort are the latest to have graduated. Most people in later cohorts have not graduated, contributing to extremely high "No Degree" rates.
# 
# ---

# %%
import time

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# make csv
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

dbl_majs = {
    'atmospheric and oceanic sciences/mathematics',
    'chemistry/materials science',
    'geography/environmental studies',
    'geology/engineering geology',
    'geology/paleobiology',
    'geophysics/applied geophysics',
    'geophysics/geophysics and space physics'
    'mathematics/applied science',
    'mathematics/economics'
    'design / media arts',
}

special_cases = {'no degree': 'no degree', 'undeclared': 'undeclared'} # make better name
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

def temp_maj2dept_mapper_that_handles_other_divs(maj): # will be replaced by extending maj2dept to all divisions
    return maj2dept_and_friends.get(maj, 'other')

df['end_dept'] = df['end_maj'].map(temp_maj2dept_mapper_that_handles_other_divs)

def categorize_outcome(row):
    if row['end_dept'] == 'no degree':
        return 'no degree'
    if row['end_dept'] == row['start_dept']:
        return 'retained'
    else: # other dept in div, or other div
        return 'other degree'
    
df['outcome'] = df.apply(categorize_outcome, axis=1)

# %%
def expand_double_majors(df):
    """
    Expand rows with double majors (containing '/') into separate rows
    """
    expanded_rows = []
    
    for _, row in df.iterrows():
        start_majors = row['start_maj'].split('/') if '/' in str(row['start_maj']) else [row['start_maj']]
        end_majors = row['end_maj'].split('/') if '/' in str(row['end_maj']) and pd.notna(row['end_maj']) else [row['end_maj']]
        
        # Create a row for each combination
        for start_maj in start_majors:
            for end_maj in end_majors:
                new_row = row.copy()
                new_row['start_maj'] = start_maj.strip()
                new_row['end_maj'] = end_maj.strip() if pd.notna(end_maj) else end_maj
                expanded_rows.append(new_row)
    
    return pd.DataFrame(expanded_rows)

# Usage
df = expand_double_majors(df)


# %%
import plotly.graph_objects as go
from ipywidgets import interact, Dropdown, fixed
import pandas as pd

def create_outcome_plot(df, department, urm_status, student_type):
    """
    Create stacked area chart based on filters
    """
    # Create outcome column
    def categorize_outcome(row):
        if row['end_dept'] == 'no degree':
            return 'No Degree'
        elif row['start_dept'] == row['end_dept']:
            return 'Stayed in Department'
        else:
            return 'Other Department'
    
    df['outcome'] = df.apply(categorize_outcome, axis=1)
    
    # Filter data
    filtered = df[df['start_dept'] == department].copy()
    
    if urm_status != 'All':
        filtered = filtered[filtered['urm'] == (urm_status == 'URM')]
    
    if student_type != 'All':
        filtered = filtered[filtered['fresh'] == (student_type == 'Freshman')]
    
    # Group and calculate percentages
    grouped = filtered.groupby(['cohort', 'outcome'])['headcount'].sum().reset_index()
    totals = filtered.groupby('cohort')['headcount'].sum().reset_index()
    totals.rename(columns={'headcount': 'total'}, inplace=True)
    
    grouped = grouped.merge(totals, on='cohort')
    grouped['percentage'] = (grouped['headcount'] / grouped['total']) * 100
    
    # Pivot
    pivot = grouped.pivot(index='cohort', columns='outcome', values='percentage').fillna(0)
    
    # Create figure
    fig = go.Figure()
    
    outcomes = ['Stayed in Department', 'Other Department', 'No Degree']
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
    
    # Update layout
    title = f'Student Outcomes for {department.title()} Department'
    if urm_status != 'All':
        title += f' ({urm_status})'
    if student_type != 'All':
        title += f' ({student_type})'
    
    fig.update_layout(
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
            y=-0.2,
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
    
    fig.show()

# Create interactive widget
departments = sorted(df['start_dept'].dropna().unique())
departments.remove('undeclared')

interact(
    create_outcome_plot,
    df=fixed(df),
    department=Dropdown(options=departments, value=departments[0], description='Department:'),
    urm_status=Dropdown(options=['All', 'URM', 'Non-URM'], value='All', description='URM Status:'),
    student_type=Dropdown(options=['All', 'Freshman', 'Transfer'], value='All', description='Student Type:')
)

# %%
import plotly.graph_objects as go
from ipywidgets import interact, Dropdown, fixed
import pandas as pd

def create_retention_plot(df, urm_status, student_type):
    # Filter cohort range
    df_filtered = df[(df['cohort'] >= 2010) & (df['cohort'] <= 2020)].copy()

    # Create outcome column
    def categorize_outcome(row):
        if row['end_dept'] == 'no degree':
            return 'No Degree'
        elif row['start_dept'] == row['end_dept']:
            return 'Stayed in Department'
        else:
            return 'Other Department'

    df_filtered['outcome'] = df_filtered.apply(categorize_outcome, axis=1)

    # Apply URM filter
    if urm_status != 'All':
        df_filtered = df_filtered[df_filtered['urm'] == (urm_status == 'URM')]

    # Apply student type filter
    if student_type != 'All':
        df_filtered = df_filtered[df_filtered['fresh'] == (student_type == 'Freshman')]

    # Calculate retention per department
    retention_rates = []

    departments = sorted(df_filtered['start_dept'].dropna().unique().tolist())
    if 'undeclared' in departments:
        departments.remove('undeclared')

    for dept in departments:
        dept_df = df_filtered[df_filtered['start_dept'] == dept]

        total = dept_df['headcount'].sum()
        retained = dept_df[dept_df['outcome'] == 'Stayed in Department']['headcount'].sum()

        retention_rate = (retained / total * 100) if total > 0 else 0

        retention_rates.append({
            'dept': dept,
            'retention_rate': retention_rate,
            'total': total
        })

    retention_df = pd.DataFrame(retention_rates).dropna()
    retention_df = retention_df.sort_values('retention_rate', ascending=True)

    # Create Plotly figure
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=retention_df['retention_rate'],
        y=retention_df['dept'],
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
    if urm_status != 'All':
        title += f" ({urm_status})"
    if student_type != 'All':
        title += f" ({student_type})"

    fig.update_layout(
        title=title,
        xaxis_title='Retention Rate (%)',
        yaxis_title='Department',
        xaxis=dict(range=[0, 100]),
        height=600,
        margin=dict(l=140, r=40, t=80, b=60),
        template='plotly_white'
    )

    fig.show()


# Interactive controls
interact(
    create_retention_plot,
    df=fixed(df),
    urm_status=Dropdown(
        options=['All', 'URM', 'Non-URM'],
        value='All',
        description='URM Status:'
    ),
    student_type=Dropdown(
        options=['All', 'Freshman', 'Transfer'],
        value='All',
        description='Student Type:'
    )
)



