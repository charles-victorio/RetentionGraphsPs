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
for col in ['urm', 'ft', 'start', 'end']:
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
grouped = df.groupby(['cohort', 'start_dept', 'outcome'])['headcount'].sum().reset_index()

# Calculate total headcount per cohort-start_dept
totals = df.groupby(['cohort', 'start_dept'])['headcount'].sum().reset_index()
totals.rename(columns={'headcount': 'total'}, inplace=True)


# Merge and calculate percentages
result = grouped.merge(totals, on=['cohort', 'start_dept'])
result['percentage'] = (result['headcount'] / result['total']) * 100


# Pivot for easier viewing
pivot = result.pivot_table(
    index=['cohort', 'start_dept'], 
    columns='outcome', 
    values='percentage', 
    fill_value=0
).reset_index()


# plotting, has duplicate work


def plot_department_outcomes(df, department):
    """
    Plot stacked area chart showing retention outcomes for a specific department
    
    Parameters:
    df: DataFrame with columns cohort, start_dept, end_dept, headcount
    department: string name of department to plot
    """
    # Filter for the specific department
    dept_df = df[df['start_dept'] == department].copy()
    
    # Create outcome column
    def categorize_outcome(row):
        if row['end_dept'] == 'no degree':
            return 'No Degree'
        elif row['start_dept'] == row['end_dept']:
            return 'Stayed in Department'
        else:
            return 'Other Department'
    
    dept_df['outcome'] = dept_df.apply(categorize_outcome, axis=1)
    
    # Group by cohort and outcome, sum headcount
    grouped = dept_df.groupby(['cohort', 'outcome'])['headcount'].sum().reset_index()
    
    # Calculate percentages
    totals = dept_df.groupby('cohort')['headcount'].sum().reset_index()
    totals.rename(columns={'headcount': 'total'}, inplace=True)
    
    grouped = grouped.merge(totals, on='cohort')
    grouped['percentage'] = (grouped['headcount'] / grouped['total']) * 100
    
    # Pivot for plotting
    pivot = grouped.pivot(index='cohort', columns='outcome', values='percentage').fillna(0)
    
    # Reorder columns for better stacking order
    column_order = ['Stayed in Department', 'Other Department', 'No Degree']
    pivot = pivot[[col for col in column_order if col in pivot.columns]]
    
    # Create stacked area chart
    fig, ax = plt.subplots(figsize=(12, 6))
    pivot.plot(kind='area', stacked=True, ax=ax, alpha=0.7)
    
    ax.set_xlabel('Cohort Year', fontsize=12)
    ax.set_ylabel('Percentage (%)', fontsize=12)
    ax.set_title(f'Student Outcomes for {department} Department (2010-2023)', fontsize=14, fontweight='bold')
    ax.set_xticks(pivot.index)
    ax.set_ylim(0, 100)
    ax.legend(title='Outcome', loc='upper left', bbox_to_anchor=(1, 1))
    ax.axvline(x=2021, color='red', linestyle='--', linewidth=2, alpha=0.7, label='Last Graduated Cohort')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f"{time.monotonic()}-{department}.png")
    
    return pivot

# Usage:
for dept in df.start_dept.unique().dropna(): # lol at dropna
    plot_department_outcomes(df, dept)