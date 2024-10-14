import pandas as pd
import plotly.graph_objs as go
import streamlit as st
# Provide the correct raw URL of the Excel file hosted on GitHub
file_url = 'https://github.com/roxiecarbon/GDP/raw/main/Zeszyt1.xlsx'

# Load the Excel file from the GitHub URL
df = pd.read_excel(file_url)

# Convert the 'Wynik' column to string
df['Wynik'] = df['Wynik'].astype(str)

# Assigned team colors
team_colors = {
    'Stal Rzeszów ': 'blue',  
    'Arka Gdynia ': 'yellow',           
    'Miedź Legnica ': 'green',           
    'Chrobry Głogów ': 'orange',       
    'Motor Lublin ': 'yellow',          
    'Znicz Pruszków ': 'red',                  
    'Polonia Warszawa ': 'black',              
    'Górnik Łęczna ': 'green',           
    'Podbeskidzie Bielsko:Biała ': 'red',             
    'Zagłębie Sosnowiec ': 'green',     
    'Lechia Gdańsk ': 'white',           
    'GKS Katowice': 'yellow',          
    'Bruk:Bet Termalica Nieciecza ': 'orange',               
    'Wisła Kraków ': 'red',         
    'Wisła Płock ': 'blue',            
    'Resovia ': 'red',          
}

# Function to calculate points based on match result
def calculate_points(home_goals, away_goals):
    if home_goals > away_goals:
        return 3, 0  
    elif home_goals < away_goals:
        return 0, 3  
    else:
        return 1, 1  

# Function to process results and calculate points for each round
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

        if home_team not in table:
            table[home_team] = 0
            goals[home_team] = [0, 0]  
        if away_team not in table:
            table[away_team] = 0
            goals[away_team] = [0, 0]

        table[home_team] += home_points
        table[away_team] += away_points

        goals[home_team][0] += home_goals  
        goals[home_team][1] += away_goals  
        goals[away_team][0] += away_goals  
        goals[away_team][1] += home_goals  

    table_df = pd.DataFrame(list(table.items()), columns=['Druzyna', 'Punkty']).sort_values(by='Punkty', ascending=False)
    goals_df = pd.DataFrame([(team, f"{scored}:{conceded}", scored - conceded, scored) 
                             for team, (scored, conceded) in goals.items()],
                            columns=['Druzyna', 'Gole', 'Różnica Bramkowa', 'Gole Strzelone']).set_index('Druzyna')

    table_df = table_df.set_index('Druzyna').join(goals_df).reset_index()

    table_df = table_df.sort_values(by=['Punkty', 'Różnica Bramkowa', 'Gole Strzelone'], ascending=[False, False, False])

    table_df['Miejsce'] = range(1, len(table_df) + 1)

    return table_df[['Miejsce', 'Druzyna', 'Punkty', 'Gole']]

# Function to calculate the dynamic chart data with animation
def calculate_chart_with_animation(dataframe, max_kolejka):
    teams = sorted(dataframe['Druzyna G'].unique())  # Alphabetically sorted
    frames = []
    initial_data = []
    all_points = {team: [0] for team in teams}  # Collect points for each team over time

    for i in range(1, max_kolejka + 1):
        for team in teams:
            team_data = dataframe[(dataframe['Druzyna G'] == team) | (dataframe['Druzyna G.1'] == team)]
            points = all_points[team][-1]  # Start with the last known points

            relevant_matches = team_data[team_data['Kolejka'] == i]
            for _, match in relevant_matches.iterrows():
                if match['Druzyna G'] == team:
                    home_goals, away_goals = map(int, match['Wynik'].split())
                    home_points, _ = calculate_points(home_goals, away_goals)
                    points += home_points
                elif match['Druzyna G.1'] == team:
                    home_goals, away_goals = map(int, match['Wynik'].split())
                    _, away_points = calculate_points(home_goals, away_goals)
                    points += away_points

            all_points[team].append(points)  # Append the new points for the team

    # Generate frames for each kolejka
    for i in range(1, max_kolejka + 1):
        frame_data = []
        for team in teams:
            # Update each team's line for the current frame
            frame_data.append(go.Scatter(
                x=list(range(1, i + 1)), 
                y=all_points[team][:i + 1], 
                mode='lines+markers', 
                name=team, 
                hoverinfo='text',
                text=[f"{team}: {points} points" for points in all_points[team][:i + 1]],  
                line=dict(color=team_colors.get(team, 'gray'), shape='spline')  
            ))

        frames.append(go.Frame(data=frame_data, name=str(i)))

    # Initial data setup
    for team in teams:
        initial_data.append(go.Scatter(
            x=[1], y=[0], mode='lines+markers', name=team, line=dict(color=team_colors.get(team, 'gray'), shape='spline')
        ))

    return initial_data, frames


