import dash_bootstrap_components

from flaskapp.dashapp.pages.utils import *

directory = get_directory(__name__)['directory']
page = get_directory(__name__)['page']
dash.register_page(__name__, path_template=f'/{directory}/{page}/<analysis_id>')
page_id = get_page_id(__name__)


def layout(analysis_id):
    analysis = session.get(Analysis, analysis_id)

    # Get the list of the model files linked to the analysis
    available_modelfiles = []

    for layermodelfile in analysis.modelfiles:
        available_modelfiles.append({'value': layermodelfile.id, 'label': layermodelfile.name})

    # Get the last pricing relationship if existing
    # TODO: Correct below with the new DB models and the new querying style
    last_pricingrelationship = session.query(PricingRelationship). \
        filter_by(analysis_id=analysis.id).order_by(PricingRelationship.id.desc()).first()

    # Create a select component for each layer and add it to the list component_select_modelfiles
    component_select_modelfiles = []

    for layer in analysis.layers:

        # Get all the models files linked to the layer in the last pricing relationship
        selected_modelfiles = []

        if last_pricingrelationship:
            # TODO: Correct below with the new DB models and the new querying style
            layermodelfiles = session.query(LayerModelFile).filter(
                LayerModelFile.pricingrelationship_id == last_pricingrelationship.id,
                LayerModelFile.layer_id == layer.id
            ).all()

            for layermodelfile in layermodelfiles:
                selected_modelfiles.append(layermodelfile.modelfile_id)

        # Create the select component
        select_modelfiles = dmc.MultiSelect(
            id={'page_id': page_id, 'type': 'select-modelfiles', 'layer_id': layer.id},
            label=f'Layer {layer.name}',
            placeholder='Click here to select the model files',
            data=available_modelfiles,
            value=selected_modelfiles,
            clearable=True,
            className='mb-3',
        )

        component_select_modelfiles.append(select_modelfiles)

    return html.Div([
        dcc.Store(id=page_id + 'store', data={'analysis_id': analysis_id}),
        own_title(__name__, analysis.name),
        own_nav_middle(__name__, analysis.id),

        html.Div([
            dbc.Row([
                dbc.Col([
                    dbc.Row([
                        dbc.Col([
                            html.Div(id=page_id + 'div-select-modelfiles', children=component_select_modelfiles),
                        ]),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dmc.TextInput(
                                id=page_id + 'input-name-relationships',
                                placeholder='Enter the name of the relationships',
                            ),
                        ], width=8),
                        dbc.Col([
                            own_button(page_id + 'btn-save', 'Save'),
                        ], width=4),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            html.Div(id=page_id + 'div-relationships-modified'),
                        ]),
                    ]),
                ], className='div-standard', width=5),
                dbc.Col([
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                dag.AgGrid(
                                    id=page_id + 'grid-relationships',
                                    rowData=df_from_sqla(analysis.pricingrelationships).to_dict('records'),
                                    columnDefs=[
                                        {'field': 'id', 'hide': True},
                                        {'field': 'name', 'checkboxSelection': True, 'headerCheckboxSelection': True},
                                    ],
                                    getRowId='params.data.id',
                                    defaultColDef={'flex': True, 'sortable': True, 'filter': True,
                                                   'floatingFilter': True},
                                    columnSize='responsiveSizeToFit',
                                    dashGridOptions={
                                        'domLayout': 'autoHeight',
                                        'rowSelection': 'single',
                                    },
                                    className='ag-theme-alpine custom',
                                ),
                            ], className='mb-3'),
                        ]),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            own_button(page_id + 'btn-select', 'Select'),
                            own_button(page_id + 'btn-delete', 'Delete'),
                        ]),
                    ]),
                ], className='div-standard', width=5),
            ]),
        ])
    ])


# https://dash.plotly.com/pattern-matching-callbacks
@callback(
    Output(page_id + 'div-relationships-modified', 'children', allow_duplicate=True),
    Input({'page_id': page_id, 'type': 'select-modelfiles', 'layer_id': ALL}, 'value'),
    config_prevent_initial_callbacks=True
)
def inform_relationships_modified(value):
    alert = dbc.Alert(
        'Save the new relationships with the Save button',
        id=page_id + 'alert-relationships-modified',
        color='danger',
    )
    return alert


