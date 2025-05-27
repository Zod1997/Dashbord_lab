import dash
from dash import dcc, html, Input, Output, State, ctx
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc
import numpy as np
import base64
import io

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
app.title = "Интерактивный дашборд продаж"

# Начальный layout
app.layout = dbc.Container([
    dbc.Row(dbc.Col(html.H1("Интерактивный дашборд продаж", className="text-center my-4"))),
    dbc.Row(dbc.Col(html.P("Загрузите CSV-файл с данными и исследуйте продажи по дате, категории и региону.",
                           className="text-center"))),

    dbc.Row([
        dbc.Col([
            dcc.Upload(
                id='upload-data',
                children=html.Div([
                    'Перетащите CSV-файл сюда или ',
                    html.A('выберите файл')
                ]),
                style={
                    'width': '100%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'marginBottom': '20px'
                },
                multiple=False
            )
        ])
    ]),

    html.Div(id='dashboard-controls', style={"display": "none"}, children=[
        dbc.Row([
            dbc.Col([
                html.Label("Диапазон дат:"),
                dcc.DatePickerRange(id='date-range', display_format='DD.MM.YYYY')
            ], md=3),
            dbc.Col([
                html.Label("Категории товаров:"),
                dcc.Dropdown(id='category-select', multi=True, placeholder="Все категории")
            ], md=3),
            dbc.Col([
                html.Label("Регион:"),
                dcc.Dropdown(id='region-select', multi=True, placeholder="Все регионы")
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
        ], className="mb-3"),

        dbc.Row([
            dbc.Col([
                html.Label("Диапазон продаж:"),
                dcc.RangeSlider(id='sales-range')
            ])
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(dcc.Graph(id='main-chart'))
        ]),
        dbc.Row([
            dbc.Col(dcc.Graph(id='pie-chart')),
            dbc.Col(dcc.Graph(id='region-chart'))
        ])
    ]),

    # Хранение данных из CSV
    dcc.Store(id='stored-data')
], fluid=True)


# Загрузка и обработка CSV
@app.callback(
    Output('stored-data', 'data'),
    Output('dashboard-controls', 'style'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def load_data(contents, filename):
    if contents:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        try:
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            df['Дата'] = pd.to_datetime(df['Дата'])
            return df.to_dict('records'), {"display": "block"}
        except Exception as e:
            return dash.no_update, {"display": "none"}
    return dash.no_update, {"display": "none"}


# Обновление элементов управления
@app.callback(
    Output('date-range', 'min_date_allowed'),
    Output('date-range', 'max_date_allowed'),
    Output('date-range', 'start_date'),
    Output('date-range', 'end_date'),
    Output('category-select', 'options'),
    Output('region-select', 'options'),
    Output('sales-range', 'min'),
    Output('sales-range', 'max'),
    Output('sales-range', 'value'),
    Input('stored-data', 'data')
)
def update_controls(data):
    if data:
        df = pd.DataFrame(data)
        categories = [{'label': cat, 'value': cat} for cat in df['Категория'].unique()]
        regions = [{'label': r, 'value': r} for r in df['Регион'].unique()]
        min_sales = int(df['Продажи'].min())
        max_sales = int(df['Продажи'].max())
        return df['Дата'].min(), df['Дата'].max(), df['Дата'].min(), df['Дата'].max(), categories, regions, min_sales, max_sales, [min_sales, max_sales]
    return dash.no_update


# Обновление графиков
@app.callback(
    Output('main-chart', 'figure'),
    Output('pie-chart', 'figure'),
    Output('region-chart', 'figure'),
    Input('stored-data', 'data'),
    Input('date-range', 'start_date'),
    Input('date-range', 'end_date'),
    Input('category-select', 'value'),
    Input('region-select', 'value'),
    Input('chart-type', 'value'),
    Input('sales-range', 'value')
)
def update_graphs(data, start_date, end_date, categories, regions, chart_type, sales_range):
    if data is None:
        return dash.no_update
    df = pd.DataFrame(data)

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
        main_fig = px.line(filtered_df, x='Дата', y='Продажи', color='Категория', hover_data=['Регион'])
    elif chart_type == 'bar':
        main_fig = px.bar(filtered_df, x='Дата', y='Продажи', color='Категория', hover_data=['Регион'])
    else:
        main_fig = px.scatter(filtered_df, x='Дата', y='Продажи', color='Категория', hover_data=['Регион'])

    pie_fig = px.pie(filtered_df, names='Категория', values='Продажи', title='Распределение по категориям')
    region_fig = px.bar(filtered_df, x='Регион', y='Продажи', color='Категория', barmode='group')

    for fig in [main_fig, pie_fig, region_fig]:
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(255,255,255,1)')

    return main_fig, pie_fig, region_fig


if __name__ == '__main__':
    app.run(debug=True)