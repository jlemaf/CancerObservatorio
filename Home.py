import streamlit as st
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import altair as alt
import pydeck as pdk
from streamlit_folium import st_folium
import json
import pyproj
import plotly.graph_objs as go

st.set_page_config(
    page_title="Observatorio del Cáncer en Chile",
    #page_icon="🧊",
    
    layout="wide",
    initial_sidebar_state="expanded",
)

#---------------------------------------------------------------------------------------
####SESSION STATE VARIABLES#####

# Hide elements

#hide hamburger button
if 'hamburger' not in st.session_state:
    st.session_state['hamburger'] = """
<style>
.e1ugi8lo1.css-fblp2m.ex0cdmw0
{
    visibility:hidden;
}
"""

#hide footer
if 'footer' not in st.session_state:
    st.session_state['footer'] = """
<style>
.css-164nlkn.e1g8pov61
{
    visibility:hidden;
}
"""

#hide line
if 'line' not in st.session_state:
    st.session_state['line'] = """
<style>
.css-1dp5vir.e13qjvis1
{
    visibility:hidden;
}
"""

st.markdown(st.session_state.hamburger, unsafe_allow_html=True)
st.markdown(st.session_state.footer, unsafe_allow_html=True)
st.markdown(st.session_state.line, unsafe_allow_html=True)

#-----------------------------------------------------------------------------------

st.title('Observatorio del Cáncer en Chile')



def_16_22 = pd.read_csv('./data/defunciones_cancer_DEIS_2016_2022.csv', 
                       index_col=[0])
def_21_22 = pd.read_csv('./data/defunciones_cancer_DEIS_2021_2022.csv',
                       index_col=[0])

#with st.expander('Data'):
#    st.dataframe(def_16_22)
#st.dataframe(def_21_22)

col1, col2 = st.columns(2)

with col1:
    
    #Número de defunciones totales
    df_mujer=def_16_22.loc[def_16_22['GLOSA_SEXO'] == 'Mujer']
    df_hombre=def_16_22.loc[def_16_22['GLOSA_SEXO'] == 'Hombre']


    selection = alt.selection_single(fields=['GLOSA_SEXO'], bind='legend')

    title = alt.TitleParams('Año de Defunción',anchor='middle',fontSize=12)
    chart_m=alt.Chart(df_mujer[:1000]).mark_line(point={"filled": False,"fill": "white"}).encode(
                                x=alt.X('ANO_DEF:N', title='Año de defunción'),
                                y=alt.Y('count(ANO_DEF):Q', title='Número anual de defunciones',axis=alt.Axis(tickMinStep=1000)),
                                opacity=alt.condition(selection, alt.value(1), alt.value(0)),
                                color=alt.Color('GLOSA_SEXO', legend=alt.Legend(title='Sexo')),
                                tooltip=[alt.Tooltip('ANO_DEF:Q', title='Año defunción'),
                                         alt.Tooltip('count(ANO_DEF):Q', title='Número')]
        ).add_selection(selection)
    chart_h=alt.Chart(df_hombre[:1000]).mark_line(point={"filled": False,"fill": "white"}).encode(
                                x=alt.X('ANO_DEF:N', title='Año de defunción'),
                                y=alt.Y('count(ANO_DEF):Q', title='Número anual de defunciones',
                                axis=alt.Axis(tickMinStep=1000)),
                                opacity=alt.condition(selection,alt.value(1), alt.value(0)),
                                color=alt.Color('GLOSA_SEXO', legend=alt.Legend(title='Sexo')),
                                tooltip=[alt.Tooltip('ANO_DEF:Q', title='Año defunción'),
                                         alt.Tooltip('count(ANO_DEF):Q', title='Número')]
        )
    st.altair_chart(alt.layer(chart_m,chart_h).properties(title=title).configure(font='Sans Serif'),use_container_width=True)



    #Defunciones por edad

    alt.data_transformers.disable_max_rows()
    selection = alt.selection_single(fields=['GLOSA_SEXO'], bind='legend')
    title = alt.TitleParams('Decesos por Edad (2016-2022)', anchor='middle',fontSize=24)
    hombre=alt.Chart(df_hombre[:1000]).mark_bar().encode(
        x=alt.X('EDAD_CANT:Q',title='Edad'),
        y=alt.Y('count(EDAD_CANT):Q',title='Cantidad'),
        color=alt.Color('GLOSA_SEXO', legend=alt.Legend(title='Sexo')),
        opacity=alt.condition(selection,alt.value(1), alt.value(0)),
        tooltip=[alt.Tooltip('EDAD_CANT:Q', title='Edad'),alt.Tooltip('count(EDAD_CANT):Q',title='Cantidad')]).add_selection(selection)

    mujer=alt.Chart(df_mujer[:100]).mark_bar().encode(x='EDAD_CANT:Q',
                                           y='count(EDAD_CANT):Q',
                                           color='GLOSA_SEXO',
                                           opacity=alt.condition(selection,
                                                               alt.value(1), alt.value(0)),
                                           tooltip=[alt.Tooltip('EDAD_CANT:Q', title='Edad'),
                                                    alt.Tooltip('count(EDAD_CANT):Q', title='Cantidad')]
                                                 )

    st.altair_chart(alt.layer(hombre,mujer).properties(title=title),use_container_width=True)

    #Defunciones por tipo de cancer
    df_count = def_16_22['GLOSA_GRUPO_DIAG1'].value_counts().to_frame()
    df_tumors=def_16_22.groupby('GLOSA_GRUPO_DIAG1').agg( Mean=('EDAD_CANT','mean'),
                                          ).astype(int)

    df_tumors['Count'] = df_count['GLOSA_GRUPO_DIAG1']
    df_tumors.sort_values(by='Count', ascending=False,inplace=True)
    df_tumors.rename(columns={'Mean':'Edad promedio deceso','Count':'Decesos totales'},
                                                                       inplace=True)
    df_tumors.index.names = ['Tipos de Cáncer']
    
    st.header('Datos por tipo de cáncer (2016-2022)')
    st.subheader('Ampliar...')
    st.dataframe(df_tumors, use_container_width=True)

