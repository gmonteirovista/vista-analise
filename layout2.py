import dash_core_components as dcc
import dash_html_components as html
import dash_table
from datetime import datetime
from datetime import date, timedelta
import pandas as pd
import numpy as np
import dash
import locale
import warnings
import dash_table.FormatTemplate as FormatTemplate
from dash_table.Format import Sign
from dash.dependencies import Input, Output, State
import plotly.express as px
import plotly.graph_objs as go
import statistics
import dash_enterprise_auth as auth
from components import Header
from app import app, server
warnings.filterwarnings("ignore")

# DATAFRAMES -----------------------------------------------------------------------------------------------------------
path = 'L:/Backoffice/Fundos/Relatorios/Nova Previa/'

file_atd = 'Data/' + datetime.today().strftime('%Y%m%d') + '.csv'
atd = pd.read_csv(path + file_atd)
atd = atd[['Ticker Bloomberg', 'volume_avg_90d', 'ValDate', 'Fund',
           'Ticker Lote', 'ProductClass', 'Book', 'FinancialPU', 'Amount',
           'Dt_Expiry', 'YesterdayPU', 'YestAmount', 'PL', 'EQUITY', 'Trade',
           'Tipo']]
atd['Prefixo'] = atd['Ticker Lote'].str[:4]

file_setores = 'Apoio/Classificacao_Equities' + '.xlsm'
setores = pd.read_excel(path + file_setores)
setores.columns = ['Prefixo', 'Ticker Lote', 'Ticker Bloomberg', 'Empresa', 'Sub_Grupo', 'Grupo']
setores1 = setores[['Prefixo', 'Sub_Grupo','Grupo']]
setores2 = setores[['Ticker Bloomberg', 'Sub_Grupo','Grupo']]

yesterday = datetime.today() - timedelta(1)
yesterday = yesterday.strftime('%d%b%Y')
file_pl = 'PL/' + 'HistoricalFundsNAVandShare-' + str(yesterday) + '-' + str(yesterday) + '.txt'
pl = pd.read_csv(path + file_pl, sep='\t')
pl.columns = ['ValDate', 'Fund', 'NAV', 'Share']

df = pd.merge(atd, setores1, on='Prefixo', how='left')
df = pd.merge(df, pl, on='Fund', how='left')
df.drop_duplicates(keep='first', inplace=True)

df = df[(df['Fund']=='BRAZIL OPPORTUNITIES FIM') |\
        (df['Fund']=='BRAZIL OPPORTUNITIES VISTA FIM') |\
        (df['Fund']=='VISTA LONG BIASED MASTER FIM') |\
        (df['Fund']=='VISTA FIA')]

df = df[['ValDate_x', 'Fund', 'Ticker Lote', 'Ticker Bloomberg', 'ProductClass',
         'Tipo','Book', 'Sub_Grupo', 'Grupo', 'Dt_Expiry', 'FinancialPU', 'YesterdayPU', 'Amount',
         'YestAmount', 'PL', 'EQUITY', 'NAV', 'Share', 'volume_avg_90d']]

df.columns = ['Date', 'Fund', 'TickerLote', 'TickerBloomberg', 'ProductClass', 'ProductType', 'Book','Subsetor',
              'Setor', 'DateExpiry', 'Price', 'YesterdayPrice', 'Amount', 'YesterdayAmount', 'PnL', 'Equity',
              'NAV', 'Share', 'VolumeAverage']

df.Date = pd.to_datetime(df.Date)

df['VarPU'] = df.apply(lambda row: (row.iloc[10]-row.iloc[11])/row.iloc[11] if row.iloc[11] != 0 else next, axis=1)
df['VarAmount'] = df.apply(lambda row: (row.iloc[12]-row.iloc[13])/row.iloc[13] if row.iloc[13] != 0 else 0, axis=1)
df['VarPnL'] = df.apply(lambda row: (row.iloc[14])/row.iloc[16] if row.iloc[16] != 0 else 0, axis=1)
df['ExposicaoDia'] = df.apply(lambda row: (row.iloc[15])/row.iloc[16] if row.iloc[16] != 0 else 0, axis=1)

df.fillna(0, inplace=True)

# Carteira Ibovespa Dataframe
file_carteira_ibov = 'Carteira Indice/' + 'Ibovespa' + datetime.today().strftime('%Y%m%d') + '.xlsx'
carteira_ibov = pd.read_excel(path + file_carteira_ibov)
carteira_ibov.columns = ['0', 'Ticker', 'Stock', 'Tipo', 'Quantidade', 'ExposicaoDia']
carteira_ibov = carteira_ibov[['Ticker', 'Quantidade', 'ExposicaoDia']]
carteira_ibov['Ticker Bloomberg'] = carteira_ibov['Ticker'] + ' BZ Equity'

carteira_ibov = carteira_ibov.merge(setores2, on='Ticker Bloomberg', how='left')
carteira_ibov.drop_duplicates(keep='first',inplace=True)
carteira_ibov = carteira_ibov[['Ticker Bloomberg', 'Ticker', 'Sub_Grupo', 'Grupo', 'Quantidade', 'ExposicaoDia']]
carteira_ibov.columns = ['Ticker Bloomberg', 'Ticker', 'Subsetor', 'Setor', 'Amount', 'ExposicaoDia']
carteira_ibov['ExposicaoDia'] = carteira_ibov['ExposicaoDia']/1000

# Type Dataframes
equity = df[df['ProductType']=='STOCK']
option = df[df['ProductType']=='OPTION']
future = df[df['ProductType']=='FUTURE']

# Inserindo contas de liquidez
equity['Liquidez'] = equity.apply(lambda row: abs(row.iloc[12]/(row.iloc[18]*0.2)) if row.iloc[18] != 0 else 0, axis=1)
option['Liquidez'] = option.apply(lambda row: abs(row.iloc[15]/(row.iloc[18]*0.2)) if row.iloc[18] != 0 else 0, axis=1)

# Caixa Dataframe
file_caixa = 'Caixa Output/' + 'CaixaOutput' + datetime.today().strftime('%Y%m%d') + '.xlsx'
caixa = pd.read_excel(path + file_caixa)
caixa.Data = pd.to_datetime(caixa.Data)

# Allocation Sector Analysis Dataframe
file_bloomberg = 'Bloomberg/DadosBloomberg' + datetime.today().strftime('%Y%m%d') + '.xlsx'
bloomberg_data = pd.read_excel(path + file_bloomberg)
bloomberg_data['ChangePrice'] = bloomberg_data.apply(lambda row: (row.iloc[1]-row.iloc[2])/row.iloc[2] if row.iloc[2] != 0 else 0, axis=1)
bloomberg_data = bloomberg_data[['ticker', 'Close', 'Open', 'Volume', 'ChangePrice']]
bloomberg_data.columns = ['Ticker Bloomberg', 'Close', 'Open', 'Volume', 'ChangePrice']
bloomberg_data = pd.merge(bloomberg_data, carteira_ibov, on='Ticker Bloomberg', how='left')
bloomberg_data.drop_duplicates(keep='first', inplace=True)
bloomberg_data['ExposicaoDia'] = bloomberg_data['ExposicaoDia']/100