@callback(
    Output(page_id + 'div-relationships-modified', 'children'),
    Input(page_id + 'btn-save', 'n_clicks'),
    State(page_id + 'store', 'data'),
    State({'page_id': page_id, 'type': 'select-modelfiles', 'layer_id': ALL}, 'id'),
    State({'page_id': page_id, 'type': 'select-modelfiles', 'layer_id': ALL}, 'value'),
    State(page_id + 'input-name-relationships', 'value'),
    config_prevent_initial_callbacks=True
)
def process_result(n_clicks, data, id_, value, name):
    # TODO: Go to the view result page after processing
    # id_ is a list of dictionaries that contains the layer id for each select component
    # e.g. [{'page_id': page_id, 'type': 'select-modelfiles', 'layer_id': 1}, {'page_id': page_id, 'type': 'select-modelfiles', 'layer_id': 2}]
    # value is a list of the lists that give the ids of the selected model files for each layer
    # e.g. [[54, 65], [54], [54]]
    start = time.perf_counter()
    analysis_id = data['analysis_id']
    analysis = session.get(Analysis, analysis_id)
    n_layers = len(id_)

    # Save the layer-to-modelfiles relationships
    for i in range(n_layers):
        layer_id = id_[i]['layer_id']
        layer = session.get(Layer, layer_id)

        # Clear the previous layer-to-modelfiles relationships
        layer.modelfiles.clear()

        # Append the new relationships
        for modelfile_id in value[i]:
            modelfile = session.get(ModelFile, modelfile_id)
            layer.modelfiles.append(modelfile)

    resultfile = ResultFile(name=name)
    analysis.resultfiles.append(resultfile)

    # Iterate over the layers and linked modelfiles to get the result file's layers, model files and result year losses
    for layer in analysis.layers:
        resultlayer = get_resultlayer_from(layer)
        resultfile.layers.append(resultlayer)

        for modelfile in layer.modelfiles:
            query = select(ResultModelFile).filter_by(resultfile=resultfile, id_src=modelfile.id)
            resultmodelfile = session.execute(query).scalar_one()

            # If resultmodelfile is None (= the original modelfile wasn't copied already) => copy the original modelfile
            if not resultmodelfile:
                resultmodelfile = get_resultmodelfile_from(modelfile)
                resultfile.modelfiles.append(resultmodelfile)

                for modelyearloss in modelfile.yearlosses:
                    resultmodelyearloss = get_resultmodelyearloss_from(modelyearloss)
                    resultmodelfile.yearlosses.append(resultmodelyearloss)

            resultlayer.modelfiles.append(resultmodelfile)

    # Create the year losses for each layer of the resultfile
    for resultlayer in resultfile.layers:
        for resultmodelfile in resultlayer.modelfiles:
            for modelyearloss in resultmodelfile.yearlosses:
                resultlayeryearloss = get_resultlayeryearloss_from(modelyearloss, resultlayer, resultmodelfile)
                resultlayer.yearlosses.append(resultlayeryearloss)

        # Work out the overall annual loss ratio and ceded ratio (for all resultmodelfiles)
        # https://www.tutorialspoint.com/how-to-groupby-and-sum-sql-columns-using-sqlalchemy-in-python
        query = select(
            ResultLayerYearLoss.year, func.sum(ResultLayerYearLoss.loss_ratio).label('loss_ratio')
        ).filter_by(layer=resultlayer).group_by(ResultLayerYearLoss.year)

        loss_ratio_by_year = pd.DataFrame(session.execute(query).all())
        loss_ratio_by_year.set_index('year', inplace=True)

        loss_ratio_by_year['ceded_loss_ratio'] = loss_ratio_by_year['loss_ratio'].apply(
            lambda loss_ratio: min(resultlayer.agg_limit / 100, max(0, loss_ratio - resultlayer.agg_deduct / 100)))

        loss_ratio_by_year['ceded_ratio'] = loss_ratio_by_year['ceded_loss_ratio'] / loss_ratio_by_year['loss_ratio']

        for resultlayeryearloss in resultlayer.yearlosses:
            year = resultlayeryearloss.year
            gross = resultlayeryearloss.gross
            ceded = gross * loss_ratio_by_year.at[year, 'ceded_ratio']
            resultlayeryearloss.ceded = ceded
            resultlayeryearloss.net = gross - ceded

    session.commit()

    alert = dbc.Alert(
        'The relationships have been saved and the result has been processed',
        id=page_id + 'alert-relationships-saved',
        color='success',
        duration=4000,
    )

    print(f'Elapsed time: {time.perf_counter() - start}')  # TODO: Timer
    return alert


def get_resultlayer_from(layer):
    resultlayer = ResultLayer(
        name=layer.name,
        premium=layer.premium,
        limit=layer.limit,
        deductible=layer.deductible,
    )
    return resultlayer


def get_resultmodelfile_from(modelfile):
    resultmodelfile = ResultModelFile(
        id_src=modelfile.id,
        name=modelfile.name,
        type=modelfile.type,
    )
    return resultmodelfile


def get_resultmodelyearloss_from(modelyearloss):
    resultmodelyearloss = ResultModelYearLoss(
        year=modelyearloss.year,
        loss_ratio=modelyearloss.loss_ratio,
    )
    return resultmodelyearloss


def get_resultlayeryearloss_from(modelyearloss, resultlayer, resultmodelfile):
    resultlayeryearloss = ResultLayerYearLoss(
        model_id=resultmodelfile.id,
        model_name=resultmodelfile.name,
        year=modelyearloss.year,
        type=resultmodelfile.type,
        loss_ratio=modelyearloss.loss_ratio,
        gross=resultlayer.premium * modelyearloss.loss_ratio,
    )
    return resultlayeryearloss
