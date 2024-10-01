import streamlit as st
import pandas as pd
import plotly.express as px

# Title of the app
st.title("GDP per Capita Choropleth Dashboard")

# Provide the URL of the Excel file hosted on GitHub
file_url = 'https://github.com/roxiecarbon/GDP/blob/main/imf-dm-export-20241002.xlsx'

# Load the Excel file from the GitHub URL
df = pd.read_excel(file_url)

# Replace 'no data' with NaN
df.replace('no data', pd.NA, inplace=True)

# Convert all GDP columns to numeric, forcing errors to NaN
df.iloc[:, 1:] = df.iloc[:, 1:].apply(pd.to_numeric, errors='coerce')

# Melt the data to make it suitable for animation (year as a column, not a separate field)
df_melted = pd.melt(df, id_vars=['GDP per capita, current prices (Purchasing power parity; international dollars per capita)'], 
                    var_name='Year', 
                    value_name='GDP per capita')

# Rename columns for clarity
df_melted.columns = ['Country', 'Year', 'GDP per capita']

# Filter out NaN values
df_melted = df_melted.dropna()

# Ensure 'Year' is treated as a string for proper animation display
df_melted['Year'] = df_melted['Year'].astype(str)

# Ensure GDP per capita is numeric (in case some stray text data is there)
df_melted['GDP per capita'] = pd.to_numeric(df_melted['GDP per capita'], errors='coerce')

# Create the color cap at the 90th percentile
gdp_percentile = df_melted.groupby('Year')['GDP per capita'].quantile(0.90).to_dict()

# Add a capped value for visualization
df_melted['Capped GDP per capita'] = df_melted.apply(lambda row: min(row['GDP per capita'], gdp_percentile[row['Year']]), axis=1)

# Create a choropleth map using Plotly with animation and proper color scaling
fig = px.choropleth(df_melted, 
                    locations='Country', 
                    locationmode='country names',
                    color='Capped GDP per capita',  # Use the capped GDP per capita
                    hover_name='Country', 
                    hover_data={'GDP per capita': True, 'Year': True},  # Ensure both GDP and Year are in hover
                    animation_frame='Year',  # Add the slider with the Year column
                    color_continuous_scale='RdYlGn',  # Light red to dark green
                    range_color=None,  # Remove fixed color range to allow auto-adjustment per year
                    title='GDP per Capita Over Time (Capped at 90th Percentile)')

# Update layout to include play/pause button and slider controls
fig.update_layout(
    coloraxis_colorbar={
        'title': 'GDP per Capita',
    },
    sliders=[{
        'currentvalue': {"prefix": "Year: "}
    }],
    updatemenus=[{
        'buttons': [
            {'args': [None, {'frame': {'duration': 500, 'redraw': True}, 'fromcurrent': True}], 'label': 'Play', 'method': 'animate'},
            {'args': [[None], {'frame': {'duration': 0, 'redraw': False}, 'mode': 'immediate'}], 'label': 'Pause', 'method': 'animate'}
        ],
        'direction': 'left',
        'pad': {'r': 10, 't': 87},
        'showactive': False,
        'type': 'buttons',
        'x': 0.1,
        'xanchor': 'right',
        'y': 0,
        'yanchor': 'top'
    }]
)

# Display the interactive Plotly chart in Streamlit
st.plotly_chart(fig)
