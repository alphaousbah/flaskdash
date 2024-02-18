from flaskapp.dashapp.pages.utils import *

directory = get_directory(__name__)['directory']
page = get_directory(__name__)['page']
dash.register_page(__name__, path_template=f'/{directory}/{page}/<analysis_id>', order=2)
page_id = get_page_id(__name__)


def layout(analysis_id, resultfile_id=None):
    analysis = session.get(Analysis, analysis_id)

    if resultfile_id:
        resultfile = session.get(ResultFile, resultfile_id)
    else:
        # Get the last result file in none was provided via the url's query string
        # TODO: Correct query below
        resultfile = session.query(ResultFile).filter_by(analysis_id=analysis.id).order_by(
            ResultFile.id.desc()).first()

    if resultfile:
        # Set the title of the page
        title = resultfile.name.capitalize()

        # Get the layers and model files for the pricing relationship of the result file
        # Use the set() function to get the model files and layers without repetition
        # Sort the objects by name with the sorted() function
        layermodelfiles = resultfile.pricingrelationship.layermodelfiles

        modelfiles = set([layermodelfile.modelfile for layermodelfile in layermodelfiles])
        modelfiles = sorted(modelfiles, key=lambda modelfile: modelfile.name)

        layers = set([layermodelfile.layer for layermodelfile in layermodelfiles])
        layers = sorted(layers, key=lambda layer: layer.name)

        # Get the year loss table for the result file
        resultyearlosses = resultfile.resultyearlosses

        df_oep, df_summary = get_df_oep_summary(layers, modelfiles, resultyearlosses)
        resultfile_name = resultfile.name

    else:
        # Set the title of the page with no results provided
        title = 'Process a pricing model to get the results'
        df_oep, df_summary = pd.DataFrame(), pd.DataFrame()
        resultfile_name = ''

    return html.Div([
        dcc.Store(id=page_id + 'store', data={'analysis_id': analysis_id, 'resultfile_id': resultfile_id}),
        own_title(__name__, analysis.name),
        own_nav_middle(__name__, analysis.id),
        own_nav_bottom(__name__, analysis.id),

        html.Div([
            dbc.Row([
                dbc.Col([
                    html.Div(title, className='h6 mb-3'),
                ]),
            ]),
            dbc.Row([
                dbc.Col([
                    # https://dash.plotly.com/dash-ag-grid/row-pinning
                    dag.AgGrid(
                        id=page_id + 'grid-oep',
                        rowData=df_oep.to_dict('records'),
                        columnDefs=[{'field': col} for col in df_oep.columns if col != 'proba'],
                        columnSize='responsiveSizeToFit',
                        dashGridOptions={
                            'domLayout': 'autoHeight',
                            'pinnedBottomRowData': df_summary.to_dict('records'),
                        },
                        csvExportParams={'fileName': f'Results {resultfile_name}.csv'},
                        className='ag-theme-alpine custom mb-2',
                    ),
                ]),
            ]),
            dbc.Row([
                dbc.Col([
                    own_button(page_id + 'btn-export', 'Export Results to CSV'),
                ]),
            ]),
            dbc.Row([
                dbc.Col([

                ]),
            ]),
        ], className='div-standard')
    ])

@callback(
    Output(page_id + 'grid-oep', 'exportDataAsCsv'),
    Input(page_id + 'btn-export', 'n_clicks'),
    config_prevent_initial_callbacks=True
)
def export_data_to_csv(n_clicks):
    if n_clicks:
        return True
    return False
