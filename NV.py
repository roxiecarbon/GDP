import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time

# Provide the correct raw URL of the Excel file hosted on GitHub
file_url = 'https://github.com/roxiecarbon/GDP/raw/main/nvda_us_d.xlsx'

# Load the Excel file from GitHub URL using openpyxl as the engine
df = pd.read_excel(file_url, engine='openpyxl')

# Rename columns to English for easier processing
df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']

# Convert 'Date' column to datetime format
df['Date'] = pd.to_datetime(df['Date'])

# Streamlit app layout
st.title('NVIDIA Stock Investment Growth Over Time')

# Input for the investment amount
investment_amount = st.number_input('Enter Investment Amount', value=120000000)

# Calculate the number of shares purchased based on the input investment amount
initial_price = df['Open'].iloc[0]
shares_purchased = investment_amount / initial_price

# Calculate the value of the investment over time
df['Investment Value'] = shares_purchased * df['Close']

# Create the animated figure using Plotly
fig = go.Figure()

# Add trace for the investment value over time
fig.add_trace(go.Scatter(x=df['Date'], y=df['Investment Value'], mode='lines', name='Investment Value'))

# Create frames for the animation (incremental steps of the drawing)
frames = [go.Frame(data=[go.Scatter(x=df['Date'][:k], y=df['Investment Value'][:k])],
                   name=str(k)) for k in range(1, len(df))]

# Set up the layout for the figure, including animation settings
fig.update_layout(
    title=f'NVIDIA Stock Investment Growth Over Time (${investment_amount} Initial Investment)',
    xaxis_title='Date',
    yaxis_title='Investment Value (USD)',
    updatemenus=[dict(type='buttons',
                      showactive=False,
                      buttons=[dict(label='Play',
                                    method='animate',
                                    args=[None, dict(frame=dict(duration=50, redraw=True),
                                                     fromcurrent=True, mode='immediate')]),
                               dict(label='Pause',
                                    method='animate',
                                    args=[[None], dict(frame=dict(duration=0, redraw=False),
                                                       mode='immediate')])])],
    xaxis_rangeslider_visible=True
)

# Add frames to the figure
fig.frames = frames

# Add a delay (e.g., 1 second) before starting the animation automatically
time.sleep(1)

# Start the animation after 1 second by simulating a click on the 'Play' button
fig.update_layout(updatemenus=[{
    'type': 'buttons',
    'buttons': [
        {
            'label': 'Play',
            'method': 'animate',
            'args': [None, {
                'frame': {'duration': 50, 'redraw': True},
                'fromcurrent': True, 'mode': 'immediate'
            }]
        },
        {
            'label': 'Pause',
            'method': 'animate',
            'args': [[None], {
                'frame': {'duration': 0, 'redraw': False},
                'mode': 'immediate'
            }]
        }
    ],
    'direction': 'left',
    'pad': {'r': 10, 't': 87},
    'showactive': False,
    'x': 0.1,
    'xanchor': 'right',
    'y': 0,
    'yanchor': 'top',
    'active': 0  # Automatically set the play button as active
}])

# Display the interactive Plotly chart in Streamlit
st.plotly_chart(fig)
