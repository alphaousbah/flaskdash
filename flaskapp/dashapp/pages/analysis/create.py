from flaskapp.dashapp.pages.utils import *

dash.register_page(__name__)
page_id = get_page_id(__name__)


def layout():
    return html.Div([
        dcc.Location(id=page_id + 'location'),
        dcc.Store(id=page_id + 'store'),
        html.H5('Create Analysis', className='title'),
        html.Div([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader('Analysis Settings'),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label('AGIR Quote', html_for=page_id + 'input-quote', width=2),
                                    dbc.Input(
                                        id=page_id + 'input-quote',
                                        placeholder='Enter a value',
                                        type='number',
                                    ),
                                ]),
                            ], className='mb-2'),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label('Analysis Name', html_for=page_id + 'input-name', width=2),
                                    dbc.Input(id=page_id + 'input-name', placeholder='Enter a value'),
                                ]),
                            ], className='mb-2'),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label('Client', html_for=page_id + 'input-client', width=2),
                                    dbc.Input(id=page_id + 'input-client', placeholder='Enter a value'),
                                ]),
                            ], className='mb-2'),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Button('Create', id=page_id + 'btn-create', n_clicks=0, className='button'),
                                ]),
                            ]),
                            dbc.Row([
                                html.Div(id=page_id + 'div-inform'),
                            ]),
                        ]),
                    ], className='card'),
                ], width=10),
            ]),
        ], className='div-standard'),
    ])


@callback(
    Output(page_id + 'store', 'data'),
    Output(page_id + 'div-inform', 'children'),
    Input(page_id + 'btn-create', 'n_clicks'),
    State(page_id + 'input-quote', 'value'),
    State(page_id + 'input-name', 'value'),
    State(page_id + 'input-client', 'value'),
    config_prevent_initial_callbacks=True
)
def create_analysis(n_clicks, quote, name, client):
    """
    Error handling:
    For SQLAlchemy: https://docs.sqlalchemy.org/en/14/orm/session_basics.html#framing-out-a-begin-commit-rollback-block
    In general: https://jellis18.github.io/post/2021-12-13-python-exceptions-rust-go/

    def divide(x, y):
        if y == 0:
            raise ZeroDivisionError('Cannot divide by zero')
        return x / y

    try:
        print(divide(5, 0))
    except ZeroDivisionError as e:
        print(e)

    """
    try:
        analysis = Analysis(quote=quote, name=name, client=client)
        session.add(analysis)
    except ValueError as e:
        session.rollback()
        alert = dbc.Alert(
            str(e),
            color='danger',
            duration=4000,
        )
        return no_update, alert
    else:
        session.commit()
        data = {'analysis_id': analysis.id}
        alert = dbc.Alert(
            'The analysis has been created. You will be redirected to the analysis workspace in an instant.',
            id=page_id + 'alert-success',
            color='success',
        )
        return data, alert

@callback(
    Output(page_id + 'location', 'pathname'),
    Input(page_id + 'alert-success', 'is_open'),
    State(page_id + 'store', 'data'),
)
def goto_analysis_workspace(is_open, data):
    # Redirect when the is_open property of the 'alert-success' component is triggered
    # Sleep for 3 seconds so that the user can see the success alert message
    time.sleep(3)

    return f'/dashapp/analysis/view/{data["analysis_id"]}'
