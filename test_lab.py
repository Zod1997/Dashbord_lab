import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc
import numpy as np
from datetime import datetime

data = {
    "Дата": pd.date_range(start='2025-04-20', end='2025-12-31', freq='D').tolist() * 3,
    "Категория": ['Электроника'] * 256 + ['Мебель'] * 256 + ['Одежда'] * 256,
    "Продажи": np.random.randint(100, 5000, 768),
    "Регион": np.random.choice(['Север', 'Юг', 'Восток', 'Запад'], 768)
}
df = pd.DataFrame(data)
df['Дата'] = pd.to_datetime(df['Дата'])

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
app.title = "Дашборд продаж"

app.layout = dbc.Container([
    dbc.Row(dbc.Col(html.H1("Анализ продаж 2025", className="text-center my-4"))),
    dbc.Row(dbc.Col(html.P("Интерактивная визуализация продаж по категориям и регионам", className="text-center"))),

    dbc.Row([
        dbc.Col([
            html.Label("Диапазон дат:"),
            dcc.DatePickerRange(
                id='date-range',
                min_date_allowed=df['Дата'].min(),
                max_date_allowed=df['Дата'].max(),
                start_date=df['Дата'].min(),
                end_date=df['Дата'].max(),
                display_format='DD.MM.YYYY'
            )
        ], md=3),

        dbc.Col([
            html.Label("Категории товаров:"),
            dcc.Dropdown(
                id='category-select',
                options=[{'label': cat, 'value': cat} for cat in df['Категория'].unique()],
                multi=True,
                placeholder="Все категории"
            )
        ], md=3),

        dbc.Col([
            html.Label("Регион:"),
            dcc.Dropdown(
                id='region-select',
                options=[{'label': r, 'value': r} for r in df['Регион'].unique()],
                multi=True,
                placeholder="Все регионы"
            )
        ], md=3),

        dbc.Col([
            html.Label("Тип графика:"),
            dcc.RadioItems(
                id='chart-type',
                options=[
                    {'label': ' Линейный', 'value': 'line'},
                    {'label': ' Столбчатый', 'value': 'bar'},
                    {'label': ' Точечный', 'value': 'scatter'}
                ],
                value='bar',
                inline=True
            )
        ], md=3)
    ], className="mb-4"),

    dbc.Row([
        dbc.Col([
            html.Label("Диапазон продаж:"),
            dcc.RangeSlider(
                id='sales-range',
                min=df['Продажи'].min(),
                max=df['Продажи'].max(),
                step=500,
                marks={i: str(i) for i in range(0, 5001, 1000)},
                value=[df['Продажи'].min(), df['Продажи'].max()]
            )
        ])
    ]),

    dbc.Row([
        dbc.Col(dcc.Graph(id='main-chart'))
    ], className="mt-4"),

    dbc.Row([
        dbc.Col(dcc.Graph(id='pie-chart')),
        dbc.Col(dcc.Graph(id='region-chart'))
    ])
])

@app.callback(
    [Output('main-chart', 'figure'),
     Output('pie-chart', 'figure'),
     Output('region-chart', 'figure')],
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('category-select', 'value'),
     Input('region-select', 'value'),
     Input('chart-type', 'value'),
     Input('sales-range', 'value')]
)
def update_charts(start_date, end_date, categories, regions, chart_type, sales_range):
    filtered_df = df[
        (df['Дата'] >= start_date) &
        (df['Дата'] <= end_date) &
        (df['Продажи'] >= sales_range[0]) &
        (df['Продажи'] <= sales_range[1])
    ]

    if categories:
        filtered_df = filtered_df[filtered_df['Категория'].isin(categories)]
    if regions:
        filtered_df = filtered_df[filtered_df['Регион'].isin(regions)]

    if chart_type == 'line':
        main_fig = px.line(filtered_df, x='Дата', y='Продажи', color='Категория')
    elif chart_type == 'bar':
        main_fig = px.bar(filtered_df, x='Дата', y='Продажи', color='Категория')
    else:
        main_fig = px.scatter(filtered_df, x='Дата', y='Продажи', color='Категория')

    pie_fig = px.pie(filtered_df, names='Категория', values='Продажи', title='Распределение по категориям')
    region_fig = px.bar(filtered_df, x='Регион', y='Продажи', color='Категория', barmode='group')

    for fig in [main_fig, pie_fig, region_fig]:
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)')

    return main_fig, pie_fig, region_fig

if __name__ == '__main__':
    app.run(debug=True)