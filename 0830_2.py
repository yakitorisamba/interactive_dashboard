import pandas as pd
import numpy as np
import plotly.graph_objs as go
from dash import Dash, dcc, html, Input, Output, State, callback_context
from dash.exceptions import PreventUpdate

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
app = Dash(__name__, external_stylesheets=external_stylesheets)
app.config.suppress_callback_exceptions = True

# Load real data
total_df = pd.read_csv("total_result.csv")
measured_df = pd.read_csv("measured_data.csv")

# Create heatmap data
heatmap_df = total_df.corr()

def parse_column_name(col):
    parts = col.split('_')
    vth_type = parts[0]
    vg = float(parts[1].split('.')[0])
    level = int(parts[1].split('.')[1])
    return vth_type, vg, level

def create_long_df(df):
    data = []
    for col in df.columns:
        if col.startswith('VTH'):
            vth_type, vg, level = parse_column_name(col)
            data.append({
                'VTH': df[col],
                'Vg': vg,
                'Type': vth_type,
                'Level': level
            })
    return pd.DataFrame(data)

long_df = create_long_df(total_df)

app.layout = html.Div([
    html.Div([
        dcc.Graph(id="heatmap", config={"displayModeBar": False}),
    ], className="six columns"),
    html.Div([
        html.Div(id="scatter-plots-container")
    ], className="six columns"),
    html.Div([
        dcc.Graph(id="selected-data-plot")
    ], className="twelve columns"),
    dcc.Store(id='scatter-plots-store', data=[]),
    dcc.Store(id='selected-data-store'),
])

@app.callback(
    Output("heatmap", "figure"),
    Input("heatmap", "id")
)
def update_heatmap(_):
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_df.values,
        x=heatmap_df.columns,
        y=heatmap_df.columns,
        colorscale="Viridis"
    ))
    fig.update_layout(
        title="Correlation Heatmap",
        xaxis_title="Parameters",
        yaxis_title="Parameters",
        height=600
    )
    return fig

@app.callback(
    [Output("scatter-plots-container", "children"),
     Output("scatter-plots-store", "data")],
    [Input("heatmap", "clickData")],
    [State("scatter-plots-store", "data")]
)
def update_scatter_plots(clickData, existing_plots):
    if not clickData:
        raise PreventUpdate
    
    existing_plots = existing_plots or []
    x_col = clickData['points'][0]['x']
    y_col = clickData['points'][0]['y']
    
    new_plot_id = f"scatter-plot-{len(existing_plots)}"
    existing_plots.append({"id": new_plot_id, "x": x_col, "y": y_col})
    
    new_plot = html.Div([
        dcc.Graph(id={"type": "scatter", "index": new_plot_id}),
    ])
    
    return [html.Div([new_plot] + [html.Div(id=plot['id']) for plot in existing_plots[:-1]]), existing_plots]

@app.callback(
    Output({"type": "scatter", "index": ALL}, "figure"),
    [Input("scatter-plots-store", "data")]
)
def update_scatter_figures(plots_data):
    if not plots_data:
        raise PreventUpdate
    
    figures = []
    for plot_data in plots_data:
        x_col = plot_data['x']
        y_col = plot_data['y']
        
        fig = go.Figure()
        
        for vth_type in ['VTH_W', 'VTH_E']:
            for level in long_df['Level'].unique():
                df_filtered = long_df[(long_df['Type'] == vth_type) & (long_df['Level'] == level)]
                fig.add_trace(go.Scatter(
                    x=df_filtered['Vg'],
                    y=df_filtered[y_col] if y_col in df_filtered.columns else df_filtered['VTH'],
                    mode='markers',
                    name=f'{vth_type} - Level {level}',
                    marker=dict(size=8)
                ))
        
        fig.update_layout(
            title=f"{x_col} vs {y_col}",
            xaxis_title="Vg",
            yaxis_title=y_col,
            height=400
        )
        figures.append(fig)
    
    return figures

@app.callback(
    Output("selected-data-store", "data"),
    [Input({"type": "scatter", "index": ALL}, "selectedData")]
)
def store_selected_data(selectedData):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    selected_points = []
    for points in selectedData:
        if points:
            selected_points.extend(points['points'])
    
    return selected_points

@app.callback(
    Output("selected-data-plot", "figure"),
    Input("selected-data-store", "data")
)
def update_selected_data_plot(selectedData):
    if not selectedData:
        raise PreventUpdate
    
    fig = go.Figure()
    
    for point in selectedData:
        vth_type, vg, level = parse_column_name(point['curveNumber'])
        
        # Plot selected points from total_result.csv
        fig.add_trace(go.Scatter(
            x=[point['x']],
            y=[point['y']],
            mode='markers',
            name=f'{vth_type} - Level {level} (Selected)',
            marker=dict(size=10, symbol='star')
        ))
        
        # Plot corresponding data from measured_data.csv
        measured_data = measured_df[(measured_df['Type'] == vth_type) & 
                                    (measured_df['Vg'] == vg) & 
                                    (measured_df['Level'] == level)]
        fig.add_trace(go.Scatter(
            x=measured_data['Vg'],
            y=measured_data['VTH'],
            mode='markers',
            name=f'{vth_type} - Level {level} (Measured)',
            marker=dict(size=8)
        ))
    
    fig.update_layout(
        title="Selected Data vs Measured Data",
        xaxis_title="Vg",
        yaxis_title="VTH",
        height=600
    )
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
