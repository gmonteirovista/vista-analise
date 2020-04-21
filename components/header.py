import dash_html_components as html
import dash_core_components as dcc

def Header():
    return html.Div([
        get_logo(),
        get_header(),
        html.Br([])
    ])

def get_logo():
    logo = html.Div([

        html.Div([
            html.Img(src='http://vistacapital.com.br/wp-content/uploads/2019/10/vistacapital-logo-cor.png')
        ], className="ten columns"),


    ], className="row gs-header")
    return logo


def get_header():
    header = html.Div([

        html.Div([
            html.H3(
                'Relatório de Prévia e Análise')
        ], className="ten columns")

    ], className="banner")
    return header