bloomberg_data.fillna(0, inplace=True)
bloomberg_data['Amount'] = bloomberg_data['Amount'].apply(lambda row: str(row).replace('.', ''))
bloomberg_data['Amount'] = bloomberg_data['Amount'].apply(lambda row: float(row))

performance_sector_ibov = bloomberg_data[['Ticker', 'ChangePrice', 'Amount', 'ExposicaoDia', 'Subsetor', 'Setor',  'Open']]
performance_sector_ibov.columns = ['Ticker', 'ChangePriceIbov','AmountIbov', 'ExposicaoDiaIbov', 'Subsetor', 'Setor',  'Open']
performance_sector_ibov['ReturnIbov'] = performance_sector_ibov.apply(lambda row: (row[1]*row[2])/(row[6]*row[2]) if row.iloc[2] != 0 else 0, axis=1)
performance_sector_ibov.drop(['Open'], axis=1, inplace=True)

performance_sector_vista = df[['TickerLote', 'VarPnL', 'ExposicaoDia', 'Subsetor', 'Setor', 'Fund']]
performance_sector_vista.columns = ['Ticker', 'VarPnL', 'ExposicaoDiaVista', 'Subsetor', 'Setor', 'Fund']
performance_sector = pd.merge(performance_sector_vista, performance_sector_ibov, on='Ticker', how='inner')
performance_sector = performance_sector[['Ticker', 'VarPnL', 'ExposicaoDiaVista', 'ReturnIbov', 'ExposicaoDiaIbov', 'Subsetor_x', 'Setor_x']]
performance_sector.columns = ['Ticker', 'VarPnL', 'ExposicaoDiaVista', 'ReturnIbov', 'ExposicaoDiaIbov', 'Subsetor', 'Setor']

performance_sector_vista_pt = pd.pivot_table(performance_sector, values=['ExposicaoDiaVista', 'VarPnL'], index=['Subsetor'],
                                             margins=True, margins_name='Total', aggfunc=np.sum).sort_values(by='ExposicaoDiaVista')
performance_sector_ibov_pt = pd.pivot_table(performance_sector, values=['ExposicaoDiaIbov', 'ReturnIbov'], index=['Subsetor'],
                                            margins=True, margins_name='Total', aggfunc=np.sum).sort_values(by='ExposicaoDiaIbov')
performance_sector_ibov_pt.reset_index(inplace=True)
performance_sector_vista_pt.reset_index(inplace=True)

performance_attribution = pd.merge(performance_sector_vista_pt, performance_sector_ibov_pt, on='Subsetor', how='inner')
performance_attribution.columns = ['Subsetor', 'ExposicaoVista', 'ReturnVista', 'ExposicaoIBOV', 'ReturnIBOV']

performance_attribution['Alfa'] = performance_attribution.apply(lambda row: (row.iloc[1]-row.iloc[3]) if row.iloc[3] != 0 else 0, axis=1)
performance_attribution['PureSectorAllocation'] = performance_attribution.apply(lambda row: ((row.iloc[1]-row.iloc[3])*(row.iloc[4]-row.iloc[2])) if row.iloc[3] != 0 else 0, axis=1)
performance_attribution['WithinSectorAllocation'] = performance_attribution.apply(lambda row: ((row.iloc[3])*(row.iloc[2]-row.iloc[4])) if row.iloc[3] != 0 else 0, axis=1)
performance_attribution['InteractionEffect'] = performance_attribution.apply(lambda row: ((row.iloc[1]-row.iloc[3])*(row.iloc[2]-row.iloc[4])) if row.iloc[3] != 0 else 0, axis=1)
performance_attribution['Attribution'] = performance_attribution.apply(lambda row: (row.iloc[6]+row.iloc[7]+row.iloc[8]) if row.iloc[3] != 0 else 0, axis=1)

# Top Daily Gain, Loss and Volume Dataframe
top_gain = bloomberg_data.sort_values(by='ChangePrice', ascending=False).head(5)[['Ticker', 'ChangePrice']]
top_loss = bloomberg_data.sort_values(by='ChangePrice', ascending=True).head(5)[['Ticker', 'ChangePrice']]
top_volume = bloomberg_data.sort_values(by='Volume', ascending=False).head(5)[['Ticker', 'Volume']]
top_volume.reset_index(inplace=True)
top_volume['Volume'] = top_volume['Volume'].apply(lambda row: "{:,.2f}".format(row))
top_volume = top_volume[['Ticker', 'Volume']]

# IBOV Day Performance Dataframe
file_performance_ibov = 'Bloomberg/IBOV' + datetime.today().strftime('%Y%m%d') + '.csv'
ibov_daily_performance = pd.read_csv(path + file_performance_ibov)
ibov_daily_performance['Return'] = ibov_daily_performance.apply(lambda row: (row[1]-row[2])/row[2], axis=1)

# Dataframe pro stacked graph
equity_pt = pd.pivot_table(equity, values='ExposicaoDia', index=['TickerLote'], aggfunc=np.sum).sort_values(by='ExposicaoDia')
equity_pt['Prefixo'] = equity_pt.index.str[:4]
equity_pt['Prefixo'] = equity_pt.Prefixo.replace('BOVA', 'IBOV')

option_pt = pd.pivot_table(option, values='ExposicaoDia', index=['TickerLote'], aggfunc=np.sum).sort_values(by='ExposicaoDia')
option_pt['Prefixo'] = option_pt.index.str[:4]
option_pt['Prefixo'] = option_pt.Prefixo.replace('IBOV', 'IBOV')

equity_option = pd.merge(equity_pt, option_pt, on='Prefixo', how='outer').groupby(['Prefixo']).sum()
equity_option.columns = ['Stocks', 'Options']


# Passivo Dataframe
file_passivo = 'Passivo Output/'+ 'PassivoOutput' + datetime.today().strftime('%Y%m%d') + '.xlsx'
passivo = pd.read_excel(path + file_passivo)

# PnL by Type Dataframe
total_1 = df[df['ProductType']=='STOCK']
total_2 = df[df['ProductType']=='OPTION']
total_3 = df[df['ProductType']=='FUTURE']

a = round((total_1.PnL.sum())/list(total_1.NAV)[0], 2)
b = round((total_2.PnL.sum())/list(total_2.NAV)[0], 2)
try:
    c = round((total_3.PnL.sum())/list(total_3.NAV)[0], 2)
except:
    c = 0

total = {'Stocks': a,
        'Options': b,
        'Futures': c}

total = pd.DataFrame(total, index=[0]).transpose()
total.reset_index(inplace=True)
total.columns = ['Type', 'Total']



