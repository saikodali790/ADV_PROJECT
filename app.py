Python 3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license()" for more information.
>>> import pandas as pd
... import dash
... from dash import dcc, html, Input, Output
... import plotly.express as px
... 
... # Load dataset
... df = pd.read_csv("global_student_migration.csv")
... 
... # Initialize Dash app
... app = dash.Dash(__name__)
... server = app.server  # This is important for Render deployment
... 
... # Layout
... app.layout = html.Div([
...     html.H1("🌍 Global Student Migration Dashboard", style={'textAlign': 'center'}),
... 
...     html.Div([
...         html.Label("Select Year:"),
...         dcc.Dropdown(
...             id='year-dropdown',
...             options=[{'label': y, 'value': y} for y in sorted(df['Year'].unique())],
...             value=sorted(df['Year'].unique())[0],
...             clearable=False
...         )
...     ], style={'width': '40%', 'margin': 'auto'}),
... 
...     dcc.Graph(id='bubble-map', style={'height': '600px'}),
...     dcc.Graph(id='trend-line', style={'height': '500px'})
... ])
... 
... # Callbacks
... @app.callback(
...     [Output('bubble-map', 'figure'),
...      Output('trend-line', 'figure')],
...     [Input('year-dropdown', 'value')]
)
def update_dashboard(selected_year):
    # Filter data
    filtered_df = df[df['Year'] == selected_year]

    # Bubble map
    fig_map = px.scatter_geo(
        filtered_df,
        locations="Country_Code",
        color="Continent",
        size="Students",
        hover_name="Country",
        projection="natural earth",
        title=f"Student Migration in {selected_year}"
    )

    # Trend line
    fig_trend = px.line(
        df.groupby("Year", as_index=False)['Students'].sum(),
        x='Year',
        y='Students',
        markers=True,
        title="Global Student Migration Trend"
    )

    return fig_map, fig_trend


# Run app
if __name__ == "__main__":
    app.run_server(debug=False, host="0.0.0.0", port=8080)
