from flaskapp.dashapp.pages.utils import *

directory = get_directory(__name__)['directory']
page = get_directory(__name__)['page']
dash.register_page(__name__, path_template=f'/{directory}/{page}/<analysis_id>')
page_id = get_page_id(__name__)


def layout(analysis_id):
    analysis = session.get(Analysis, analysis_id)

    if analysis.layers:
        df = df_from_sqla(analysis.layers)
        df = df.sort_values(['display_order', 'id'], ascending=[True, True])
    else:
        # Create an empty pandas dataframe
        # https://stackoverflow.com/questions/13784192/creating-an-empty-pandas-dataframe-and-then-filling-it
        df = pd.DataFrame([])

    return html.Div([
        dcc.Store(id=page_id + 'store', data={'analysis_id': analysis_id}),
        own_title(__name__, analysis.name),
        own_nav_middle(__name__, analysis.id),
        own_nav_bottom(__name__, analysis.id),

        html.Div([
            dbc.Row([
                dbc.Col([
                    dbc.DropdownMenu(
                        label='Add layers',
                        children=[
                            dbc.DropdownMenuItem('1', id=page_id + 'btn-create-1'),
                            dbc.DropdownMenuItem('2', id=page_id + 'btn-create-2'),
                            dbc.DropdownMenuItem('3', id=page_id + 'btn-create-3'),
                            dbc.DropdownMenuItem('4', id=page_id + 'btn-create-4'),
                            dbc.DropdownMenuItem('5', id=page_id + 'btn-create-5'),
                        ],
                        className='button',
                        toggle_style={
                            'color': '#2780e3',
                            'fontSize': '13px',
                            'background': '#f5f8fa',
                        }
                    ),
                    own_button(page_id + 'btn-save', 'Save Layers'),
                    own_button(page_id + 'btn-delete', 'Delete Layers'),
                ], width=5),
                dbc.Col([
                    html.Div(id=page_id + 'div-layers-modif'),
                ], width=7),
            ]),
            dbc.Row([
                dbc.Col([
                    # https://www.ag-grid.com/react-data-grid/cell-data-types/
                    dag.AgGrid(
                        id=page_id + 'grid-layers',
                        rowData=df.to_dict('records'),
                        columnDefs=[
                            {'field': 'id', 'hide': True},
                            {'field': 'analysis_id', 'hide': True},
                            {'field': 'display_order', 'hide': True},
                            {
                                'field': 'name',
                                'checkboxSelection': True, 'headerCheckboxSelection': True,
                                'rowDrag': True,
                            },
                            {
                                'field': 'premium',
                                'valueFormatter': {'function': 'd3.format(",d")(params.value)'}
                            },
                            {
                                'field': 'agg_limit',
                                'valueFormatter': {'function': '(params.value) + "%"'}
                            },
                            {
                                'field': 'agg_deduct',
                                'valueFormatter': {'function': '(params.value) + "%"'}
                            },
                        ],
                        getRowId='params.data.id',
                        defaultColDef={
                            'flex': True,
                            'editable': True,
                        },
                        columnSize='responsiveSizeToFit',
                        dashGridOptions={
                            'domLayout': 'autoHeight',
                            'rowSelection': 'multiple',
                            'rowDragManaged': True, 'rowDragMultiRow': True, 'animateRows': True
                        },
                        className='ag-theme-alpine custom mb-2',
                    ),
                ], width=12)
            ]),
        ], className='div-standard')
    ])