# LAYOUT ---------------------------------------------------------------------------------------------------------------
app.layout = html.Div([

    html.Div([
        Header(),

        html.Div([
            # Date Picker
            html.Div([
                dcc.DatePickerSingle(
                    id='date-picker',
                    min_date_allowed=df.Date.min(),
                    max_date_allowed=df.Date.max() + timedelta(1),
                    initial_visible_month=df.Date.max(),
                    date=df.Date.max()
                ),
            ], className='two columns', style={'margin-bottom': '0.5em'}),

            # Fund Dropdown
            html.Div([
                dcc.Dropdown(
                    id='fund-dropdown',
                    options=[{'label': i, 'value': i} for i in list(df['Fund'].unique())],
                    value='BRAZIL OPPORTUNITIES FIM'
                ),
            ], className='four columns', style={'margin-left': '-0.5em', 'margin-bottom': '0.5em'}),
        ], className='row'),


        html.Div([

            html.H6(
                "PERFORMANCE PREVIEW",
                className="subtitle padded", style={'margin-top': '2.5em'}
            ),

            # minicontainer 1 - PnL
            html.Div([
                html.Div([html.H3(id="well_text1", style={'textAlign': 'center'}), html.P("PnL")],
                         id="mini-container1",
                         )
            ], className="mini_container three columns", style={'margin-left': '2em'}),

            # minicontainer 2 - Patrimônio Líquido
            html.Div([
                html.Div([html.H3(id="well_text2", style={'textAlign': 'center'}), html.P("IBOV")],
                         id="mini-container2",
                         )
            ], className="mini_container three columns"),

            # minicontainer 3 - Caixa
            html.Div([
                html.Div([html.H3(id="well_text3", style={'textAlign': 'center'}), html.P("Alfa")],
                         id="mini-container3",
                         )
            ], className="mini_container three columns"),

            # Tabela - Total
            html.Div([
                html.Div(
                    dash_table.DataTable(
                        id='tabletotal',
                        data=total.to_dict('rows'),
                        columns=[{'id': 'Type', 'name': 'Type', 'type': 'text'},
                                 {'id': 'Total', 'name': 'PnL by Type', 'type': 'numeric',
                                  'format': FormatTemplate.percentage(2).sign(Sign.positive)},
                                 ],
                        editable=True,
                        style_table={'height': 'auto', 'border': 'thin grey solid'},
                        sort_action="native",
                        sort_mode="multi",
                        selected_rows=[],
                        style_header={'backgroundColor': 'rgb(174, 153, 103)', 'fontWeight': 'bold',
                                      'color': 'rgb(79, 59, 39)'},
                        style_cell={"fontFamily": "Arial", "size": 10, 'textAlign': 'center'},
                        style_data_conditional=[{'if': {'row_index': 'odd'},
                                                 'backgroundColor': 'rgb(248, 248, 248)'},
                                                {'if': {'column_id': 'Total',
                                                        'filter_query': '{Total} = 0.00'},
                                                 'color': 'rgb(227, 217, 18)'},
                                                {'if': {'column_id': 'Total',
                                                        'filter_query': '{Total} < 0.00'},
                                                 'color': 'rgb(227, 18, 18)'},
                                                {'if': {'column_id': 'Total',
                                                        'filter_query': '{Total} > 0.00'},
                                                 'color': 'rgb(48, 194, 41)'},
                                                ]

                    )
                )
            ], className="mini_container2 three columns", style={'margin-bottom': '1em'}),
        ], className='row'),


        html.Div([
            # Tabela 1 - Stocks
            html.Div([
                html.Div(
                    dash_table.DataTable(
                        id='table1',
                        data=equity.to_dict('rows'),
                        columns=[{'id': 'TickerLote', 'name': ' Product', 'type': 'text'},
                                 {'id': 'VarPU', 'name': 'Price Variation', 'type': 'numeric',
                                  'format': FormatTemplate.percentage(2).sign(Sign.positive)},
                                 {'id': 'VarPnL', 'name': 'PnL', 'type': 'numeric',
                                  'format': FormatTemplate.percentage(2).sign(Sign.positive)},
                                 {'id': 'VarAmount', 'name': 'Amount Variation', 'type': 'numeric',
                                  'format': FormatTemplate.percentage(2).sign(Sign.positive)},
                                 {'id': 'ExposicaoDia', 'name': 'Exposição', 'type': 'numeric',
                                  'format': FormatTemplate.percentage(2).sign(Sign.positive)},
                                 {'id': 'Liquidez', 'name': 'Days to Cover', 'type': 'numeric'},
                                 {'id': 'Subsetor', 'name': 'Setor Micro', 'type': 'text'}
                                 ],
                        editable=True,
                        style_table={'height': 'auto', 'border': 'thin grey solid'},
                        sort_action="native",
                        sort_mode="multi",
                        selected_rows=[],
                        style_header={'backgroundColor': 'rgb(174, 153, 103)', 'fontWeight': 'bold', 'color': 'rgb(79, 59, 39)'},
                        style_cell={"fontFamily": "Arial", "size": 10, 'textAlign': 'center'},
                        style_data_conditional=[{'if': {'row_index': 'odd'},
                                                        'backgroundColor': 'rgb(248, 248, 248)'},
                                                {'if': {'column_id': 'VarPU',
                                                        'filter_query': '{VarPU} >= 0.01 && {VarPU} < 100' },
                                                        'backgroundColor': 'rgb(104, 212, 132)'},
                                                {'if': {'column_id': 'VarPU',
                                                        'filter_query': '{VarPU} >= 0.005 && {VarPU} < 0.01'},
                                                        'backgroundColor': 'rgb(111, 212, 104)'},
                                                {'if': {'column_id': 'VarPU',
                                                        'filter_query': '{VarPU} >= 0.0025 && {VarPU} < 0.005'},
                                                        'backgroundColor': 'rgb(165, 204, 110)'},
                                                {'if': {'column_id': 'VarPU',
                                                        'filter_query': '{VarPU} >= 0 && {VarPU} < 0.0025'},
                                                        'backgroundColor': 'rgb(190, 204, 110)'},
                                                {'if': {'column_id': 'VarPU',
                                                        'filter_query': '{VarPU} >= -0.0025 && {VarPU} < 0'},
                                                 'backgroundColor': 'rgb(207, 179, 68)'},
                                                {'if': {'column_id': 'VarPU',
                                                        'filter_query': '{VarPU} >= -0.005 && {VarPU} < -0.0025'},
                                                 'backgroundColor': 'rgb(207, 160, 68)'},
                                                {'if': {'column_id': 'VarPU',
                                                        'filter_query': '{VarPU} >= -0.01 && {VarPU} < -0.005'},
                                                 'backgroundColor': 'rgb(209, 138, 79)'},
                                                {'if': {'column_id': 'VarPU',
                                                        'filter_query': '{VarPU} >= -100 && {VarPU} < -0.01'},
                                                 'backgroundColor': 'rgb(209, 105, 79)'}
                                                ]

                    )
                )
            ], className="pretty_container twelve columns", style={'margin-bottom': '1em'}),
        ]),

        html.Div([
            # Tabela 2 - Option
            html.Div([
                html.Div(
                    dash_table.DataTable(
                        id='table2',
                        data=option.to_dict('rows'),
                        columns=[{'id': 'TickerLote', 'name': ' Product', 'type': 'text'},
                                 {'id': 'VarPnL', 'name': 'PnL', 'type': 'numeric',
                                  'format': FormatTemplate.percentage(2).sign(Sign.positive)},
                                 {'id': 'ExposicaoDia', 'name': ' Exposição Δ', 'type': 'numeric',
                                  'format': FormatTemplate.percentage(2).sign(Sign.positive)},
                                 {'id': 'DateExpiry', 'name': 'Expiration Date', 'type': 'text'},
                                 {'id': 'Liquidez', 'name': 'Days to Cover', 'type': 'numeric'},
                                 ],
                        editable=True,
                        style_table={'height': 'auto', 'border': 'thin grey solid'},
                        sort_action="native",
                        sort_mode="multi",
                        selected_rows=[],
                        style_header={'backgroundColor': 'rgb(174, 153, 103)', 'fontWeight': 'bold', 'color': 'rgb(79, 59, 39)'},
                        style_cell={"fontFamily": "Arial", "size": 10, 'textAlign': 'center'},
                        style_data_conditional=[{'if': {'row_index': 'odd'},
                                                        'backgroundColor': 'rgb(248, 248, 248)'},
                                                {'if': {'column_id': 'VarPnL',
                                                        'filter_query': '{VarPnL} >= 0.01 && {VarPnL} < 100' },
                                                        'backgroundColor': 'rgb(104, 212, 132)'},
                                                {'if': {'column_id': 'VarPnL',
                                                        'filter_query': '{VarPnL} >= 0.005 && {VarPnL} < 0.01'},
                                                        'backgroundColor': 'rgb(111, 212, 104)'},
                                                {'if': {'column_id': 'VarPnL',
                                                        'filter_query': '{VarPnL} >= 0.0025 && {VarPnL} < 0.005'},
                                                        'backgroundColor': 'rgb(165, 204, 110)'},
                                                {'if': {'column_id': 'VarPnL',
                                                        'filter_query': '{VarPnL} >= 0 && {VarPnL} < 0.0025'},
                                                        'backgroundColor': 'rgb(190, 204, 110)'},
                                                {'if': {'column_id': 'VarPnL',
                                                        'filter_query': '{VarPnL} >= -0.0025 && {VarPnL} < 0'},
                                                 'backgroundColor': 'rgb(207, 179, 68)'},
                                                {'if': {'column_id': 'VarPnL',
                                                        'filter_query': '{VarPnL} >= -0.005 && {VarPnL} < -0.0025'},
                                                 'backgroundColor': 'rgb(207, 160, 68)'},
                                                {'if': {'column_id': 'VarPnL',
                                                        'filter_query': '{VarPnL} >= -0.01 && {VarPnL} < -0.005'},
                                                 'backgroundColor': 'rgb(209, 138, 79)'},
                                                {'if': {'column_id': 'VarPnL',
                                                        'filter_query': '{VarPnL} >= -100 && {VarPnL} < -0.01'},
                                                 'backgroundColor': 'rgb(209, 105, 79)'}
                                                ]
                    )
                )
            ], className="pretty_container eight columns", style={'margin-bottom': '1.75em', 'margin-right': '1.55em'}),

            # Tabela 3 - Future
            html.Div([
                html.Div(
                    dash_table.DataTable(
                        id='table3',
                        data=future.to_dict('rows'),
                        columns=[{'id': 'TickerLote', 'name': ' Product', 'type': 'text'},
                                 {'id': 'VarPnL', 'name': 'PnL', 'type': 'numeric',
                                  'format': FormatTemplate.percentage(3).sign(Sign.positive)},
                                 {'id': 'DateExpiry', 'name': 'Expiration Date', 'type': 'text'}
                                 ],
                        editable=True,
                        style_table={'height': 'auto', 'border': 'thin grey solid'},
                        sort_action="native",
                        sort_mode="multi",
                        selected_rows=[],
                        style_header={'backgroundColor': 'rgb(174, 153, 103)', 'fontWeight': 'bold', 'color': 'rgb(79, 59, 39)'},
                        style_cell={"fontFamily": "Arial", "size": 10, 'textAlign': 'center'},
                        style_data_conditional=[{'if': {'row_index': 'odd'},
                                                        'backgroundColor': 'rgb(248, 248, 248)'},
                                                {'if': {'column_id': 'VarPnL',
                                                        'filter_query': '{VarPnL} >= 0.01 && {VarPnL} < 100' },
                                                        'backgroundColor': 'rgb(104, 212, 132)'},
                                                {'if': {'column_id': 'VarPnL',
                                                        'filter_query': '{VarPnL} >= 0.005 && {VarPnL} < 0.01'},
                                                        'backgroundColor': 'rgb(111, 212, 104)'},
                                                {'if': {'column_id': 'VarPnL',
                                                        'filter_query': '{VarPnL} >= 0.0025 && {VarPnL} < 0.005'},
                                                        'backgroundColor': 'rgb(165, 204, 110)'},
                                                {'if': {'column_id': 'VarPnL',
                                                        'filter_query': '{VarPnL} >= 0 && {VarPnL} < 0.0025'},
                                                        'backgroundColor': 'rgb(190, 204, 110)'},
                                                {'if': {'column_id': 'VarPnL',
                                                        'filter_query': '{VarPnL} >= -0.0025 && {VarPnL} < 0'},
                                                 'backgroundColor': 'rgb(207, 179, 68)'},
                                                {'if': {'column_id': 'VarPnL',
                                                        'filter_query': '{VarPnL} >= -0.005 && {VarPnL} < -0.0025'},
                                                 'backgroundColor': 'rgb(207, 160, 68)'},
                                                {'if': {'column_id': 'VarPnL',
                                                        'filter_query': '{VarPnL} >= -0.01 && {VarPnL} < -0.005'},
                                                 'backgroundColor': 'rgb(209, 138, 79)'},
                                                {'if': {'column_id': 'VarPnL',
                                                        'filter_query': '{VarPnL} >= -100 && {VarPnL} < -0.01'},
                                                 'backgroundColor': 'rgb(209, 105, 79)'}
                                                ]
                    )
                )
            ], className="pretty_container four columns"),
        ], className='row flex-display', style={'margin-bottom': '10.75em'}),


        html.Div([

            html.H6(
                "Page 2",
                className="espacopagina espaco", style={'margin-top': '10em'}
            ),
            html.H6(
                    "IBOVESPA - TOP DAILY GAINS, LOSSES AND VOLUME",
                    className="subtitle padded"
                    ),

            # Tabela - Top Gain
            html.Div([
                html.Div(
                    dash_table.DataTable(
                        id='table_top_gain',
                        data=top_gain.to_dict('rows'),
                        columns=[{'id': 'Ticker', 'name': ' Ticker', 'type': 'text'},
                                 {'id': 'ChangePrice', 'name': 'Price Variation', 'type': 'numeric',
                                  'format': FormatTemplate.percentage(2).sign(Sign.positive)},
                                 ],
                        style_header={'backgroundColor': 'rgb(174, 153, 103)', 'fontWeight': 'bold',
                                      'color': 'rgb(79, 59, 39)'},
                        style_cell={"fontFamily": "Arial", "size": 10, 'textAlign': 'center'},
                        style_data_conditional=[{'if': {'row_index': 'odd'},
                                                 'backgroundColor': 'rgb(248, 248, 248)'},
                                                {'if': {'column_id': 'ChangePrice',
                                                        'filter_query': '{ChangePrice} < 0.00'},
                                                 'color': 'rgb(227, 18, 18)'},
                                                {'if': {'column_id': 'ChangePrice',
                                                        'filter_query': '{ChangePrice} > 0.00'},
                                                 'color': 'rgb(48, 194, 41)'},
                                                ]
                    )
                )
            ], className="pretty_container four columns", style={'margin-bottom': '1.75em'}),

            # Tabela - Top Loss
            html.Div([
                html.Div(
                    dash_table.DataTable(
                        id='table_top_loss',
                        data=top_loss.to_dict('rows'),
                        columns=[{'id': 'Ticker', 'name': 'Ticker', 'type': 'text'},
                                 {'id': 'ChangePrice', 'name': 'Price Variation', 'type': 'numeric',
                                  'format': FormatTemplate.percentage(2).sign(Sign.positive)},
                                 ],
                        style_header={'backgroundColor': 'rgb(174, 153, 103)', 'fontWeight': 'bold',
                                      'color': 'rgb(79, 59, 39)'},
                        style_cell={"fontFamily": "Arial", "size": 10, 'textAlign': 'center'},
                        style_data_conditional=[{'if': {'row_index': 'odd'},
                                                 'backgroundColor': 'rgb(248, 248, 248)'},
                                                {'if': {'column_id': 'ChangePrice',
                                                        'filter_query': '{ChangePrice} < 0.00'},
                                                 'color': 'rgb(227, 18, 18)'},
                                                {'if': {'column_id': 'ChangePrice',
                                                        'filter_query': '{ChangePrice} > 0.00'},
                                                 'color': 'rgb(48, 194, 41)'},
                                                ]
                    )
                )
            ], className="pretty_container four columns", style={'margin-bottom': '1.75em'}),

            # Tabela - Top Volume
            html.Div([
                html.Div(
                    dash_table.DataTable(
                        id='table_top_volume',
                        data=top_volume.to_dict('rows'),
                        columns=[{'id': 'Ticker', 'name': ' Ticker', 'type': 'text'},
                                 {'id': 'Volume', 'name': 'Volume', 'type': 'numeric'},
                                 ],
                        style_header={'backgroundColor': 'rgb(174, 153, 103)', 'fontWeight': 'bold',
                                      'color': 'rgb(79, 59, 39)'},
                        style_cell={"fontFamily": "Arial", "size": 10, 'textAlign': 'center'},
                        style_data_conditional=[{'if': {'row_index': 'odd'},
                                                 'backgroundColor': 'rgb(248, 248, 248)'},
                                                ]
                    )
                )
            ], className="pretty_container four columns", style={'margin-bottom': '1.75em'}),

        ], className='row flex-display'),


        html.Div([
            html.H6(
                "SECTOR ALLOCATION ANALYSIS",
                className="subtitle padded", style={'margin-top': '2em'}
            ),
            # Gráfico 1
            html.Div([
                html.Div([
                    html.Div(
                        dcc.Graph(
                            id='graph1',
                            figure={'data': [go.Bar(x=df['Subsetor'],
                                                    y=df['ExposicaoDia'])],
                                    'layout': {'title': 'EXPOSIÇÃO POR SUBSETOR',
                                               'plot_bgcolor': 'rgba(0, 0, 0, 0)',
                                               'paper_bgcolor': 'rgba(0, 0, 0, 0)'},
                                    }
                        )
                    )
                ], className='pretty_container twelve columns'),
            ], className='row'),
        ]),


        # Gráfico 2
        html.Div([
            html.Div([
                html.Div(
                    dcc.Graph(
                        id='graph2',
                        figure={'data': [go.Bar(x=df['Setor'],
                                                y=df['ExposicaoDia'])],
                                'layout': {'title': 'EXPOSIÇÃO POR SETOR',
                                           'plot_bgcolor': 'rgba(0, 0, 0, 0)',
                                           'paper_bgcolor': 'rgba(0, 0, 0, 0)'},
                                }
                    )
                )
            ], className='pretty_container twelve columns', style={'margin-bottom': '10.75em'}),
        ], className='row'),


        html.Div([
            html.H6(
                "Page 3",
                className="espacopagina espaco", style={'margin-top': '10em'}
            ),
            # Tabela 4 - Performance Sector Attribution
            html.Div([
                html.Div(
                    dash_table.DataTable(
                        id='table4',
                        data=performance_attribution.to_dict('rows'),
                        columns=[{'id': 'Subsetor', 'name': 'Subsetor', 'type': 'text'},
                                 {'id': 'ExposicaoVista', 'name': 'Exp Vista', 'type': 'numeric',
                                  'format': FormatTemplate.percentage(2).sign(Sign.positive)},
                                 {'id': 'ExposicaoIBOV', 'name': 'Exp. Bench', 'type': 'numeric',
                                  'format': FormatTemplate.percentage(2).sign(Sign.positive)},
                                 {'id': 'Alfa', 'name': 'Alfa', 'type': 'numeric',
                                  'format': FormatTemplate.percentage(2).sign(Sign.positive)},
                                 {'id': 'ReturnVista', 'name': 'Return Vista', 'type': 'numeric',
                                  'format': FormatTemplate.percentage(2).sign(Sign.positive)},
                                 {'id': 'ReturnIBOV', 'name': 'Return Bench', 'type': 'numeric',
                                  'format': FormatTemplate.percentage(2).sign(Sign.positive)},
                                 {'id': 'PureSectorAllocation', 'name': 'Pure Sector', 'type': 'numeric',
                                  'format': FormatTemplate.percentage(3).sign(Sign.positive)},
                                 {'id': 'WithinSectorAllocation', 'name': 'Within Sector', 'type': 'numeric',
                                  'format': FormatTemplate.percentage(3).sign(Sign.positive)},
                                 {'id': 'InteractionEffect', 'name': 'Interaction', 'type': 'numeric',
                                  'format': FormatTemplate.percentage(3).sign(Sign.positive)},
                                 {'id': 'Attribution', 'name': 'Attribution', 'type': 'numeric',
                                  'format': FormatTemplate.percentage(3).sign(Sign.positive)},
                                 ],
                        editable=True,
                        style_table={'height': 'auto', 'border': 'thin grey solid'},
                        sort_action="native",
                        sort_mode="multi",
                        selected_rows=[],
                        style_header={'backgroundColor': 'rgb(174, 153, 103)', 'fontWeight': 'bold',
                                      'color': 'rgb(79, 59, 39)'},
                        style_cell={"fontFamily": "Arial", "size": 10, 'textAlign': 'center'},
                        style_data_conditional=[{'if': {'column_id': 'ExposicaoVista', },
                                                 'backgroundColor': 'rgb(248, 248, 248)'},
                                                {'if': {'column_id': 'ExposicaoIBOV'},
                                                 'backgroundColor': 'rgb(248, 248, 248)'},
                                                {'if': {'column_id': 'PureSectorAllocation'},
                                                 'backgroundColor': 'rgb(248, 248, 248)'},
                                                {'if': {'column_id': 'WithinSectorAllocation'},
                                                 'backgroundColor': 'rgb(248, 248, 248)'},
                                                {'if': {'column_id': 'InteractionEffect'},
                                                 'backgroundColor': 'rgb(248, 248, 248)'},
                                                {'if': {'column_id': 'Attribution'},
                                                 'backgroundColor': 'rgb(248, 248, 248)'},

                                                {'if': {'column_id': 'Alfa',
                                                        'filter_query': '{Alfa} >= 0.02'},
                                                        'backgroundColor': 'rgb(130, 237, 100)'},
                                                {'if': {'column_id': 'Alfa',
                                                        'filter_query': '{Alfa} >= -0.02 && {Alfa} < 0.02'},
                                                        'backgroundColor': 'rgb(237, 235, 100)'},
                                                {'if': {'column_id': 'Alfa',
                                                        'filter_query': '{Alfa} <= -0.02'},
                                                        'backgroundColor': 'rgb(237, 100, 100)'},

                                                {'if': {'column_id': 'ReturnVista',
                                                        'filter_query': '{ReturnVista} < 0.00'},
                                                        'color': 'rgb(227, 18, 18)'},
                                                {'if': {'column_id': 'ReturnVista',
                                                        'filter_query': '{ReturnVista} > 0.00'},
                                                        'color': 'rgb(48, 194, 41)'},
                                                {'if': {'column_id': 'ReturnIBOV',
                                                        'filter_query': '{ReturnIBOV} < 0.00'},
                                                        'color': 'rgb(227, 18, 18)'},
                                                {'if': {'column_id': 'ReturnIBOV',
                                                        'filter_query': '{ReturnIBOV} > 0.00'},
                                                        'color': 'rgb(48, 194, 41)'},

                                                ]
                    )
                )
            ], className="pretty_container twelve columns", style={'margin-bottom': '1em'}),
        ], className='row flex-display'),


        # Gráfico 3
        html.Div([
            html.Div([
                html.Div(
                    dcc.Graph(
                        id='graph3',
                        figure={'data': [go.Bar(x=equity_option.index,
                                                y=equity_option['Stocks'],
                                                name='À Vista',
                                                marker={'color': 'rgb(174, 153, 103)'},
                                                text=list(round(equity_option['Stocks'], 2)),
                                                textposition="outside"
                                                ),
                                         go.Bar(x=equity_option.index,
                                                 y=equity_option['Options'],
                                                 name='Opções',
                                                 marker={'color': 'rgb(64, 140, 168)'},
                                                 text=list(round(equity_option['Options'], 2)),
                                                 textposition="outside"
                                                 )
                                         ],
                                'layout': {'title': '<b>EXPOSIÇÃO POR TICKER</b>',
                                           'barmode': 'stack-relative',
                                           'xaxis': {'showgrid': False},
                                           'yaxis': {'showgrid': False},
                                           'plot_bgcolor': 'rgba(0, 0, 0, 0)',
                                           'paper_bgcolor': 'rgba(0, 0, 0, 0)',
                                           'margin': {"r": 0, "t": 20, "b": 0, "l": 2},
                                           }
                                }
                    )
                )
            ], className='pretty_container twelve columns'),
        ], className='row'),



        html.Div([
            html.H6(
                "CASH AND FINANCIAL TRANSACTIONS",
                className="subtitle padded", style={'margin-top': '1.75em'}
            ),
            # Tabela 5 - Caixa
            html.Div([
                html.Div(
                    dash_table.DataTable(
                        id='table-caixa',
                        data=caixa.to_dict('rows'),
                        columns=[{'id': 'Data', 'name': ' Data', 'type': 'text'},
                                 {'id': 'Caixa', 'name': 'Caixa', 'type': 'numeric',
                                  'format': FormatTemplate.money(3).sign(Sign.positive)},
                                 {'id': 'Caixa + LFT', 'name': 'Caixa + LFT', 'type': 'numeric',
                                  'format': FormatTemplate.money(3).sign(Sign.positive)}
                                 ],
                        editable=True,
                        style_table={'height': 'auto', 'border': 'thin grey solid'},
                        sort_action="native",
                        sort_mode="multi",
                        selected_rows=[],
                        style_header={'backgroundColor': 'rgb(174, 153, 103)', 'fontWeight': 'bold',
                                      'color': 'rgb(79, 59, 39)'},
                        style_cell={"fontFamily": "Arial", "size": 10, 'textAlign': 'center'},
                        style_data_conditional=[{'if': {'row_index': 'odd'},
                                                 'backgroundColor': 'rgb(248, 248, 248)'}
                                                ]
                    )
                )
            ], className="pretty_container eight columns", style={'margin-bottom': '1em'}),
        ], className='row flex-display'),

        html.Div([
            # Tabela 6 - Passivo
            html.Div([
                html.Div(
                    dash_table.DataTable(
                        id='table-passivo',
                        data=passivo.to_dict('rows'),
                        columns=[{'id': 'Data', 'name': ' Data', 'type': 'text'},
                                 {'id': 'Cotizacao', 'name': 'Cotização', 'type': 'numeric',
                                  'format': FormatTemplate.money(2).sign(Sign.positive)},
                                 {'id': 'Liquidacao', 'name': 'Liquidação', 'type': 'numeric',
                                  'format': FormatTemplate.money(2).sign(Sign.positive)}
                                 ],
                        editable=True,
                        style_table={'height': 'auto', 'border': 'thin grey solid'},
                        sort_action="native",
                        sort_mode="multi",
                        selected_rows=[],
                        style_header={'backgroundColor': 'rgb(174, 153, 103)', 'fontWeight': 'bold',
                                      'color': 'rgb(79, 59, 39)'},
                        style_cell={"fontFamily": "Arial", "size": 10, 'textAlign': 'center'},
                        style_data_conditional=[{'if': {'row_index': 'odd'},
                                                 'backgroundColor': 'rgb(248, 248, 248)'}
                                                ]
                    )
                )
            ], className="pretty_container eight columns", style={'margin-bottom': '1em', 'margin-left': '0.8em'}),
        ], className='row flex-display'),


    ], className="subpage"),
], className="page")


