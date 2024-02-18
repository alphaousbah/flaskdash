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


# rowTransaction: https://dash.plotly.com/dash-ag-grid/client-side
@callback(
    Output(page_id + 'grid-analyses', 'rowTransaction', allow_duplicate=True),
    Input(page_id + 'btn-copy', 'n_clicks'),
    State(page_id + 'grid-analyses', 'selectedRows'),
    config_prevent_initial_callbacks=True
)
def copy_analyses(n_clicks, selectedRows):
    if n_clicks is None or selectedRows is None:
        return no_update

    # Copy the selected analyses
    newRows = []
    for row in selectedRows:
        analysis_id = row['id']
        analysis = session.get(Analysis, analysis_id)
        new = analysis.copy()
        session.add(new)
        session.commit()
        newRows.append(
            {
                'id': new.id,
                'quote': '[' + str(new.quote) + '](/dashapp/analysis/view/' + str(new.id) + ')',
                'name': '[' + new.name + '](/dashapp/analysis/view/' + str(new.id) + ')',
                'client': new.client
            }
        )
    # Update the analyses grid
    return {'add': newRows, 'addIndex': 0}


@callback(
    Output(page_id + 'grid-analyses', 'rowTransaction'),
    Input(page_id + 'btn-delete', 'n_clicks'),
    State(page_id + 'grid-analyses', 'selectedRows'),
)
def delete_analyses(n_clicks, selectedRows):
    if n_clicks is None or selectedRows is None:
        return no_update

    # Delete the selected analyses
    # SQLAlchemy error handling: https://docs.sqlalchemy.org/en/14/orm/session_basics.html#framing-out-a-begin-commit-rollback-block
    try:
        for row in selectedRows:
            analysis_id = row['id']
            analysis = session.get(Analysis, analysis_id)
            session.delete(analysis)
    except e:
        session.rollback()
        print(e)
        return no_update
    else:
        session.commit()
        return {'remove': selectedRows}
        # TODO: Add a modal to ask the user to confirm the deletion
