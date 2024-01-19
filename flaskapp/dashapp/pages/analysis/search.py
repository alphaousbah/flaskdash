from flaskapp.dashapp.pages.utils import *

dash.register_page(__name__, path='/')
page_id = get_page_id(__name__)


def layout():
    if Analysis.query.all():
        df = df_from_sqla(Analysis.query.order_by(Analysis.id.desc()).all())

        for col in ['quote', 'name']:
            df[col] = '[' + df[col] + '](/dashapp/analysis/view/' + df['id'].astype(str) + ')'
    else:
        df = pd.DataFrame([])

    return html.Div([
        html.H5('Analysis Search', className='title'),
        html.Div([
            dbc.Row([
                dbc.Col([
                    dcc.Link(dbc.Button('Create', id=page_id + 'btn-create', className='button'),
                             href='/dashapp/analysis/create'),
                    dbc.Button('Copy', id=page_id + 'btn-copy', className='button'),
                    dbc.Button('Delete', id=page_id + 'btn-delete', className='button'),
                ]),
            ]),
            dbc.Row([
                dbc.Col([
                    dag.AgGrid(
                        id=page_id + 'grid-analyses',
                        rowData=df.to_dict('records'),
                        columnDefs=[
                            {'field': 'id', 'hide': True},
                            {'field': 'quote', 'cellRenderer': 'markdown', 'checkboxSelection': True},
                            {'field': 'name', 'cellRenderer': 'markdown'},
                            {'field': 'client'},
                        ],
                        getRowId='params.data.id',
                        defaultColDef={
                            'flex': True, 'sortable': True, 'filter': True, 'floatingFilter': True,
                        },
                        columnSize='responsiveSizeToFit',
                        dashGridOptions={
                            'domLayout': 'autoHeight',
                            'rowSelection': 'multiple',
                        },
                        className='ag-theme-alpine custom',
                    ),
                ], width=6),
            ]),
        ], className='div-standard'),
    ]),


# TODO: Add a modal to ask the user to confirm the deletion
@callback(
    Output(page_id + 'grid-analyses', 'rowTransaction'),
    Input(page_id + 'btn-delete', 'n_clicks'),
    State(page_id + 'grid-analyses', 'selectedRows'),
)
def delete_analysis(n_clicks, selectedRows):
    if n_clicks is None or selectedRows is None:
        return no_update

    # Delete selected analyses
    for row in selectedRows:
        analysis_id = row['id']
        analysis = db.session.get(Analysis, analysis_id)
        db.session.delete(analysis)
    db.session.commit()  # Commit after the loop for DB performance

    # Update the analyses grid
    return {'remove': selectedRows}
