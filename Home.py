import streamlit as st
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import altair as alt
import pydeck as pdk
import json
import pyproj
import plotly.graph_objs as go
from textwrap import wrap
import sys
sys.path.insert(1, '.')



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
if 'pie_type' not in st.session_state:
    st.session_state['pie_type'] = 'Todos'
if 'filt_df' not in st.session_state:
    st.session_state['filt_df'] = [2016,2022]

st.title('Observatorio del Cáncer en Chile')
st.divider()

def_16_22 = pd.read_csv('./data/defunciones_cancer_DEIS_2016_2022.csv', 
                       index_col=[0])
def_21_22 = pd.read_csv('./data/defunciones_cancer_DEIS_2021_2022.csv',
                       index_col=[0])

df = pd.concat([def_16_22, def_21_22]).drop_duplicates()
#with st.expander('Data'):
#    st.dataframe(def_16_22)
#st.dataframe(def_21_22)
datapoints=df.shape[0]
datapoint_m=df.loc[df['GLOSA_SEXO']=='Mujer'].shape[0]
datapoint_h=df.loc[df['GLOSA_SEXO']=='Hombre'].shape[0]
mean_age = f"{df['EDAD_CANT'].mean():.2f}"
mean_age_m = f"{df.loc[df['GLOSA_SEXO']=='Mujer']['EDAD_CANT'].mean():.2f}"
mean_age_h = f"{df.loc[df['GLOSA_SEXO']=='Hombre']['EDAD_CANT'].mean():.2f}"
st.markdown(f'Durante los años 2016 a 2022 se han registrado: **{datapoints}** decesos por cáncer.')
st.markdown(f'De estos **{datapoint_m} ({(datapoint_m/datapoints)*100:.2f}%)** son mujeres y **{datapoint_h} ({datapoint_h/datapoints*100:.2f}%)** son hombres.')
st.markdown(f"La edad promedio de fallecimiento es de {mean_age} años, {mean_age_m} años para mujeres y {mean_age_h} años para hombres" )


st.divider()

def filt_df(df, min, max):
    df2=df.loc[df['ANO_DEF'].ge(min) & df['ANO_DEF'].le(max)]
    return df2

year_range=st.slider("Seleccionar un rango de años",value=[2016,2022],min_value=2016,max_value=2022,
                     key='slider_years',on_change=filt_df, args=(df, st.session_state.filt_df[0],st.session_state.filt_df[1]))

st.write(year_range[0],year_range[1])

df = filt_df(df, year_range[0], year_range[1])

col1, col2 = st.columns(2)

with col1:
    
    #Número de defunciones totales
    @st.cache_data
    def def_line(df):
        df_mujer=df.loc[df['GLOSA_SEXO'] == 'Mujer']
        df_hombre=df.loc[df['GLOSA_SEXO'] == 'Hombre']


        selection = alt.selection_single(fields=['GLOSA_SEXO'], bind='legend')

        title = alt.TitleParams('Año de Defunción',anchor='middle',fontSize=12)
        chart_m=alt.Chart(df_mujer).mark_line(point={"filled": False,"fill": "white"}).encode(
                                    x=alt.X('ANO_DEF:N', title='Año de defunción'),
                                    y=alt.Y('count(ANO_DEF):Q', title='Número anual de defunciones',axis=alt.Axis(tickMinStep=1000)),
                                    opacity=alt.condition(selection, alt.value(1), alt.value(0)),
                                    color=alt.Color('GLOSA_SEXO', legend=alt.Legend(title='Sexo')),
                                    tooltip=[alt.Tooltip('ANO_DEF:Q', title='Año defunción'),
                                             alt.Tooltip('count(ANO_DEF):Q', title='Número')]
            ).add_selection(selection)
        chart_h=alt.Chart(df_hombre).mark_line(point={"filled": False,"fill": "white"}).encode(
                                    x=alt.X('ANO_DEF:N', title='Año de defunción'),
                                    y=alt.Y('count(ANO_DEF):Q', title='Número anual de defunciones',
                                    axis=alt.Axis(tickMinStep=1000)),
                                    opacity=alt.condition(selection,alt.value(1), alt.value(0)),
                                    color=alt.Color('GLOSA_SEXO', legend=alt.Legend(title='Sexo')),
                                    tooltip=[alt.Tooltip('ANO_DEF:Q', title='Año defunción'),
                                             alt.Tooltip('count(ANO_DEF):Q', title='Número')]
            )
        chart=alt.layer(chart_m,chart_h).properties(title=title).configure(font='Sans Serif')
        return chart
    
    chart=def_line(df)
    #st.altair_chart(chart,use_container_width=True)
 
    st.divider()


    #Histograma defunciones por edad
    @st.cache_data 
    def def_hist(df):
        df_mujer=df.loc[df['GLOSA_SEXO'] == 'Mujer']
        df_hombre=df.loc[df['GLOSA_SEXO'] == 'Hombre']
        alt.data_transformers.disable_max_rows()
        selection = alt.selection_single(fields=['GLOSA_SEXO'], bind='legend')
        title = alt.TitleParams('Decesos por Edad (2016-2022)', anchor='middle',fontSize=24)
        hombre=alt.Chart(df_hombre).mark_bar().encode(
            x=alt.X('EDAD_CANT:Q',title='Edad'),
            y=alt.Y('count(EDAD_CANT):Q',title='Cantidad'),
            color=alt.Color('GLOSA_SEXO', legend=alt.Legend(title='Sexo')),
            opacity=alt.condition(selection,alt.value(1), alt.value(0)),
            tooltip=[alt.Tooltip('EDAD_CANT:Q', title='Edad'),alt.Tooltip('count(EDAD_CANT):Q',title='Cantidad')]).add_selection(selection)

        mujer=alt.Chart(df_mujer).mark_bar().encode(x='EDAD_CANT:Q',
                                               y='count(EDAD_CANT):Q',
                                               color='GLOSA_SEXO',
                                               opacity=alt.condition(selection,
                                                                   alt.value(1), alt.value(0)),
                                               tooltip=[alt.Tooltip('EDAD_CANT:Q', title='Edad'),
                                                        alt.Tooltip('count(EDAD_CANT):Q', title='Cantidad')]
                                                     )
        chart = alt.layer(hombre,mujer).properties(title=title)
        return chart

    chart = def_hist(df)
    #st.altair_chart(chart,use_container_width=True)
    st.divider()


