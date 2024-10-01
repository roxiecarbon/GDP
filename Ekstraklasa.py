import pandas as pd
import dash
from dash import dcc, html
from dash.dash_table import DataTable
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go

# Wczytanie danych z pliku Excel
file_path = r'C:\Users\Ja\Downloads\Zeszyt1.xlsx'  # Ścieżka do pliku
sheet_name = 'Z'  # Nazwa arkusza, zmień na właściwą jeśli jest inna

# Wczytaj dane z Excela
df = pd.read_excel(file_path, sheet_name=sheet_name)

# Przekonwertuj kolumnę 'Wynik' na tekst
df['Wynik'] = df['Wynik'].astype(str)

# Lista drużyn do podświetlenia
highlighted_teams = ['Puszcza Niepołomice', 'Lechia Gdańsk', 'Radomiak Radom', 'Korona Kielce',
                     'Zagłębie Lubin', 'Piast Gliwice', 'Górnik Zabrze', 'Raków Częstochowa']

# Kolory przypisane do drużyn
team_colors = {
    'Puszcza Niepołomice': 'lightcoral',
    'Lechia Gdańsk': 'lightgreen',
    'Radomiak Radom': 'lightblue',
    'Korona Kielce': 'lightyellow',
    'Zagłębie Lubin': 'lightpink',
    'Piast Gliwice': 'lightsalmon',
    'Górnik Zabrze': 'lightcyan',
    'Raków Częstochowa': 'lightgoldenrodyellow'
}

# Funkcja do obliczania punktów na podstawie wyniku
def calculate_points(home_goals, away_goals):
    if home_goals > away_goals:
        return 3, 0  # Gospodarz wygrywa, 3 punkty dla gospodarza
    elif home_goals < away_goals:
        return 0, 3  # Gość wygrywa, 3 punkty dla gościa
    else:
        return 1, 1  # Remis, po 1 punkcie

# Przetwarzanie wyników i obliczanie punktów dla każdej drużyny po danej kolejce
def calculate_table(dataframe, max_kolejka):
    table = {}
    goals = {}

    for index, row in dataframe.iterrows():
        if row['Kolejka'] > max_kolejka:
            continue

        home_team = row['Druzyna G']
        away_team = row['Druzyna G.1']
        wynik = row['Wynik']

        home_goals, away_goals = map(int, wynik.split())

        home_points, away_points = calculate_points(home_goals, away_goals)

        # Initialize team points and goals if not already in the table
        if home_team not in table:
            table[home_team] = 0
            goals[home_team] = [0, 0]  # [scored, conceded]
        if away_team not in table:
            table[away_team] = 0
            goals[away_team] = [0, 0]

        # Update points
        table[home_team] += home_points
        table[away_team] += away_points

        # Update goals
        goals[home_team][0] += home_goals  # Home team scored
        goals[home_team][1] += away_goals  # Home team conceded
        goals[away_team][0] += away_goals  # Away team scored
        goals[away_team][1] += home_goals  # Away team conceded

    # Create the final table with teams, points, goals, and goal difference
    table_df = pd.DataFrame(list(table.items()), columns=['Druzyna', 'Punkty']).sort_values(by='Punkty', ascending=False)
    goals_df = pd.DataFrame([(team, f"{scored}:{conceded}", scored - conceded, scored) 
                             for team, (scored, conceded) in goals.items()],
                            columns=['Druzyna', 'Gole', 'Różnica Bramkowa', 'Gole Strzelone']).set_index('Druzyna')

    # Merge the points table with the goals table
    table_df = table_df.set_index('Druzyna').join(goals_df).reset_index()

    # Sort by Points, Goal Difference, and Goals Scored
    table_df = table_df.sort_values(by=['Punkty', 'Różnica Bramkowa', 'Gole Strzelone'], ascending=[False, False, False])

    # Add ranking column
    table_df['Miejsce'] = range(1, len(table_df) + 1)

    return table_df[['Miejsce', 'Druzyna', 'Punkty', 'Gole']]

