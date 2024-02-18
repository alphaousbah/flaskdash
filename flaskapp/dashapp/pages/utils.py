"""
This module defines various utility functions and components for the application.

Functions:
- get_nav_top(): Create the top navigation bar with a logo and links.
- get_title(module, analysis_name): Generate a title for a specific page within the application.
- get_nav_middle(module, analysis_id): Create a middle navigation bar with links to different sections.
- get_chapter_target(chapter): Determine the target page for a given section (e.g., 'analysis', 'data').
- get_nav_bottom(module, analysis_id): Create a bottom navigation bar with links to additional pages.
- get_directory(module): Extract the directory and page names from a module path.
- get_navloc(module): Determine the navigation location for a given page.
- get_page_id(module): Generate a unique page ID based on the directory and page names.
- df_from_query(query): Convert SQLAlchemy query results into a pandas DataFrame.
- get_table_analyses(component_id, query): Generate a data table for analysis records.
- get_table_layers(component_id, query): Generate a data table for layers records.
- get_table_lossfiles(component_id, query): Generate a data table for loss files records.
- get_table_losses(component_id, query): Generate a data table for loss records.
- get_table_modelfiles(component_id, query): Generate a data table for model files records.
- get_table_relationships(component_id, query): Generate a data table for relationship records.
- get_datatable_style_header(): Define the style for data table headers.
- get_datatable_css(): Define custom CSS rules for data tables.
- get_datatable_style_cell(): Define the style for data table cells.
- get_button(component_id, name): Create a button component.
- get_lognorm_param(serie): Calculate log-normal distribution parameters from a data series.

Dependencies:
- dash
- dash_bootstrap_components
- numpy
- pandas

"""

# TODO: Update the doctring
import dash
from dash import html, dcc, dash_table, callback, Output, Input, State, ALL, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import dash_ag_grid as dag
from flaskapp.extensions import session
from flaskapp.models import *
import numpy as np
import pandas as pd
from scipy.stats import lognorm
import plotly.express as px
from io import StringIO
import os
import time


def own_nav_top():
    return dbc.Navbar(
        dbc.Container([
            html.A(
                dbc.Row([
                    dbc.Col(html.Img(src='/dashapp/assets/logo-ccr-re.png', height="30px")),
                    dbc.Col(dbc.NavbarBrand('SLy', className="ms-2")),
                ],
                    align='center',
                    className='g-0',
                ),
                href='#',
                style={'textDecoration': 'none'},
            ),
            dbc.NavbarToggler(id='navbar-toggler', n_clicks=0),
            dbc.Collapse(
                dbc.Nav([
                    dbc.NavLink('Search', href='/dashapp/'),
                    dbc.NavLink('Create Analysis', href='/dashapp/analysis/create'),
                    dbc.DropdownMenu(
                        [
                            dbc.DropdownMenuItem('Entry 1'),
                            dbc.DropdownMenuItem('Entry 2'),
                            dbc.DropdownMenuItem(divider=True),
                            dbc.DropdownMenuItem('Entry 3'),
                        ],
                        nav=True,
                        in_navbar=True,
                        label='Dropdown',
                        className='me-auto',  # The following navitems will be on the right of the navbar
                    ),
                    dbc.NavLink('abah@ccr-re.fr (add Flask Login)', href='#'),
                ],
                    className='w-100',
                ),
                id='navbar-collapse',
                is_open=False,
                navbar=True,
            ),
        ],
            fluid=True,
        ),
        color='dark',
        dark=True,
        className='mb-1',
    )


def own_title(module, analysis_name):
    directory_name = get_directory(module)['directory']
    page_name = get_directory(module)['page']

    if page_name != directory_name:
        string_title = str(analysis_name) + ' | ' + str(directory_name).capitalize() + ' | ' + str(
            page_name).capitalize()
    else:
        string_title = str(analysis_name) + ' | ' + str(directory_name).capitalize()

    title = html.Div(
        html.H5(string_title, className='title')
    )

    return title


