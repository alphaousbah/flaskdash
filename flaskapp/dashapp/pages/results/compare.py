import dash
from dash import html, dcc, dash_table, callback, Output, Input, State, ALL
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from flaskapp.dashapp.pages.utils import *
from flaskapp.extensions import db
from flaskapp.models import *
import pandas as pd

directory = get_directory(__name__)['directory']
page = get_directory(__name__)['page']
dash.register_page(__name__, path_template=f'/{directory}/{page}/<analysis_id>', order=3)
page_id = get_page_id(__name__)


def layout(analysis_id):
    analysis = db.session.get(Analysis, analysis_id)

    return html.Div([
        dcc.Store(id=page_id + 'store', data={'analysis_id': analysis_id}),
        own_title(__name__, analysis.name),
        own_nav_middle(__name__, analysis.id),
        own_nav_bottom(__name__, analysis.id),

        html.Div([
            dbc.Row([
                dbc.Col([

                ]),
            ]),
            dbc.Row([
                dbc.Col([

                ]),
                dbc.Col([

                ]),
            ]),
            dbc.Row([
                dbc.Col([

                ]),
            ]),
        ], className='div-standard')
    ])