# CALLBACK -------------------------------------------------------------------------------------------------------------
# Minicontainer 1 - Children
@app.callback(Output('well_text1', 'children'),
              [Input('date-picker', 'date'),
               Input('fund-dropdown', 'value')])
def update_data(date, value):
    data_1 = df[df['Fund']==value]
    data_1 = data_1[(data_1['Date'] == date)]
    valor = ((data_1.PnL.sum())/list(data_1.NAV)[0])*100
    valor = "{:,.2f} % ".format(valor)
    return valor


# Minicontainer 2
@app.callback(Output('well_text2', 'children'),
              [Input('date-picker', 'date'),
               Input('fund-dropdown', 'value')])
def update_data(date, value):
    valor = (ibov_daily_performance.Return[0])*100
    valor = "{:,.2f} %".format(valor)
    return valor


# Minicontainer 3
@app.callback(Output('well_text3', 'children'),
              [Input('date-picker', 'date'),
               Input('fund-dropdown', 'value')])
def update_data(date, value):
    data_1 = df[df['Fund']==value]
    data_1 = data_1[(data_1['Date'] == date)]
    valor = ((data_1.PnL.sum())/list(data_1.NAV)[0])
    valor = (valor - ibov_daily_performance.Return[0])*100
    valor = "{:,.2f} %".format(valor)
    return valor