with col2:
    alt.data_transformers.disable_max_rows()

    @st.cache_data
    def violin_plot(df):

        #def_16_22 = pd.read_csv('./data/defunciones_cancer_DEIS_2016_2022.csv', 
        #                       index_col=[0])
        # Wrap on whitespace with a max line length of 30 chars
        #def_16_22['GLOSA_GRUPO_DIAG1'] = def_16_22['GLOSA_GRUPO_DIAG1'].apply(wrap, args=[30])


        title = alt.TitleParams('Edad de Decesos por Tipos de Cáncer', anchor='middle',fontSize=14)

        chart=alt.Chart(df).transform_density(
            "EDAD_CANT",
            as_=["EDAD_CANT", "density"],
            groupby=['GLOSA_GRUPO_DIAG1']
        ).mark_area().encode(
            x=alt.X("EDAD_CANT:Q",title='Edad'),
            y=alt.Y("density:Q", stack="center", title=None, 
                    impute=None, 
                    scale=alt.Scale(nice=False, zero=False),
                    axis=alt.Axis(labels=False, values=[0],grid=False, ticks=True)),
            color=alt.Color('GLOSA_GRUPO_DIAG1:N',  legend=alt.Legend(title='Tipo de Cáncer')),
            tooltip=[alt.Tooltip('EDAD_CANT:Q',format='.02',title='Edad'),
                     alt.Tooltip('density:Q',format='.02%',title='Porcentaje'),
                     alt.Tooltip('GLOSA_GRUPO_DIAG1',title='Tipo')],
            row=alt.Row( 'GLOSA_GRUPO_DIAG1:N', center=True,
                header=alt.Header(
                    title=None,
                 labels=False), spacing=0, align='none',)
        ).properties(title=title).configure_facet(
                  spacing=0,
        ).configure_view(
                continuousHeight=25,  continuousWidth=250,
                discreteHeight=100,  discreteWidth=250,

            stroke='#ddd')
        return chart
    
    chart = violin_plot(df)
    st.altair_chart(chart) #use_container_width=True)

    st.divider()

    #Pie de lugar defuncion
    fig = go.Figure(data=[go.Pie(labels=df['LUGAR_DEFUNCION'],values=df['ANO_DEF'].value_counts(), title='Lugar de Defunción')])
    st.plotly_chart(fig, use_container_width=False)
   
   
   
#Defunciones por tipo de cancer
@st.cache_data
def def_pie_type(df, sexo): 
    if sexo=='Todos':
        df_count = df['GLOSA_GRUPO_DIAG1'].value_counts().to_frame()
        df_tumors=df.groupby('GLOSA_GRUPO_DIAG1').agg( Mean=('EDAD_CANT','mean'), 
                                    ).astype(int)
    elif sexo=='Mujer':
        df_m = df[df['GLOSA_SEXO'] == 'Mujer']
        df_count = df_m['GLOSA_GRUPO_DIAG1'].value_counts().to_frame()
        df_tumors=df_m.groupby('GLOSA_GRUPO_DIAG1').agg( Mean=('EDAD_CANT','mean'),
                                    ).astype(int)
    elif sexo=='Hombre':
        df_h = df[df['GLOSA_SEXO'] == 'Hombre']
        df_count = df_h['GLOSA_GRUPO_DIAG1'].value_counts().to_frame()
        df_tumors=df_h.groupby('GLOSA_GRUPO_DIAG1').agg( Mean=('EDAD_CANT','mean'),
                                    ).astype(int)
    df_tumors['Count'] = df_count['GLOSA_GRUPO_DIAG1']
    df_tumors.sort_values(by='Count', ascending=False,inplace=True)
    df_tumors.rename(columns={'Mean':'Edad promedio deceso','Count':'Decesos totales'},
                                                                inplace=True)
    df_tumors.index.names = ['Tipos de Cáncer']
    indexes=df_tumors.index.to_frame()
    fig = go.Figure(data=[go.Pie(labels=indexes,values=df_tumors['Decesos totales'], title=df.index.name)])
    fig.update_layout(title='Defunciones por tipos de Cáncer')
    return fig

st.header('Datos por tipo de cáncer (2016-2022)')

sb_pie = st.selectbox('Seleccionar sexo', ('Todos','Mujer', 'Hombre'), key='pie_type',
             on_change=def_pie_type,args=(df,st.session_state.pie_type))
#st.plotly_chart(def_pie_type(df,sb_pie), use_container_width=True)




import plotly.graph_objects as go
from plotly.colors import n_colors

# 12 sets of normal distributed random data, with increasing mean and standard deviation
df_gby=df.groupby(['GLOSA_GRUPO_DIAG1','EDAD_CANT']).count()
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

#st.plotly_chart(fig, use_container_width=True)

#fig = go.Figure()
#for data_line, color in zip(data, colors):
#    fig.add_trace(go.Violin(x=data_line, line_color=color))

#fig.update_traces(orientation='h', side='positive', width=3, points=False)
#fig.update_layout(xaxis_showgrid=False, xaxis_zeroline=False)
#st.plotly_chart(fig)