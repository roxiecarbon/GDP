import streamlit as st
import pandas as pd
import plotly.express as px

# Title of the app
st.title("GDP per Capita Choropleth Dashboard")

# Provide the correct raw URL of the Excel file hosted on GitHub
file_url = 'https://github.com/roxiecarbon/GDP/raw/main/imf-dm-export-20241002.xlsx'

# Load the Excel file from the GitHub URL
df = pd.read_excel(file_url)

# Rest of your existing code remains unchanged
df.replace('no data', pd.NA, inplace=True)
df.iloc[:, 1:] = df.iloc[:, 1:].apply(pd.to_numeric, errors='coerce')

# Continue with the melting, renaming, and plotting code
df_melted = pd.melt(df, id_vars=['GDP per capita, current prices (U.S. dollars per capita)'], 
                    var_name='Year', 
                    value_name='GDP per capita')

df_melted.columns = ['Country', 'Year', 'GDP per capita']
df_melted = df_melted.dropna()
df_melted['Year'] = df_melted['Year'].astype(str)
df_melted['GDP per capita'] = pd.to_numeric(df_melted['GDP per capita'], errors='coerce')

gdp_percentile = df_melted.groupby('Year')['GDP per capita'].quantile(0.90).to_dict()
df_melted['Capped GDP per capita'] = df_melted.apply(lambda row: min(row['GDP per capita'], gdp_percentile[row['Year']]), axis=1)

fig = px.choropleth(df_melted, 
                    locations='Country', 
                    locationmode='country names',
                    color='Capped GDP per capita',  
                    hover_name='Country', 
                    hover_data={'GDP per capita': True, 'Year': True},  
                    animation_frame='Year',  
                    color_continuous_scale='RdYlGn',
                    title='GDP per Capita Over Time (Capped at 90th Percentile)')

fig.update_layout(
    coloraxis_colorbar={'title': 'GDP per Capita'},
    sliders=[{'currentvalue': {"prefix": "Year: "}}],
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