# Total PnL by ProductType
@app.callback(Output('tabletotal', 'data'),
              [Input('date-picker', 'date'),
               Input('fund-dropdown', 'value')])
def update_data(date, value):
    total_1 = df[(df['Fund'] == value) & (df['Date'] == date) & (df['ProductType'] == 'STOCK')]
    total_2 = df[(df['Fund'] == value) & (df['Date'] == date) & (df['ProductType'] == 'OPTION')]
    total_3 = df[(df['Fund'] == value) & (df['Date'] == date) & (df['ProductType'] == 'FUTURE')]

    a = round((total_1.PnL.sum()) / list(total_1.NAV)[0], 4)
    b = round((total_2.PnL.sum()) / list(total_2.NAV)[0], 4)
    try:
        c = round((total_3.PnL.sum()) / list(total_3.NAV)[0], 4)
    except:
        c = 0

    total = {'Stocks': a,
             'Options': b,
             'Futures': c}

    total = pd.DataFrame(total, index=[0]).transpose()
    total.reset_index(inplace=True)
    total.columns = ['Type', 'Total']
    total = total.to_dict('rows')

    return total


# Tabela 1 - Stocks
@app.callback(Output('table1', 'data'),
              [Input('date-picker', 'date'),
               Input('fund-dropdown', 'value')])