# Callback that creates n layers with n defined by the click on the dropdown menu
for i in [1, 2, 3, 4, 5]:
    @callback(
        Output(page_id + 'grid-layers', 'rowTransaction', allow_duplicate=True),
        Output(page_id + 'div-layers-modif', 'children', allow_duplicate=True),
        Input(page_id + f'btn-create-{i}', 'n_clicks'),
        State(page_id + 'store', 'data'),
        State(page_id + f'btn-create-{i}', 'children'),
        config_prevent_initial_callbacks=True
    )
    def create_layers(n_clicks, data, n_layers):  # n_layers = children property of btn-create
        analysis_id = data['analysis_id']
        analysis = session.get(Analysis, analysis_id)
        n_layers = int(n_layers[0])

        # Initialize the grid transaction
        newRows = []

        for i in range(n_layers):
            # Set the layers default parameters values
            name = 'Enter a name'
            premium = 0
            agg_limit = 0
            agg_deduct = 0
            display_order = 999  # Set display_order to 999 so that the new layers are displayed in the last position

            layer = Layer(
                name=name,
                premium=premium,
                agg_limit=agg_limit,
                agg_deduct=agg_deduct,
                display_order=display_order,
            )
            analysis.layers.append(layer)
            session.flush()

            newRows.append(
                {
                    'id': layer.id,
                    'name': layer.name,
                    'premium': layer.premium,
                    'agg_limit': layer.agg_limit,
                    'agg_deduct': layer.agg_deduct,
                    'display_order': layer.display_order,
                    'analysis_id': analysis_id
                }
            )
        session.commit()

        alert = dbc.Alert(
            'The layers have been modified. Save the changes with the Save button',
            id=page_id + 'alert-modified',
            color='danger',
            className='text-center',
        )

        return {'add': newRows}, alert


@callback(
    Output(page_id + 'grid-layers', 'rowTransaction'),
    Output(page_id + 'div-layers-modif', 'children', allow_duplicate=True),
    Input(page_id + 'btn-delete', 'n_clicks'),
    State(page_id + 'grid-layers', 'selectedRows'),
    State(page_id + 'store', 'data'),
    config_prevent_initial_callbacks=True
)
def delete_layers(n_clicks, selectedRows, data):
    if n_clicks is None or selectedRows is None:
        raise PreventUpdate

    # Identify and get the analysis
    analysis_id = data['analysis_id']
    analysis = session.get(Analysis, analysis_id)

    # Delete the selected layers
    for row in selectedRows:
        layer_id = row['id']
        layer = session.get(Layer, layer_id)
        session.delete(layer)
    session.commit()  # Commit after the loop for DB performance

    alert = dbc.Alert(
        'The layers have been deleted',
        id=page_id + 'alert-deleted',
        duration=3000,
        className='text-center',
    )

    # Update the layers table
    return {'remove': selectedRows}, alert


@callback(
    Output(page_id + 'div-layers-modif', 'children', allow_duplicate=True),
    Input(page_id + 'grid-layers', 'cellValueChanged'),
    # Input(page_id + 'grid-layers', 'virtualRowData'),
    config_prevent_initial_callbacks=True
)
def inform_layers_modified(cellValueChanged):
    alert = dbc.Alert(
        'The layers have been modified. Save the changes with the Save button',
        color='danger',
        className='text-center',
    )
    return alert


# TODO: Correct with session.rollback and only one commit!!!
@callback(
    Output(page_id + 'div-layers-modif', 'children'),
    Input(page_id + 'btn-save', 'n_clicks'),
    State(page_id + 'grid-layers', 'virtualRowData'),  # Use virtualRowData instead of rowData to get the rows order
    config_prevent_initial_callbacks=True
)
def save_layers(n_clicks, virtualRowData):
    try:
        for row in virtualRowData:
            layer = session.get(Layer, row['id'])
            layer.name = row['name']
            layer.premium = row['premium']
            layer.agg_limit = row['agg_limit']
            layer.agg_deduct = row['agg_deduct']
            layer.display_order = virtualRowData.index(row)
        session.commit()  # Commit after the loop for DB performance and input data checking

        alert = dbc.Alert(
            'The changes have been saved',
            className='text-center',
        )
    except ValueError as e:
        alert = dbc.Alert(
            str(e),
            color='danger',
            className='text-center',
        )
    return alert