# Run the Dash app
app = dash.Dash(__name__)

app.layout = html.Div(style={'display': 'flex', 'flexDirection': 'row'}, children=[
    html.Div(style={'width': '50%', 'padding': '10px'}, children=[
        html.H1(children='Tabela Ligowa'),

        # Slider for the table
        dcc.Slider(
            id='kolejka-slider-table',
            min=df['Kolejka'].min(),
            max=df['Kolejka'].max(),
            value=df['Kolejka'].min(),  # Start from the first round
            marks={str(k): str(k) for k in df['Kolejka'].unique()},
            step=None,
            tooltip={"placement": "bottom", "always_visible": True}
        ),

        DataTable(
            id='football-table',
            columns=[{"name": i, "id": i} for i in ['Miejsce', 'Druzyna', 'Punkty', 'Gole']],
            data=[],  
            style_cell={'textAlign': 'center', 'fontSize': '10px'},  
            style_header={
                'backgroundColor': 'lightblue',
                'fontWeight': 'bold',
                'fontSize': '12px'  
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'lightgrey',
                },
                *[
                    {
                        'if': {'filter_query': f'{{Druzyna}} = "{team}"'},
                        'backgroundColor': color
                    }
                    for team, color in team_colors.items()
                ]
            ],
            page_action='none',
            style_table={'height': '350px', 'overflowY': 'auto', 'width': '70%', 'margin': 'auto'},  
        )
    ]),

    html.Div(style={'width': '50%', 'padding': '10px'}, children=[
        dcc.Graph(
            id='dynamic-line-chart',
            style={'height': '400px'}
        ),
    ])
])

# Callback for updating the table based on the slider
@app.callback(
    Output('football-table', 'data'),
    Input('kolejka-slider-table', 'value')  # ONLY connected to the table now
)
def update_table(selected_kolejka):
    table_df = calculate_table(df, selected_kolejka)
    table_data = table_df.to_dict('records')
    return table_data


# Dynamic chart with animation, no connection to the top-left slider
@app.callback(
    Output('dynamic-line-chart', 'figure'),
    Input('dynamic-line-chart', 'relayoutData')  # Use the internal chart for updates
)
def update_chart(_):
    initial_data, frames = calculate_chart_with_animation(df, df['Kolejka'].max())

    # Max cumulative points across all teams
    all_points = []
    for team in df['Druzyna G'].unique():
        team_data = df[(df['Druzyna G'] == team) | (df['Druzyna G.1'] == team)]
        team_points = 0
        for _, match in team_data.iterrows():
            home_goals, away_goals = map(int, match['Wynik'].split())
            if match['Druzyna G'] == team:
                home_points, _ = calculate_points(home_goals, away_goals)
                team_points += home_points
            elif match['Druzyna G.1'] == team:
                _, away_points = calculate_points(home_goals, away_goals)
                team_points += away_points
        all_points.append(team_points)

    max_points = max(all_points) if all_points else 10  # Dynamic y-axis limit

    fig = {
        'data': initial_data,
        'layout': go.Layout(
            title='Points Over Time',
            xaxis={'title': 'Kolejka', 'range': [1, df['Kolejka'].max()]},
            yaxis={'title': 'Points', 'range': [0, max_points]},  # Dynamic y-axis limit based on max cumulative points
            plot_bgcolor='black',
            paper_bgcolor='black',
            font=dict(color="white"),
            legend=dict(
                title='Teams',
                traceorder='normal',
                font=dict(color="white")
            ),
            updatemenus=[{
                'type': 'buttons',
                'showactive': False,
                'buttons': [
                    {
                        'label': 'Play',
                        'method': 'animate',
                        'args': [None, {'frame': {'duration': 1000, 'redraw': True}, 'fromcurrent': True}]
                    },
                    {
                        'label': 'Pause',
                        'method': 'animate',
                        'args': [[None], {'frame': {'duration': 0, 'redraw': False}, 'mode': 'immediate'}]
                    }
                ]
            }],
            sliders=[{  # This is the internal slider controlling the matchday and animation
                'steps': [{'args': [[str(k)], {'frame': {'duration': 1000, 'redraw': True}, 'mode': 'immediate'}], 
                           'label': str(k), 'method': 'animate'} for k in range(1, df['Kolejka'].max() + 1)],
                'currentvalue': {'prefix': 'Kolejka: ', 'font': {'color': 'white'}}
            }]
        ),
        'frames': frames
    }

    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