def own_nav_middle(module, analysis_id):
    directory_name = get_directory(module)['directory']

    nav_middle = dbc.Nav([
        dbc.NavLink(
            str(chapter).capitalize(),
            href=f'/dashapp/{chapter}/{get_chapter_target(chapter)}/{analysis_id}',
            active=(chapter == directory_name),
        )
        for chapter in ['analysis', 'data', 'models', 'relationships', 'results']
    ],
        pills=True,
        className='nav_middle',
    )

    return nav_middle


def get_chapter_target(chapter):
    match chapter:
        case 'analysis':
            return 'view'
        case 'data':
            return 'layers'
        case 'relationships':
            return 'define'
        case 'models':
            return 'experience'
        case 'results':
            return 'manage'


def own_nav_bottom(module, analysis_id):
    directory_name = get_directory(module)['directory']

    nav_bottom = dbc.Nav([
        dbc.NavLink(
            page['name'],
            href=str(page['relative_path']).replace('none', str(analysis_id)),
            active='exact'
        )
        for page in dash.page_registry.values()
        if own_navloc(page['module']) == 'bottom' and str(page['path']).startswith('/' + directory_name)
    ],
        pills=True,
        className='nav_bottom',
    )

    return html.Div(nav_bottom)


def get_directory(module):
    # # Run this script to understand the code of the function
    # module1 = 'flaskapp.dashapp/pages.data'
    # module2 = 'flaskapp.dashapp/pages.data.premiums'
    #
    # index_pages_module1 = module1.index('pages')
    # index_pages_module2 = module2.index('pages')
    #
    # directory1 = str(module1[index_pages_module1:]).split('.')[1]
    # directory2 = str(module2[index_pages_module2:]).split('.')[1]
    #
    # page1 = str(module1[index_pages_module1:]).split('.')[-1]
    # page2 = str(module2[index_pages_module2:]).split('.')[-1]
    #
    # print(directory1)  # data = the directory name we want
    # print(directory2)  # data = the directory name we want
    #
    # print(page1)  # data = the page name we want
    # print(page2)  # premiums = the page name we want
    index_string_pages = str(module).index('pages')
    substring = str(module)[index_string_pages:].split('.')
    directory_name = substring[1]
    page_name = substring[-1]

    return {'directory': directory_name, 'page': page_name}


def own_navloc(module):
    page_name = str(module).split('.')[-1]

    match page_name:
        case 'search' | 'create':
            return 'top'
        case 'analysis' | 'data' | 'models' | 'results':
            return 'middle'
        case _:
            return 'bottom'


def get_page_id(module):
    directory_name = get_directory(module)['directory']
    page_name = get_directory(module)['page']

    if page_name != directory_name:
        page_id = directory_name + '-' + page_name + '-'
    else:
        page_id = page_name

    return page_id


def df_from_sqla(query):
    # https://stackoverflow.com/questions/1958219/how-to-convert-sqlalchemy-row-object-to-a-python-dict
    list_from_query = \
        [{col.name: str(getattr(record, col.name)) for col in record.__table__.columns} for record in query]

    return pd.DataFrame(list_from_query)


def get_link_results(row):
    # Check if the pricing relationships has already been processed,
    # that is if a corresponding result file exists
    # If so, create a link to the result
    # TODO: Correct below with the new DB models and the new querying style
    resultfile = session.query(ResultFile) \
        .filter_by(analysis_id=row['analysis_id'], pricingrelationship_id=row['id']).first()

    if resultfile:
        # Link to the result
        return '[View results]' \
            + '(/dashapp/results/view/' + row['analysis_id'] + '?resultfile_id=' + str(resultfile.id) + ')'
    else:
        return 'Process to get results'


def own_button(component_id, name):
    return dbc.Button(
        name,
        id=component_id,
        outline=True,
        color='primary',
        className='button',
    )


