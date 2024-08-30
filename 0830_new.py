import pandas as pd
import numpy as np
import plotly.graph_objs as go
from dash import Dash, dcc, html, Input, Output, State, callback_context
from dash.dependencies import ALL
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
        dcc.Graph(id="scatter-plot")
    ], className="six columns"),
    html.Div([
        dcc.Graph(id="selected-data-plot")
    ], className="twelve columns"),
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
    Output("scatter-plot", "figure"),
    Input("heatmap", "selectedData")
)
def update_scatter(selectedData):
    if not selectedData:
        raise PreventUpdate
    
    x_col = selectedData['points'][0]['x']
    y_col = selectedData['points'][0]['y']
    
    fig = go.Figure()
    
    for vth_type in ['VTH_W', 'VTH_E']:
        for level in long_df['Level'].unique():
            df_filtered = long_df[(long_df['Type'] == vth_type) & (long_df['Level'] == level)]
            fig.add_trace(go.Scatter(
                x=df_filtered['Vg'],
                y=df_filtered[x_col] if x_col in df_filtered.columns else df_filtered['VTH'],
                mode='markers',
                name=f'{vth_type} - Level {level}',
                marker=dict(size=8)
            ))
    
    fig.update_layout(
        title=f"{x_col} vs {y_col}",
        xaxis_title="Vg",
        yaxis_title=x_col,
        height=600
    )
    return fig

@app.callback(
    Output("selected-data-store", "data"),
    Input("scatter-plot", "selectedData")
)
def store_selected_data(selectedData):
    if not selectedData:
        raise PreventUpdate
    return selectedData

@app.callback(
    Output("selected-data-plot", "figure"),
    Input("selected-data-store", "data")
)
def update_selected_data_plot(selectedData):
    if not selectedData:
        raise PreventUpdate
    
    fig = go.Figure()
    
    for point in selectedData['points']:
        vth_type, vg, level = parse_column_name(point['curveNumber'])
        
        # Plot selected points from total_result.csv
        fig.add_trace(go.Scatter(
            x=[vg],
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
