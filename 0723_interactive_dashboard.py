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

columns = [f"VTHE_{i}" for i in range(10, 28)] + [f"VTHW_{i}" for i in range(10, 28)]

df = pd.DataFrame(np.random.rand(30, len(columns)), columns=columns)


# ヒートマップを作成するためのデータフレーム

heatmap_df = df.corr()


def wide_to_long(df):

    long_df = pd.DataFrame()

    for col in df.columns:

        parts = col.split('_')

        vth_type = parts[0]

        vg = float(parts[1])

        temp_df = pd.DataFrame({

            "VTH": df[col],

            "Vg": vg,

            "Type": vth_type

        })

        long_df = pd.concat([long_df, temp_df])

    return long_df.reset_index(drop=True)


long_df = wide_to_long(df)


# measured_data.csvとtotal_result.csvを読み込み

measured_df = pd.read_csv("measured_data.csv")

total_df = pd.read_csv("total_result.csv")


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

        dcc.Store(id='scatter-plots-store', data=[]),  # 散布図のIDを保持するためのストア

        html.Button("Generate VTH vs Vg Graph", id="generate-graph", n_clicks=0),

        dcc.Graph(id="vth-vs-vg-graph", style={"display": "none"}),

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

                config={"displayModeBar": True},

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


@app.callback(

    Output("vth-vs-vg-graph", "figure"),

    Output("vth-vs-vg-graph", "style"),

    Input("generate-graph", "n_clicks"),

    State({'type': 'scatter', 'index': ALL}, "selectedData"),

)

def generate_vth_vs_vg_graph(n_clicks, selectedDataList):

    if n_clicks == 0:

        raise PreventUpdate

    

    selectedpoints = df.index

    for selected_data in selectedDataList:

        if selected_data and selected_data["points"]:

            selectedpoints = np.intersect1d(

                selectedpoints, [p["customdata"] for p in selected_data["points"]]

            )


    selected_df = df.loc[selectedpoints]

    

    if selected_df.empty:

        raise PreventUpdate


    long_selected_df = wide_to_long(selected_df)

    

    fig = px.scatter(long_selected_df, x="Vg", y="VTH", color="Type", symbol="Type")

    fig.update_traces(mode='lines+markers')

    

    # Add measured data as circles

    fig.add_trace(go.Scatter(x=measured_df["Vg"], y=measured_df["VTH"],

                             mode='markers',

                             marker=dict(symbol='circle', size=10, color='red'),

                             name='Measured Data'))

    

    # Add total result data as lines

    for vth_type in total_df["Type"].unique():

        filtered_df = total_df[total_df["Type"] == vth_type]

        fig.add_trace(go.Scatter(x=filtered_df["Vg"], y=filtered_df["VTH"],

                                 mode='lines',

                                 name=f'Total Result {vth_type}'))


    fig.update_layout(

        title="VTH vs Vg",

        xaxis_title="Vg (V)",

        yaxis_title="VTH",

    )

    

    return fig, {"display": "block"}


if __name__ == "__main__":

    app.run_server(debug=True)

