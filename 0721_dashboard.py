from dash import Dash, dcc, html, Input, Output, State, callback_context
from dash.dependencies import ALL
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from dash.exceptions import PreventUpdate

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = Dash(__name__, external_stylesheets=external_stylesheets)
app.config.suppress_callback_exceptions = True

# サンプルデータの作成
np.random.seed(0)
df = pd.DataFrame({"Col " + str(i + 1): np.random.rand(30) for i in range(6)})

# ヒートマップを作成するためのデータフレーム
heatmap_df = df.corr()

app.layout = html.Div(
    [
        html.Div(
            dcc.Graph(id="heatmap", config={"displayModeBar": False}),
            className="six columns",
        ),
        html.Div(
            id="scatter-plots-container",
            children=[],
            className="six columns",
        ),
        dcc.Store(id='scatter-plots-store', data=[]),  # 散布図のIDを保持するためのストア
    ],
    className="row",
)

# ヒートマップを作成する関数
def create_heatmap():
    fig = go.Figure(data=go.Heatmap(z=heatmap_df.values, x=heatmap_df.columns, y=heatmap_df.columns, colorscale="Viridis"))
    fig.update_layout(margin={"l": 20, "r": 20, "b": 20, "t": 20})
    return fig

# 散布図を作成する関数
def create_scatter_plot(x_col, y_col, selectedpoints=None):
    fig = px.scatter(df, x=x_col, y=y_col, text=df.index)
    fig.update_traces(
        selectedpoints=selectedpoints,
        customdata=df.index,
        mode="markers+text",
        marker={"color": "rgba(0, 116, 217, 0.7)", "size": 20},
        unselected={
            "marker": {"opacity": 0.3},
            "textfont": {"color": "rgba(0, 0, 0, 0)"},
        },
    )
    fig.update_layout(
        margin={"l": 20, "r": 0, "b": 15, "t": 5},
        dragmode="select",
        hovermode=False,
        newselection_mode="gradual",
    )
    return fig

@app.callback(
    Output("scatter-plots-container", "children"),
    Output("scatter-plots-store", "data"),
    [Input("heatmap", "clickData"),
     Input({'type': 'scatter', 'index': ALL}, "selectedData")],
    State("scatter-plots-container", "children"),
    State("scatter-plots-store", "data")
)
def update_scatter_plots_and_selection(clickData, selectedDataList, current_children, current_ids):
    ctx = callback_context

    if not ctx.triggered:
        raise PreventUpdate

    triggered_id = ctx.triggered[0]['prop_id']

    if 'heatmap.clickData' in triggered_id:
        if clickData is None:
            raise PreventUpdate

        x_col = clickData['points'][0]['x']
        y_col = clickData['points'][0]['y']
        scatter_id = f"scatter-{x_col}-{y_col}"
        
        if scatter_id not in current_ids:
            new_graph = dcc.Graph(
                id={'type': 'scatter', 'index': scatter_id},
                figure=create_scatter_plot(x_col, y_col),
                config={"displayModeBar": False},
                style={"display": "inline-block", "width": "400px", "height": "300px"},
            )
            current_children.append(new_graph)
            current_ids.append(scatter_id)
    else:
        selectedpoints = df.index
        for selected_data in selectedDataList:
            if selected_data and selected_data["points"]:
                selectedpoints = np.intersect1d(
                    selectedpoints, [p["customdata"] for p in selected_data["points"]]
                )

        updated_children = []
        for child in current_children:
            if isinstance(child, dict) and "props" in child and "figure" in child["props"]:
                graph_id = child["props"]["id"]["index"]
                x_col, y_col = graph_id.split("-")[1:3]
                fig = create_scatter_plot(x_col, y_col, selectedpoints)
                child["props"]["figure"] = fig
            updated_children.append(child)
        current_children = updated_children

    return current_children, current_ids

@app.callback(
    Output("heatmap", "figure"),
    Input("heatmap", "selectedData")
)
def update_heatmap(selectedData):
    return create_heatmap()

if __name__ == "__main__":
    app.run_server(debug=True)
