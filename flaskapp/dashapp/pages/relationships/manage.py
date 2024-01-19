from flaskapp.dashapp.pages.utils import *

directory = get_directory(__name__)['directory']
page = get_directory(__name__)['page']
dash.register_page(__name__, path_template=f'/{directory}/{page}/<analysis_id>')
page_id = get_page_id(__name__)


def layout(analysis_id):
    analysis = db.session.get(Analysis, analysis_id)

    # Get the list of the model files linked to the analysis
    available_modelfiles = []

    for modelfile in analysis.modelfiles:
        available_modelfiles.append({'value': modelfile.id, 'label': modelfile.name})

    # Get the last pricing relationship if existing
    last_pricingrelationship = db.session.query(PricingRelationship).order_by(PricingRelationship.id.desc()).first()

    # Create a select component for each layer and add it to the list component_select_modelfiles
    component_select_modelfiles = []

    for layer in analysis.layers:

        # Get all the models files linked to the layer in the last pricing relationship
        selected_modelfiles = []

        if last_pricingrelationship:

            layer_modelfiles = db.session.query(LayerToModelfile).filter(
                LayerToModelfile.pricingrelationship == last_pricingrelationship,
                LayerToModelfile.layer == layer
            ).all()

            for modelfile in layer_modelfiles:
                selected_modelfiles.append(modelfile.id)

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
                    'Content',
                ]),
            ]),
        ], className='div-standard')
    ])