def get_lognorm_param(serie):
    mean = np.mean(serie)
    std = np.std(serie)

    mu = np.log(mean / np.sqrt(1 + std ** 2 / mean ** 2))
    scale = np.exp(mu)
    s = np.sqrt(np.log((1 + std ** 2 / mean ** 2)))

    return {
        'mean': mean,
        'std': std,
        'mu': mu,
        'scale': scale,
        's': s
    }


def get_df_oep_summary(layers, modelfiles, resultyearlosses):
    # Initialize the OEP table
    QUANTILES = [.999, .998, .996, .995, .99, .98, .9667, .96, .95, .9, .8, .5]
    df_oep = pd.DataFrame({
        'quantile': [f'{quantile:.2%}' for quantile in QUANTILES],
        'return period': [f'{1 / (1 - quantile):,.0f}' for quantile in QUANTILES],
        'proba': QUANTILES,
    })

    # Initialize the summary table
    df_summary = pd.DataFrame({
        'quantile': ['Pure premium', 'Standard deviation'],
        'return period': [''] * 2,
        'proba': [''] * 2,
    }, index=['Pure premium', 'Standard deviation'])

    # Add rows to df_summary relating to the model files
    df_summary_index_ini = list(df_summary.index)

    for modelfile in modelfiles:
        df_summary.loc[len(df_summary)] = [f'PP {modelfile.name}'] + [''] * 2

    df_summary.index = df_summary_index_ini + [f'PP {modelfile.name}' for modelfile in modelfiles]

    """
    What df_summary will look like:

    index               quantile            return period       proba
    -------------------------------------------------------------------
    Pure premium        Pure premium        ''                  ''
    Standard deviation  Standard deviation  ''                  ''
    Model File 1        PP Model File 1     ''                  ''
    Model File 2        PP Model File 1     ''                  ''
    ...                 ...                 ''                  ''

    """

    # Add columns to df_summary relating to the layers
    for layer in layers:
        df_summary[layer.name] = [''] * len(df_summary.index)

    """
    What df_summary will look like:

    index               quantile            return period       proba       Layer 1     Layer2
    ---------------------------------------------------------------------------------------------
    Pure premium        Pure premium        ''                  ''          ''          ''
    Standard deviation  Standard deviation  ''                  ''          ''          ''
    Model File 1        PP Model File 1     ''                  ''          ''          ''
    Model File 2        PP Model File 1     ''                  ''          ''          ''
    ...                 ...                 ''                  ''          ''          ''

    """

    # Get the OEP, pure premium and standard deviation by layer
    for layer in layers:
        resultyearlosses_for_layer = [
            resultyearloss for resultyearloss in resultyearlosses
            if resultyearloss.layermodelfile.layer == layer
        ]

        if len(resultyearlosses_for_layer) > 0:
            recoveries = df_from_sqla(resultyearlosses_for_layer)[['year', 'recovery']]
            recoveries['recovery'] = recoveries['recovery'].astype(int)

            recoveries_by_year = recoveries.groupby('year')['recovery'].sum()
            df_oep[layer.name] = df_oep['proba'].map(lambda proba: f'{recoveries_by_year.quantile(proba):,.0f}')

            df_summary.at['Pure premium', layer.name] = f'{recoveries_by_year.mean():,.0f}'
            df_summary.at['Standard deviation', layer.name] = f'{recoveries_by_year.std():,.0f}'

        # Get the expected loss by loss model
        for modelfile in modelfiles:
            resultyearlosses_for_layer_and_modelfile = [
                resultyearloss for resultyearloss in resultyearlosses_for_layer
                if resultyearloss.layermodelfile.modelfile == modelfile
            ]
            recoveries_modelfile = df_from_sqla(resultyearlosses_for_layer_and_modelfile)

            if len(recoveries_modelfile) > 0:
                recoveries_modelfile['recovery'] = recoveries_modelfile['recovery'].astype(int)
                df_summary.at[f'PP {modelfile.name}', layer.name] \
                    = f'{round(recoveries_modelfile["recovery"].mean()):,.0f}'

    return df_oep, df_summary