def update_data(date, value):
    equity['Liquidez'] = round(equity['Liquidez'], 2)
    data_1 = equity[equity['Fund']==value]
    data_1 = data_1[(data_1['Date'] == date)]
    data_1 = data_1.to_dict('rows')
    return data_1


# Tabela 2 - Option
@app.callback(Output('table2', 'data'),
              [Input('date-picker', 'date'),
               Input('fund-dropdown', 'value')])
def update_data(date, value):
    option['Liquidez'] = round(option['Liquidez'], 2)
    data_1 = option[option['Fund']==value]
    data_1 = data_1[(data_1['Date'] == date)]
    data_1 = data_1.to_dict('rows')
    return data_1


# Tabela 3 - Future
@app.callback(Output('table3', 'data'),
              [Input('date-picker', 'date'),
               Input('fund-dropdown', 'value')])
def update_data(date, value):
    data_1 = future[future['Fund']==value]
    data_1 = data_1[(data_1['Date'] == date)]
    data_1 = data_1.to_dict('rows')
    return data_1


# Gráfico 1
@app.callback(Output('graph1', 'figure'),
              [Input('date-picker', 'date'),
               Input('fund-dropdown', 'value')])
def update_data(date, value):

    data_2 = df[df['Fund']==value]
    data_2 = data_2[(data_2['Date'] == date)]
    data_2 = pd.pivot_table(data_2, values='ExposicaoDia', index=['Subsetor'], aggfunc=np.sum).sort_values(by='ExposicaoDia')
    data_2['ExposicaoDia'] = data_2['ExposicaoDia']*100

    ibov_2 = pd.pivot_table(carteira_ibov, values='ExposicaoDia', index=['Subsetor'], aggfunc=np.sum)

    data_2 = data_2.merge(ibov_2, on='Subsetor', how='left')
    data_2.columns = ['ExposicaoDia_vista', 'ExposicaoDia_ibov']
    data_2.fillna(0, inplace=True)

    figure = {'data': [go.Bar(x=data_2.index,
                              y=data_2['ExposicaoDia_vista'],
                              name='Vista Capital',
                              marker={'color': 'rgb(174, 153, 103)'},
                              text=list(round(data_2['ExposicaoDia_vista'], 2)),
                              textposition="outside",
                              ),
                       go.Bar(x=data_2.index,
                              y=data_2['ExposicaoDia_ibov'],
                              name='Ibovespa',
                              marker={'color': 'rgb(64, 140, 168)'},
                              text=list(round(data_2['ExposicaoDia_ibov'], 2)),
                              textposition="outside"
                             )
                       ],
              'layout': {'title': '<b>EXPOSIÇÃO POR SUBSETOR</b>',
                         'xaxis': {'showgrid': False},
                         'yaxis': {'showgrid': False},
                         'plot_bgcolor': 'rgba(0, 0, 0, 0)',
                         'paper_bgcolor': 'rgba(0, 0, 0, 0)',
                         }
              }
    return figure


