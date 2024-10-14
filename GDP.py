import pandas as pd
import plotly.graph_objs as go
import streamlit as st

# Load the Excel file from the GitHub URL
file_url = 'https://github.com/roxiecarbon/GDP/raw/main/Zeszyt1.xlsx'
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
    teams = sorted(dataframe['Druzyna G'].unique())
    frames = []
    initial_data = []
    all_points = {team: [0] for team in teams}  

    for i in range(1, max_kolejka + 1):
        for team in teams:
            team_data = dataframe[(dataframe['Druzyna G'] == team) | (dataframe['Druzyna G.1'] == team)]
            points = all_points[team][-1]  

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

            all_points[team].append(points)

    for i in range(1, max_kolejka + 1):
        frame_data = []
        for team in teams:
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

    for team in teams:
        initial_data.append(go.Scatter(
            x=[1], y=[0], mode='lines+markers', name=team, line=dict(color=team_colors.get(team, 'gray'), shape='spline')
        ))

    return initial_data, frames

# Streamlit app layout
st.title('Tabela Ligowa')

# Slider for selecting "Kolejka"
selected_kolejka = st.slider(
    'Wybierz Kolejkę',
    min_value=int(df['Kolejka'].min()),
    max_value=int(df['Kolejka'].max()),
    value=int(df['Kolejka'].min())
)

# Display the league table
st.subheader('Tabela')
table_df = calculate_table(df, selected_kolejka)
st.dataframe(table_df)

# Display the animated points chart
st.subheader('Points Over Time')

initial_data, frames = calculate_chart_with_animation(df, df['Kolejka'].max())

max_points = max(table_df['Punkty']) if not table_df.empty else 10

fig = go.Figure(
    data=initial_data,
    layout=go.Layout(
        title='Points Over Time',
        xaxis={'title': 'Kolejka', 'range': [1, df['Kolejka'].max()]},
        yaxis={'title': 'Points', 'range': [0, max_points]},
        plot_bgcolor='black',
        paper_bgcolor='black',
        font=dict(color="white"),
        sliders=[{
            'steps': [{'args': [[str(k)], {'frame': {'duration': 1000, 'redraw': True}, 'mode': 'immediate'}], 
                       'label': str(k), 'method': 'animate'} for k in range(1, df['Kolejka'].max() + 1)],
            'currentvalue': {'prefix': 'Kolejka: ', 'font': {'color': 'white'}}
        }]
    ),
    frames=frames
)

# Display the chart in Streamlit
st.plotly_chart(fig)
