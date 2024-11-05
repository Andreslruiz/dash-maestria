import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html
import dash_bootstrap_components as dbc

# Solo una definición del objeto Dash
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Cargar los datos
# base_path = "C:/Users/andre/OneDrive/Escritorio/Maestria IA/Semestre 1/Aplicaciones I/Actividad 4 -Carlos Andres Loaiza Ruiz/"
base_path = ''
df_muertes = pd.read_excel(f"{base_path}datos_mortalidad.xlsx", sheet_name="No_Fetales_2019")
df_departamentos = pd.read_excel(f"{base_path}divipola.xlsx", sheet_name="Hoja1")

# Agrupar las muertes por COD_MUNICIPIO para contar las muertes por municipio
df_totales_muertes = df_muertes.groupby('COD_MUNICIPIO').size().reset_index(name='TOTAL_MUERTES')

# Combina df_totales_muertes con df_departamentos para incluir MUNICIPIO y DEPARTAMENTO
df_completo = pd.merge(
    df_totales_muertes,
    df_departamentos[['COD_MUNICIPIO', 'MUNICIPIO', 'COD_DEPARTAMENTO', 'DEPARTAMENTO']],
    on='COD_MUNICIPIO',
    how='left'
)

gdf_colombia = gpd.read_file(f"{base_path}colombia_departamentos.geojson")

gdf_colombia["DEPARTAMENTO"] = gdf_colombia["NOMBRE_DPT"].str.lower()
df_completo["DEPARTAMENTO"] = df_completo["DEPARTAMENTO"].str.lower()

gdf_colombia = gdf_colombia.merge(df_completo, on="DEPARTAMENTO", how="left")

# Gráfico de mapa
fig_map = px.choropleth(
    gdf_colombia,
    geojson=gdf_colombia.geometry,
    locations=gdf_colombia.index,
    color="TOTAL_MUERTES",
    hover_name="DEPARTAMENTO",
    title="Distribución Total de Muertes por Departamento en Colombia (2019)",
    color_continuous_scale="Reds"
)
fig_map.update_geos(fitbounds="locations", visible=False)

# b) Gráfico de líneas: total de muertes por meses
df_muertes['FECHA'] = pd.to_datetime(df_muertes['AÑO'].astype(str) + '-' + df_muertes['MES'].astype(str) + '-01')
muertes_por_mes = df_muertes.groupby('FECHA').size().reset_index(name='TOTAL_MUERTES_MENSUALES')

fig_line = px.line(
    muertes_por_mes, x='FECHA', y='TOTAL_MUERTES_MENSUALES',
    title='Representación del total de muertes por meses en Colombia, mostrando las variaciones mensuales'
)

# c) Gráfico de barras: 5 ciudades más violentas
df_homicidios = df_muertes[df_muertes['MANERA_MUERTE'] == 'Homicidio']

df_homicidios_merged = pd.merge(
    df_homicidios,
    df_departamentos[['COD_MUNICIPIO', 'MUNICIPIO']],
    on='COD_MUNICIPIO',
    how='left'
)

homicidios_por_municipio = df_homicidios_merged.groupby('MUNICIPIO').size().reset_index(name='TOTAL_HOMICIDIOS')
top_5_homicidios = homicidios_por_municipio.nlargest(5, 'TOTAL_HOMICIDIOS')

fig_bar = px.bar(
    top_5_homicidios,
    x='MUNICIPIO',
    y='TOTAL_HOMICIDIOS',
    title='Top 5 Municipios con Más Homicidios en Colombia',
    labels={'MUNICIPIO': 'Municipio', 'TOTAL_HOMICIDIOS': 'Total Homicidios'},
    color='MUNICIPIO'
)

# d) Gráfico circular: 10 ciudades con menor índice de muertes
ciudades_menor_muertes = df_completo.groupby('MUNICIPIO').size().nsmallest(10).reset_index(name='TOTAL_MUERTES')
fig_pie = px.pie(
    ciudades_menor_muertes, names='MUNICIPIO', values='TOTAL_MUERTES',
    title='Gráfico que muestra las 10 ciudades con el menor índice de muertes en Colombia'
)

# e) Tabla: 10 principales causas de muerte
top_causas_muerte = df_muertes.groupby('MANERA_MUERTE').size().reset_index(name='TOTAL_MUERTES')
top_causas_muerte = top_causas_muerte.sort_values(by='TOTAL_MUERTES', ascending=False).head(10)

table_fig = go.Figure(
    data=[go.Table(
        header=dict(
            values=['Causa de Muerte', 'Total'],
            fill_color='paleturquoise',
            align='left'
        ),
        cells=dict(
            values=[top_causas_muerte['MANERA_MUERTE'], top_causas_muerte['TOTAL_MUERTES']],
            fill_color='lavender',
            align='left'
        ))
    ]
)

# f) Histograma: Distribución de muertes según rangos de edad
df_muertes['GRUPO_EDAD'] = df_muertes['GRUPO_EDAD'].astype(str)
df_muertes['GRUPO_EDAD'] = df_muertes['GRUPO_EDAD'].str.replace(' años', '')
df_muertes['EDAD_RANGO'] = pd.cut(
    df_muertes['GRUPO_EDAD'].astype(int), 
    bins=[0, 4, 9, 14, 19, 24, 29, 34, 39, 44, 49, 54, 59, 64, 69, 74, 79, 84, 89, 94, 100], 
    labels=["0-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-54", "55-59", "60-64", "65-69", "70-74", "75-79", "80-84", "85-89", "90-94", "95-100"]
)
fig_hist = px.histogram(df_muertes, x='EDAD_RANGO', title='Distribución de muertes según rangos de edad quinquenales')

# g) Gráfico de barras apiladas: Total de muertes por sexo
df_muertes['SEXO'] = df_muertes['SEXO'].replace({1: 'Masculino', 2: 'Femenino'})
muertes_por_sexo = df_muertes.groupby(['COD_DEPARTAMENTO', 'SEXO']).size().unstack(fill_value=0)
fig_stacked_bar = px.bar(
    muertes_por_sexo, title='Comparativa del total de muertes por sexo en cada departamento',
    labels={'value': 'Total de Muertes', 'COD_DEPARTAMENTO': 'Departamento'}
)

# Definición del layout de la aplicación
app.layout = html.Div([
    html.H3("Carlos Andrés Loaiza Ruiz"),
    html.H4("Maestría en Inteligencia Artificial"),
    html.H4("Universidad de La Salle"),
    html.H4("Materia: Aplicaciones I"),

    html.Div([
        html.Div([dcc.Graph(figure=fig_map)]),
        html.Div([dcc.Graph(figure=fig_line)]),
        html.Div([dcc.Graph(figure=fig_bar)]),
        html.Div([dcc.Graph(figure=fig_pie)]),
        html.Div([dcc.Graph(figure=table_fig)]),
        html.Div([dcc.Graph(figure=fig_hist)]),
        html.Div([dcc.Graph(figure=fig_stacked_bar)])
    ])
])

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=False)
