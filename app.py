import os
import pandas as pd
import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go

# Load dataset
df = pd.read_csv("global_student_migration.csv")

# Create the Dash app
app = dash.Dash(__name__)
app.title = "Global Student Migration Interactive Dashboard"
server = app.server  # For Render deployment

# Layout
app.layout = html.Div([

    html.H1("🌍 Global Student Migration Dashboard", style={'textAlign': 'center'}),
    html.P(
        "This dashboard tells the story of how students move across the globe: "
        "where they study, why they choose certain destinations, how they perform, "
        "their career outcomes after graduation, and which courses are the most popular.",
        style={'textAlign': 'center', 'fontSize': 16}
    ),

    html.Div([
        html.Label("Select Destination Country"),
        dcc.Dropdown(
            id='country_dropdown',
            options=[{'label': i, 'value': i} for i in sorted(df['destination_country'].dropna().unique())],
            value=sorted(df['destination_country'].dropna().unique())[0],
            clearable=False
        ),
        html.Br(),
        html.Label("Select Year of Enrollment"),
        dcc.Slider(
            id='year_slider',
            min=int(df['year_of_enrollment'].min()),
            max=int(df['year_of_enrollment'].max()),
            step=1,
            value=int(df['year_of_enrollment'].min()),
            marks={i: str(i) for i in range(
                int(df['year_of_enrollment'].min()),
                int(df['year_of_enrollment'].max()) + 1
            )}
        ),
    ], style={'width': '50%', 'margin': 'auto'}),

    html.Br(),

    html.Div([
        html.Div([
            html.H3("1️⃣ Global Student Migration"),
            html.P("Interactive world map showing where students go in the selected year. "
                   "The chosen country is marked with a red highlight."),
            dcc.Graph(id='map_chart')
        ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'}),

        html.Div([
            html.H3("2️⃣ Why Students Enroll"),
            html.P("A bar chart showing the most common reasons students choose a given country "
                   "in the selected year."),
            dcc.Graph(id='reason_chart'),
            html.Div(id='reason_narrative', style={'fontStyle': 'italic', 'padding': '10px'})
        ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'}),
    ]),

    html.Div([
        html.Div([
            html.H3("3️⃣ Salary Outcomes Across Countries"),
            html.P("A box plot comparing starting salaries across all countries in the selected year. "
                   "The chosen country is highlighted in red for easy comparison."),
            dcc.Graph(id='salary_chart')
        ], style={'width': '98%', 'display': 'inline-block', 'verticalAlign': 'top'}),
    ]),

    html.Div([
        html.H3("4️⃣ Most Popular Courses Among Students"),
        html.P("Shows the most frequently chosen courses for students in the selected country and year."),
        dcc.Graph(id='course_chart'),
        html.Div(id='course_narrative', style={'fontStyle': 'italic', 'padding': '10px'})
    ])
])

# Callback
@app.callback(
    Output('map_chart', 'figure'),
    Output('reason_chart', 'figure'),
    Output('salary_chart', 'figure'),
    Output('reason_narrative', 'children'),
    Output('course_chart', 'figure'),
    Output('course_narrative', 'children'),
    Input('country_dropdown', 'value'),
    Input('year_slider', 'value')
)
def update_charts(selected_country, selected_year):
    year_df = df[df['year_of_enrollment'] == selected_year]

    # Map
    if year_df.empty:
        map_fig = px.choropleth(title="No data for this year")
    else:
        count_df = year_df.groupby('destination_country').size().reset_index(name='count')
        map_fig = px.choropleth(
            count_df,
            locations='destination_country',
            locationmode='country names',
            color='count',
            hover_name='destination_country',
            color_continuous_scale='Viridis',
            title=f"Student Migration in {selected_year}"
        )
        map_fig.update_geos(showcoastlines=True, projection_type="natural earth")

        if selected_country in count_df['destination_country'].values:
            sel_data = count_df[count_df['destination_country'] == selected_country]
            map_fig.add_trace(go.Scattergeo(
                locations=sel_data['destination_country'],
                locationmode='country names',
                text=sel_data['destination_country'],
                mode='markers+text',
                marker=dict(size=15, color='red', line=dict(width=2, color='black')),
                textposition='top center',
                showlegend=False
            ))

    selected_df = year_df[year_df['destination_country'] == selected_country]

    # Reasons
    if not selected_df.empty:
        reason_counts = selected_df['enrollment_reason'].value_counts().reset_index()
        reason_counts.columns = ['Reason', 'Count']
        reason_counts['Percent'] = (reason_counts['Count'] / reason_counts['Count'].sum() * 100).round(1)
        reason_counts = reason_counts.sort_values(by='Count', ascending=False)
        colors = ['#ff7f0e' if i == 0 else '#1f77b4' for i in range(len(reason_counts))]
        reason_fig = px.bar(
            reason_counts, x='Reason', y='Count',
            text=reason_counts.apply(lambda row: f"{row['Count']} ({row['Percent']}%)", axis=1),
            color=reason_counts.index,
            color_discrete_sequence=colors
        )
        reason_fig.update_traces(textposition="outside", showlegend=False)
        top_reason = reason_counts.iloc[0]
        reason_story = f"In {selected_year}, most students choosing {selected_country} cited '{top_reason['Reason']}' — {top_reason['Percent']}%."
    else:
        reason_fig = px.bar(title="No data")
        reason_story = "No data available."

    # Salary
    salary_df = year_df[year_df['starting_salary_usd'] > 0].copy()
    if not salary_df.empty:
        medians = salary_df.groupby('destination_country')['starting_salary_usd'].median().sort_values(ascending=False)
        salary_df['destination_country'] = pd.Categorical(salary_df['destination_country'], categories=medians.index, ordered=True)
        salary_df['highlight'] = salary_df['destination_country'].apply(
            lambda x: 'Selected Country' if x == selected_country else 'Other'
        )
        salary_fig = px.box(
            salary_df,
            x='destination_country',
            y='starting_salary_usd',
            points='all',
            color='highlight',
            color_discrete_map={'Selected Country': 'red', 'Other': 'lightgray'},
            title=f"Starting Salary Comparison in {selected_year} (Highlight: {selected_country})"
        )
        salary_fig.update_xaxes(tickangle=45)
    else:
        salary_fig = px.box(title="No salary data")

    # Courses
    if not selected_df.empty and 'course_name' in selected_df.columns:
        course_counts = selected_df['course_name'].value_counts().reset_index()
        course_counts.columns = ['Course', 'Count']
        course_counts['Percent'] = (course_counts['Count'] / course_counts['Count'].sum() * 100).round(1)
        course_counts = course_counts.sort_values(by='Count', ascending=False)
        colors = ['#2ca02c' if i == 0 else '#1f77b4' for i in range(len(course_counts))]
        course_fig = px.bar(
            course_counts, x='Course', y='Count',
            text=course_counts.apply(lambda row: f"{row['Count']} ({row['Percent']}%)", axis=1),
            color=course_counts.index,
            color_discrete_sequence=colors
        )
        course_fig.update_traces(textposition="outside", showlegend=False)
        top_course = course_counts.iloc[0]
        course_story = f"In {selected_year}, the most chosen course in {selected_country} was '{top_course['Course']}' — {top_course['Percent']}% of students."
    else:
        course_fig = px.bar(title="No course data")
        course_story = "No course data available."

    return map_fig, reason_fig, salary_fig, reason_story, course_fig, course_story


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8050))
    app.run_server(host="0.0.0.0", port=port, debug=False)
