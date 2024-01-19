from flaskapp.dashapp.pages.utils import *

directory = get_directory(__name__)['directory']
page = get_directory(__name__)['page']
dash.register_page(__name__, path_template=f'/{directory}/{page}/<analysis_id>', order=1)
page_id = get_page_id(__name__)


def layout(analysis_id):
    analysis = db.session.get(Analysis, analysis_id)
    df = df_from_sqla(analysis.pricingrelationships)
    try:
        df['results'] = df.apply(get_link_results, axis=1)
    except ValueError as e:
        print(e)

    return html.Div([
        dcc.Store(id=page_id + 'store', data={'analysis_id': analysis_id}),
        own_title(__name__, analysis.name),
        own_nav_middle(__name__, analysis.id),
        own_nav_bottom(__name__, analysis.id),

        html.Div([
            dbc.Row([
                dbc.Col([
                    own_button(page_id + 'btn-process', 'Process'),
                    own_button(page_id + 'btn-delete', 'Delete'),
                    dcc.Loading(
                        html.Div(
                            dag.AgGrid(
                                id=page_id + 'grid-relationships',
                                rowData=df.to_dict('records'),
                                columnDefs=[
                                    {'field': 'id', 'hide': True},
                                    {'field': 'name', 'checkboxSelection': True},
                                    {'field': 'results', 'cellRenderer': 'markdown'},
                                ],
                                getRowId='params.data.id',
                                columnSize='responsiveSizeToFit',
                                dashGridOptions={
                                    'domLayout': 'autoHeight',
                                    'rowSelection': 'multiple',
                                },
                            ),
                        ),
                        id=page_id + 'loading-div-table-relationships',
                    ),
                ], width=5, className='mb-2'),
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Alert(
                        'The result has been saved',
                        id=page_id + 'alert_save',
                        color='success',
                        is_open=False,
                        duration=4000,
                    ),
                ], width=5),
            ]),
            dbc.Row([
                dbc.Col([

                ]),
            ]),
        ], className='div-standard')
    ])


@callback(
    Output(page_id + 'grid-relationships', 'rowData'),
    Output(page_id + 'alert_save', 'is_open'),
    Input(page_id + 'btn-process', 'n_clicks'),
    State(page_id + 'store', 'data'),
    State(page_id + 'grid-relationships', 'selectedRows'),
)
def process_result(n_clicks, data, selectedRows):
    if n_clicks is None or selectedRows is None:
        return no_update

    analysis_id = data['analysis_id']
    analysis = db.session.get(Analysis, analysis_id)
    is_open = False
    start = time.perf_counter()  # TODO: Timer

    for row in selectedRows:
        # Check if the pricing relationships has already been processed
        # If not, process and save the result file and the result year losses
        pricingrelationship_id = row['id']
        check = db.session.query(ResultFile). \
            filter_by(analysis_id=analysis_id, pricingrelationship_id=pricingrelationship_id).first()

        if not check:
            # Save the result file
            resultfile = ResultFile(
                name=db.session.get(PricingRelationship, pricingrelationship_id).name,
                analysis_id=analysis_id,
                pricingrelationship_id=pricingrelationship_id
            )
            db.session.add(resultfile)
            db.session.commit()

            # Save the result year losses
            for layertomodelfile in resultfile.pricingrelationship.layertomodelfiles:
                layer = layertomodelfile.layer
                modelfile = layertomodelfile.modelfile

                for modelyearloss in modelfile.modelyearlosses:
                    resultyearloss = ResultYearLoss(
                        name=modelyearloss.name,
                        resultfile_id=resultfile.id,
                        layertomodelfile_id=layertomodelfile.id,
                        year=modelyearloss.year,
                        # For the SL, the amount contains the simulated loss ratio
                        grossloss=layer.premium * modelyearloss.amount
                    )

                    # Apply the SL cover to get the recovery and net amount
                    resultyearloss.recovery = get_sl_recovery(
                        resultyearloss.grossloss,
                        layer.premium,
                        layer.limit,
                        layer.deductible,
                    )
                    resultyearloss.netloss = resultyearloss.grossloss - resultyearloss.recovery

                    db.session.add(resultyearloss)
                db.session.commit()  # Commit after the loop for DB performance

            is_open = True

    df = df_from_sqla(analysis.pricingrelationships)
    df['results'] = df.apply(get_link_results, axis=1)
    rowData = df.to_dict('records')

    print(f'Elapsed time: {time.perf_counter() - start}')  # TODO: Timer
    return rowData, is_open