# Gráfico 2
@app.callback(Output('graph2', 'figure'),
              [Input('date-picker', 'date'),
               Input('fund-dropdown', 'value')])
def update_data(date, value):

    data_2 = df[df['Fund']==value]
    data_2 = data_2[(data_2['Date'] == date)]
    data_2 = pd.pivot_table(data_2, values='ExposicaoDia', index=['Setor'], aggfunc=np.sum).sort_values(by='ExposicaoDia')
    data_2['ExposicaoDia'] = data_2['ExposicaoDia']*100

    ibov_2 = pd.pivot_table(carteira_ibov, values='ExposicaoDia', index=['Setor'], aggfunc=np.sum)
    ibov_2.index.names = ['Setor']

    data_2 = data_2.merge(ibov_2, on='Setor', how='left')
    data_2.columns = ['ExposicaoDia_vista', 'ExposicaoDia_ibov']
    data_2.fillna(0, inplace=True)

    figure = {'data': [go.Bar(x=data_2.index,
                              y=data_2['ExposicaoDia_vista'],
                              name='Vista Capital',
                              marker={'color': 'rgb(174, 153, 103)'},
                              text=list(round(data_2['ExposicaoDia_vista'], 2)),
                              textposition="outside"
                              ),
                       go.Bar(x=data_2.index,
                               y=data_2['ExposicaoDia_ibov'],
                               name='Ibovespa',
                               marker={'color': 'rgb(64, 140, 168)'},
                               text=list(round(data_2['ExposicaoDia_ibov'], 2)),
                               textposition="outside"
                               )
                       ],
              'layout': {'title': '<b>EXPOSIÇÃO POR SETOR</b>',
                         'xaxis': {'showgrid': False},
                         'yaxis': {'showgrid': False},
                         'plot_bgcolor': 'rgba(0, 0, 0, 0)',
                         'paper_bgcolor': 'rgba(0, 0, 0, 0)',
                         }
              }
    return figure