with col2:

  
    from textwrap import wrap
    alt.data_transformers.disable_max_rows()

    #def_16_22 = pd.read_csv('./data/defunciones_cancer_DEIS_2016_2022.csv', 
    #                       index_col=[0])
    # Wrap on whitespace with a max line length of 30 chars
    #def_16_22['GLOSA_GRUPO_DIAG1'] = def_16_22['GLOSA_GRUPO_DIAG1'].apply(wrap, args=[30])


    title = alt.TitleParams('Edad de Decesos por Tipos de Cáncer', anchor='middle',fontSize=14)

    chart=alt.Chart(def_16_22[:1000]).transform_density(
        "EDAD_CANT",
        as_=["EDAD_CANT", "density"],
        groupby=['GLOSA_GRUPO_DIAG1']
    ).mark_area().encode(
        x=alt.X("EDAD_CANT:Q",title='Edad'),
        y=alt.Y("density:Q", stack="center", title=None, 
                impute=None, 
                scale=alt.Scale(nice=False, zero=False),
                axis=alt.Axis(labels=False, values=[0],grid=False, ticks=True)),
        color='GLOSA_GRUPO_DIAG1:N',
        row=alt.Row( 'GLOSA_GRUPO_DIAG1:N',
            header=alt.Header(
                title=None,
             labels=False), spacing=0, align='none')
    ).properties(title=title,height=100).configure_facet(
              spacing=0,
    ).configure_view(
            continuousHeight=10,  continuousWidth=250,
            discreteHeight=100,  discreteWidth=250,

        stroke='#ddd')

    
    st.altair_chart(chart) #use_container_width=True)

import plotly.graph_objects as go
from plotly.colors import n_colors

# 12 sets of normal distributed random data, with increasing mean and standard deviation
df_gby=def_16_22.groupby(['GLOSA_GRUPO_DIAG1','EDAD_CANT']).count()
query=df_gby.index.get_level_values(0).unique()
#print(query)
dfs_tipos=[[x,df_gby.loc[x]] for x in query]

colors = n_colors('rgb(5, 200, 200)', 'rgb(200, 10, 10)', len(dfs_tipos), colortype='rgb')

fig = go.Figure()
for data_line, color in zip(dfs_tipos, colors):
    #print(data_line[1].index,color)
    fig.add_trace(go.Violin(x=data_line[1].index, line_color=color,name=data_line[0],legend=None))

fig.update_traces(orientation='h', side='positive', width=1, points=False)
fig.update_layout(xaxis_showgrid=True, xaxis_zeroline=False,showlegend=False,
                  title="Defunciones por edad en tipos de cáncer", xaxis_title='EDAD')

st.plotly_chart(fig, use_container_width=True)

#fig = go.Figure()
#for data_line, color in zip(data, colors):
#    fig.add_trace(go.Violin(x=data_line, line_color=color))

#fig.update_traces(orientation='h', side='positive', width=3, points=False)
#fig.update_layout(xaxis_showgrid=False, xaxis_zeroline=False)
#st.plotly_chart(fig)