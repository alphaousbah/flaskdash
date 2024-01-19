from flaskapp.dashapp.pages.utils import *

layout = html.Div([
    dcc.Store(id='app_store', data={}, storage_type='session'),
    own_nav_top(),
    dash.page_container,
])


# Add callback for toggling the navbar collapse on small screens
@callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
)
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open