# Gráfico 3
@app.callback(Output('graph3', 'figure'),
              [Input('date-picker', 'date'),
               Input('fund-dropdown', 'value')])
def update_data(date, value):

    equity = df[(df['Fund']==value) & (df['ProductType'] == 'STOCK')]
    option = df[(df['Fund']==value) & (df['ProductType'] == 'OPTION')]

    equity = equity[equity['Date']==date]
    option = option[option['Date']==date]

    equity_pt = pd.pivot_table(equity, values='ExposicaoDia', index=['TickerLote'], aggfunc=np.sum).sort_values(by='ExposicaoDia')
    equity_pt['Prefixo'] = equity_pt.index.str[:4]
    equity_pt['Prefixo'] = equity_pt.Prefixo.replace('BOVA', 'IBOV')
    option_pt = pd.pivot_table(option, values='ExposicaoDia', index=['TickerLote'], aggfunc=np.sum).sort_values(by='ExposicaoDia')
    option_pt['Prefixo'] = option_pt.index.str[:4]
    option_pt['Prefixo'] = option_pt.Prefixo.replace('IBOV', 'IBOV')
    equity_option = pd.merge(equity_pt, option_pt, on='Prefixo', how='outer').groupby(['Prefixo']).sum()
    equity_option.columns = ['Stocks', 'Options']

    equity_option['Stocks'] = equity_option['Stocks'] * 100
    equity_option['Options'] = equity_option['Options'] * 100

    figure = {'data': [go.Bar(x=equity_option.index,
                              y=equity_option['Stocks'],
                              name='À Vista',
                              marker={'color': 'rgb(174, 153, 103)'},
                              text=list(round(equity_option['Stocks'], 2)),
                              textposition="outside",
                              ),
                       go.Bar(x=equity_option.index,
                               y=equity_option['Options'],
                               name='Opções',
                               marker={'color': 'rgb(64, 140, 168)'},
                               text=list(round(equity_option['Options'], 2)),
                               textposition="outside"
                              )
                       ],
              'layout': {'title': '<b>EXPOSIÇÃO POR TICKER</b>',
                         'xaxis': {'showgrid': False},
                         'yaxis': {'showgrid': False},
                         'plot_bgcolor': 'rgba(0, 0, 0, 0)',
                         'paper_bgcolor': 'rgba(0, 0, 0, 0)',
                         'margin': {"r": 0, "t": 30, "b": 25, "l": 40}
                         }
              }
    return figure


# Tabela 4 - Performance Sector Attribution
@app.callback(Output('table4', 'data'),
              [Input('fund-dropdown', 'value')])
def update_data(value):
    performance_sector_vista = df[['TickerLote', 'VarPnL', 'ExposicaoDia', 'Subsetor', 'Setor', 'Fund']]
    performance_sector_vista.columns = ['Ticker', 'VarPnL', 'ExposicaoDiaVista', 'Subsetor', 'Setor', 'Fund']
    performance_sector_vista = performance_sector_vista[performance_sector_vista['Fund']==value]
    performance_sector = pd.merge(performance_sector_vista, performance_sector_ibov, on='Ticker', how='inner')

    performance_sector = performance_sector[['Ticker', 'VarPnL', 'ExposicaoDiaVista', 'ReturnIbov', 'ExposicaoDiaIbov', 'Subsetor_x', 'Setor_x']]
    performance_sector.columns = ['Ticker', 'VarPnL', 'ExposicaoDiaVista', 'ReturnIbov', 'ExposicaoDiaIbov', 'Subsetor','Setor']

    performance_sector_vista_pt = pd.pivot_table(performance_sector, values=['ExposicaoDiaVista', 'VarPnL'],
                                                                     index=['Subsetor'],
                                                                     margins=True,
                                                                     margins_name='Total',
                                                                     aggfunc=np.sum).sort_values(by='ExposicaoDiaVista')

    performance_sector_ibov_pt = pd.pivot_table(performance_sector, values=['ExposicaoDiaIbov', 'ReturnIbov'],
                                                                    index=['Subsetor'],
                                                                    margins=True,
                                                                    margins_name='Total',
                                                                    aggfunc=np.sum).sort_values(by='ExposicaoDiaIbov')
    performance_sector_ibov_pt.reset_index(inplace=True)
    performance_sector_vista_pt.reset_index(inplace=True)

    performance_attribution = pd.merge(performance_sector_vista_pt, performance_sector_ibov_pt, on='Subsetor', how='inner')
    performance_attribution.columns = ['Subsetor', 'ExposicaoVista', 'ReturnVista', 'ExposicaoIBOV', 'ReturnIBOV']

    performance_attribution['Alfa'] = performance_attribution.apply(lambda row: (row.iloc[1] - row.iloc[3]) if row.iloc[3] != 0 else 0, axis=1)
    performance_attribution['PureSectorAllocation'] = performance_attribution.apply(lambda row: ((row.iloc[1] - row.iloc[3]) * ((row.iloc[4] - row.iloc[2]))) if row.iloc[3] != 0 else 0, axis=1)
    performance_attribution['WithinSectorAllocation'] = performance_attribution.apply(lambda row: ((row.iloc[3]) * ((row.iloc[2] - row.iloc[4]))) if row.iloc[3] != 0 else 0, axis=1)
    performance_attribution['InteractionEffect'] = performance_attribution.apply(lambda row: ((row.iloc[1] - row.iloc[3]) * ((row.iloc[2] - row.iloc[4]))) if row.iloc[3] != 0 else 0, axis=1)
    performance_attribution['Attribution'] = performance_attribution.apply(lambda row: (row.iloc[6] + row.iloc[7] + row.iloc[8]) if row.iloc[3] != 0 else 0, axis=1)
    data_1 = performance_attribution.to_dict('rows')
    return data_1


# Tabela 5 - Caixa
@app.callback(Output('table-caixa', 'data'),
              [Input('fund-dropdown', 'value')])
def update_data(value):
    data_1 = caixa[caixa['Fundo'] == value]
    data_1 = data_1.to_dict('rows')
    return data_1

# Tabela 6 - Passivo
@app.callback(Output('table-passivo', 'data'),
              [Input('fund-dropdown', 'value')])
def update_data(value):
    data_1 = passivo[passivo['Fundo'] == value]
    data_1 = data_1.to_dict('rows')
    return data_1


# RUN SERVER -----------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(port=8090)
