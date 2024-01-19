from flaskapp.dashapp.pages.utils import *

directory = get_directory(__name__)['directory']
page = get_directory(__name__)['page']
dash.register_page(__name__, path_template=f'/{directory}/{page}/<analysis_id>')
page_id = get_page_id(__name__)


def layout(analysis_id):
    analysis = db.session.get(Analysis, analysis_id)

    # Get the list of the model files linked to the analysis
    available_modelfiles = []

    for layertomodelfile in analysis.modelfiles:
        available_modelfiles.append({'value': layertomodelfile.id, 'label': layertomodelfile.name})

    # Get the last pricing relationship if existing
    last_pricingrelationship = db.session.query(PricingRelationship). \
        filter_by(analysis_id=analysis.id).order_by(PricingRelationship.id.desc()).first()

    # Create a select component for each layer and add it to the list component_select_modelfiles
    component_select_modelfiles = []

    for layer in analysis.layers:

        # Get all the models files linked to the layer in the last pricing relationship
        selected_modelfiles = []

        if last_pricingrelationship:

            layertomodelfiles = db.session.query(LayerToModelfile).filter(
                LayerToModelfile.pricingrelationship_id == last_pricingrelationship.id,
                LayerToModelfile.layer_id == layer.id
            ).all()

            for layertomodelfile in layertomodelfiles:
                selected_modelfiles.append(layertomodelfile.modelfile_id)

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
        own_nav_bottom(__name__, analysis.id),

        html.Div([
            dbc.Row([
                dbc.Col([
                    html.Div(id=page_id + 'div-select-modelfiles', children=component_select_modelfiles),
                ], width=4),
            ]),
            dbc.Row([
                dbc.Col([
                    dmc.TextInput(
                        id=page_id + 'input-name-relationships',
                        placeholder='Enter the name of the relationships',
                    ),
                ], width=3),
                dbc.Col([
                    own_button(page_id + 'btn-save', 'Save'),
                ], width=3),
            ]),
            dbc.Row([
                dbc.Col([
                    html.Div(id=page_id + 'div-relationships-modified'),
                ], width=4),
            ]),
        ], className='div-standard')
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
def save_relationships(n_clicks, data, id_, value, name):
    # id_ is a list of dictionaries that contains the layer id for each select component
    # e.g. [{'page_id': page_id, 'type': 'select-modelfiles', 'layer_id': 1}, {'page_id': page_id, 'type': 'select-modelfiles', 'layer_id': 2}]
    # value is a list of the lists that give the ids of the selected model files for each layer
    # e.g. [[54, 65], [54], [54]]
    analysis_id = data['analysis_id']
    n_layers = len(id_)

    # Save the pricing relationship file
    pricingrelationship = PricingRelationship(
        name=name,
        analysis_id=analysis_id,
    )
    db.session.add(pricingrelationship)
    db.session.commit()

    # Save the layer-to-modelfiles relationships
    for i in range(n_layers):
        layer_id = id_[i]['layer_id']
        layer = db.session.get(Layer, layer_id)

        for modelfile_id in value[i]:
            modelfile = db.session.get(ModelFile, modelfile_id)

            layertomodelfile = LayerToModelfile(
                name=f'{layer.name} - {modelfile.name}',
                pricingrelationship_id=pricingrelationship.id,
                layer_id=layer.id,
                modelfile_id=modelfile.id
            )
            db.session.add(layertomodelfile)
        db.session.commit()  # Commit after the loop for DB performance

    alert = dbc.Alert(
        'The relationships have been saved',
        id=page_id + 'alert-relationships-saved',
        color='success',
        duration=4000,
    )

    return alert