# Function to calculate the dynamic chart data
def calculate_chart(dataframe, max_kolejka):
    teams = dataframe['Druzyna G'].unique()
    line_data = []

    for team in teams:
        team_data = dataframe[(dataframe['Druzyna G'] == team) | (dataframe['Druzyna G.1'] == team)]
        points_over_time = []
        
        for i in range(1, max_kolejka + 1):
            relevant_matches = team_data[team_data['Kolejka'] <= i]
            points = 0
            
            for _, match in relevant_matches.iterrows():
                if match['Druzyna G'] == team:
                    home_goals, away_goals = map(int, match['Wynik'].split())
                    home_points, _ = calculate_points(home_goals, away_goals)
                    points += home_points
                elif match['Druzyna G.1'] == team:
                    home_goals, away_goals = map(int, match['Wynik'].split())
                    _, away_points = calculate_points(home_goals, away_goals)
                    points += away_points

            points_over_time.append(points)

        line_data.append(go.Scatter(x=list(range(1, max_kolejka + 1)), y=points_over_time, mode='lines', name=team))

    return line_data

# Uruchomienie aplikacji Dash z interaktywną tabelą
app = dash.Dash(__name__)

app.layout = html.Div(style={'display': 'flex', 'flexDirection': 'row'}, children=[
    # Left side with table and slider
    html.Div(style={'width': '50%', 'padding': '10px'}, children=[
        html.H1(children='Tabela Ligowa'),

        dcc.Slider(
            id='kolejka-slider',
            min=df['Kolejka'].min(),
            max=df['Kolejka'].max(),
            value=df['Kolejka'].min(),  # Start from the first round
            marks={str(k): str(k) for k in df['Kolejka'].unique()},
            step=None,
            tooltip={"placement": "bottom", "always_visible": True}
        ),
        html.Div(style={'marginTop': '20px', 'textAlign': 'center'}, children=[
            html.Button("Play", id="play-button", n_clicks=0, style={'marginRight': '10px'}),
            html.Button("Stop", id="stop-button", n_clicks=0),
        ]),

        dcc.Interval(
            id='interval',
            interval=2000,  # 2 seconds interval between updates
            n_intervals=0,
            disabled=True  # Initially disabled until "Play" is pressed
        ),
        
        DataTable(
            id='football-table',
            columns=[{"name": i, "id": i} for i in ['Miejsce', 'Druzyna', 'Punkty', 'Gole']],
            data=[],  
            style_cell={'textAlign': 'center', 'fontSize': '10px'},  # Reduced font size
            style_header={
                'backgroundColor': 'lightblue',
                'fontWeight': 'bold',
                'fontSize': '12px'  # Header font size
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'lightgrey',
                },
                # Add colors for specific teams
                *[
                    {
                        'if': {'filter_query': f'{{Druzyna}} = "{team}"'},
                        'backgroundColor': color
                    }
                    for team, color in team_colors.items()
                ]
            ],
            page_action='none',
            style_table={'height': '350px', 'overflowY': 'auto', 'width': '70%', 'margin': 'auto'},  # Reduced height and width
        )
    ]),

    # Right side with dynamic line chart
    html.Div(style={'width': '50%', 'padding': '10px'}, children=[
        dcc.Graph(
            id='dynamic-line-chart',
            style={'height': '400px'}
        )
    ])
])

# Callback to update the slider during animation
@app.callback(
    Output('kolejka-slider', 'value'),
    [Input('interval', 'n_intervals')],
    [State('kolejka-slider', 'value')]
)
def update_slider(n_intervals, current_value):
    if current_value < df['Kolejka'].max():
        return current_value + 1
    else:
        return df['Kolejka'].min()

# Callback to update the table based on the selected 'kolejka'
@app.callback(
    Output('football-table', 'data'),
    [Input('kolejka-slider', 'value')]
)
def update_table(selected_kolejka):
    table_df = calculate_table(df, selected_kolejka)
    return table_df.to_dict('records')

# Callback to control the play/pause button for animation
@app.callback(
    Output('interval', 'disabled'),
    [Input('play-button', 'n_clicks'), Input('stop-button', 'n_clicks')],
    [State('interval', 'disabled')]
)
def play_pause(play_clicks, stop_clicks, interval_disabled):
    ctx = dash.callback_context
    if ctx.triggered:
        if ctx.triggered[0]['prop_id'] == 'play-button.n_clicks':
            return False  # Start the interval
        elif ctx.triggered[0]['prop_id'] == 'stop-button.n_clicks':
            return True  # Stop the interval
    return interval_disabled

# Callback to update the line chart based on the selected 'kolejka'
@app.callback(
    Output('dynamic-line-chart', 'figure'),
    [Input('kolejka-slider', 'value')]
)
def update_line_chart(selected_kolejka):
    line_data = calculate_chart(df, selected_kolejka)
    return {'data': line_data, 'layout': go.Layout(title='Points Over Time', xaxis={'title': 'Kolejka'}, yaxis={'title': 'Points'})}

if __name__ == '__main__':
    app.run_server(debug=True)
