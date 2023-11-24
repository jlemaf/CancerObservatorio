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

from Home import def_line, def_hist
#---------------------------------------------------------------------------------------
####SESSION STATE VARIABLES#####

st.set_page_config(page_title='Mapa del Cáncer en Chile')#, page_icon = favicon, layout = 'wide', initial_sidebar_state = 'auto')
# favicon being an object of the same kind as the one you should provide st.image() with (ie. a PIL array for example) or a string (url or local file path)

# Hide elements

#hide hamburger button
st.session_state['hamburger'] = """
<style>
.e1ugi8lo1.css-fblp2m.ex0cdmw0
{
    visibility:hidden;
}
"""

#hide footer
st.session_state['footer'] = """
<style>
.css-h5rgaw.e1g8pov61
{
    visibility:hidden;
}
"""

#hide line
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


st.title('Mapa del Cáncer en Chile')

if 'region' not in st.session_state:
    st.session_state['region'] = 'Del Bíobío'
if 'pie_type' not in st.session_state:
    st.session_state['pie_type'] = 'Todos'
if 'filt_df' not in st.session_state:
    st.session_state['filt_df'] = [2016,2022]
#if 'color' not in st.session_state:
#    st.session_state['color'] = 'viridis'

df_shpfile = gpd.read_file('./shape/Chile_Simp_Comunas_data_sex_5.shp')

map_df = df_shpfile 
map_df.to_crs(pyproj.CRS.from_epsg(4326), inplace=True)
Lat = map_df['Lat']
Long = map_df['Long']

# set GeoJSON file path
path = r"./shape/Chile_Simp_Comunas_data_sex_5_2.geojson"

# write GeoJSON to file
#map_df.to_file(path, driver = "GeoJSON")
with open(path) as geofile:
    j_file = json.load(geofile)
    
# index geojson
i=1
for feature in j_file["features"]:
    feature ['id'] = str(i).zfill(2)
    i += 1


# load data
def_16_22 = pd.read_csv('./data/defunciones_cancer_DEIS_2016_2022.csv', 
                       index_col=[0])
def_21_22 = pd.read_csv('./data/defunciones_cancer_DEIS_2021_2022.csv',
                       index_col=[0])
def_16_22 = pd.concat([def_16_22, def_21_22]).drop_duplicates()

regiones = list(set(def_16_22['GLOSA_REG_RES'].values))

