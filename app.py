import dash
import dash_auth


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets, url_base_pathname='/vista-analise/')
server = app.server
app.config.suppress_callback_exceptions = True



VALID_USERNAME_PASSWORD_PAIRS = [
     ['vista_analise', 'Vist@2020']
 ]

auth = dash_auth.BasicAuth(
     app,
     VALID_USERNAME_PASSWORD_PAIRS
)