with st.container():
    @st.cache_data
    def map_maker(region,color):
        #st.session_state['region'] = region
        latlon = {'País': {'lat': -37, 'lon': -70, 'zoom':3},
              'De Arica y Parinacota': {'lat':-19,'lon':-70,'zoom':7},
              'De Tarapacá':{'lat':-20,'lon':-70,'zoom':6},
              'De Antofagasta':{'lat':-23.5,'lon':-70,'zoom':6},
              'De Atacama':{'lat':-27.5,'lon':-70,'zoom':6},
              'De Coquimbo':{'lat':-30, 'lon':-71,'zoom':7},
              'De Valparaíso':{'lat':-33,'lon':-71,'zoom':7},
              'Metropolitana de Santiago':{'lat':-33.5,'lon':-70.6,'zoom':7.5},
              "Del Libertador B. O'Higgins" : {'lat':-34.5,'lon':-71,'zoom':7.5},
              'Del Maule': {'lat':-35.5,'lon':-71.5,'zoom':7},
              'De Ñuble': {'lat':-36.5, 'lon':-72,'zoom':7},
              'Del Bíobío':{'lat':-37.5, 'lon':-72.5, 'zoom':7}, 
              'De La Araucanía': {'lat':-38.5,'lon':-72.5,'zoom':7},  
              'De Los Ríos':{'lat':-40,'lon':-73,'zoom':7},
              'De Los Lagos':{'lat':-42,'lon':-73,'zoom':6},
              'De Aisén del Gral. C. Ibáñez del Campo':{'lat':-46,'lon':-73,'zoom':5},
               'De Magallanes y de La Antártica Chilena': {'lat': -52, 'lon':-73,'zoom':5} }
        if region == 'País':
            df = def_16_22
        else:
            filt=(def_16_22['GLOSA_REG_RES'] == region)
            df = def_16_22.loc[filt]

        df.rename(columns={'GLOSA_COMUNA_RESIDENCIA':'Comuna'}, inplace=True, errors='raise')
        df_ncasos=df['Comuna'].value_counts().to_frame().rename(columns={'Comuna':'n_casos'})
        df_ncasos['p_casos'] = round((df_ncasos['n_casos'] / df_ncasos.sum()['n_casos'] *100), 2)
        df_nmujer=df[df['GLOSA_SEXO']=='Mujer']['Comuna'].value_counts().to_frame().rename(columns={'Comuna':'n_mujer'})
        df_nhombre=df[df['GLOSA_SEXO']=='Hombre']['Comuna'].value_counts().to_frame().rename(columns={'Comuna':'n_hombre'})
        df_ncasos['n_mujer'] = df_nmujer['n_mujer']
        df_ncasos['p_mujer'] = round((df_ncasos['n_mujer'] / df_ncasos['n_mujer'].sum())*100, 3)
        df_ncasos['n_hombre'] = df_nhombre['n_hombre']
        df_ncasos['p_hombre'] = round((df_ncasos['n_hombre'] / df_ncasos['n_hombre'].sum())*100, 3)

    
        #st.dataframe(n_casos)
        mapboxt = 'MapBox Token'
        choro = go.Choroplethmapbox(z=df_ncasos['n_casos'],  
                                locations = df_ncasos.index, 
                                colorscale = color,#Viridis', #Revisa estilos
                                geojson = j_file, 
                                featureidkey='properties.Comuna',
                                #text=df_ncasos['Comuna'],
                                hoverlabel={'font_size':15, 'font_family':'Courier New'},
                                customdata=np.stack([df_ncasos['n_mujer'], df_ncasos['n_hombre'],
                                                     df_ncasos['p_mujer'], df_ncasos['p_hombre'],
                                                     df_ncasos['p_casos']],axis=1),
                                hovertemplate="<b>Comuna</b>: %{location}<br>"+"<b>Número de casos</b>: %{z}(%{customdata[4]}%\rregional)<br>"+"<b>Casos (mujer)</b>:%{customdata[0]}(%{customdata[2]}%)<br>"+"<b>Casos (hombre)</b>:%{customdata[1]}(%{customdata[3]}%)"+"<extra></extra>",
                                #hovertext='%{text}',
                                marker_line_width=0.1) 
        scatt = go.Scattermapbox(lat=Lat, lon=Long,
                             mode='markers+text',    
                             below='False', 
                             marker=dict( size=12, color ='rgb(56, 44, 100)'))
        layout = go.Layout(title_text ='Números de Defunciones por Cáncer en Chile por región (2016-2022)', 
                       title_x = 0.2,  
                       width=950, height=700,
                       mapbox = dict(center= dict(lat=latlon[region]['lat'],  lon=latlon[region]['lon']),
                                     accesstoken= mapboxt, 
                                     zoom=latlon[region]['zoom'],
                                     style="carto-positron"))

        #choro, layout = map_maker(map_df=map_df)
        # assign Graph Objects figure
        fig = go.Figure(data=choro, layout=layout)
        fig.update_geos(fitbounds="locations")
        #fig = st.plotly_chart(fig, use_container_width=True)
        return fig



    color_scales=['aggrnyl', 'agsunset', 'algae', 'amp', 'armyrose', 'balance', 'blackbody', 'bluered', 'blues', 'blugrn', 'bluyl', 'brbg', 'brwnyl', 'bugn', 'bupu', 'burg', 'burgyl', 'cividis', 'curl', 'darkmint', 'deep', 'delta', 'dense', 'earth', 'edge', 'electric', 'emrld', 'fall', 'geyser', 'gnbu', 'gray', 'greens', 'greys', 'haline', 'hot', 'hsv', 'ice', 'icefire', 'inferno', 'jet', 'magenta', 'magma', 'matter', 'mint', 'mrybm', 'mygbm', 'oranges', 'orrd', 'oryel', 'oxy', 'peach', 'phase', 'picnic', 'pinkyl', 'piyg', 'plasma', 'plotly3', 'portland', 'prgn', 'pubu', 'pubugn', 'puor', 'purd', 'purp', 'purples', 'purpor', 'rainbow', 'rdbu', 'rdgy', 'rdpu', 'rdylbu', 'rdylgn', 'redor', 'reds', 'solar', 'spectral', 'speed', 'sunset', 'sunsetdark', 'teal', 'tealgrn', 'tealrose', 'tempo', 'temps', 'thermal', 'tropic', 'turbid', 'turbo', 'twilight', 'viridis', 'ylgn', 'ylgnbu', 'ylorbr', 'ylorrd'] # Appending '_r' to a named colorscale reverses it.

    #selectbox
    sb_region=st.selectbox("Seleccione Región:", regiones + ['País'], 
                 key='region', on_change=map_maker,args=(st.session_state.region, 'viridis'))


    color_sel=["aggrnyl", "amp", "algae",  "blugrn", "cividis", "deep", "emrld", "greys","ice_r", "teal", "viridis","viridis_r"]
    #for color in color_sel:
    #    st.write(color)
    color='viridis'
    st.plotly_chart(map_maker(sb_region, color), use_container_width=True)

    if sb_region == 'País':
        df = def_16_22
    else:
        filt=(def_16_22['GLOSA_REG_RES'] == sb_region)
        df = def_16_22.loc[filt]


    def filt_df(df, min, max):
        df2=df.loc[df['ANO_DEF'].ge(min) & df['ANO_DEF'].le(max)]
        return df2

    year_range=st.slider("Seleccionar un rango de años",value=[2016,2022],min_value=2016,max_value=2022, key='slider_years',on_change=filt_df, args=(df, st.session_state.filt_df[0],st.session_state.filt_df[1]))

    st.write(f"Rango de años: {year_range[0]} - {year_range[1]}")

    df = filt_df(df, year_range[0], year_range[1])


    col1, col2 = st.columns(2)

    with col1:
        st.altair_chart(def_line(df), use_container_width=True)
        st.altair_chart(def_hist(df), use_container_width=True)

    with col2:
        #st.altair_chart(violin_plot(df), use_container_width=True)
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
                tooltip=[alt.Tooltip('EDAD_CANT:Q', format='.02',title='Edad'),
                         alt.Tooltip('density:Q',format='.02%',title='Porcentaje'),
                         alt.Tooltip('GLOSA_GRUPO_DIAG1',title='Tipo')],
               
                row=alt.Row( 'GLOSA_GRUPO_DIAG1:N', center=True,
                    header=alt.Header(
                        title=None,
                     labels=False), spacing=0, align='none')
            ).properties(title=title).configure_facet(
                      spacing=0,
            ).configure_view(
                    continuousHeight=35,  continuousWidth=250,
                    discreteHeight=100,  discreteWidth=250,

                stroke='#ddd')
        st.altair_chart(chart)

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
    st.plotly_chart(def_pie_type(df,sb_pie), use_container_width=True)
