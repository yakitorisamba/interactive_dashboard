import dash
from dash import html
import dash_vtk
from vtk.util.numpy_support import vtk_to_numpy
import vtk

# VTPファイルを読み込む関数
def read_vtp(filename):
    reader = vtk.vtkXMLPolyDataReader()
    reader.SetFileName(filename)
    reader.Update()
    polydata = reader.GetOutput()
    
    # ポイントデータを取得
    points = vtk_to_numpy(polydata.GetPoints().GetData())
    
    # ポリゴンデータを取得
    polys = vtk_to_numpy(polydata.GetPolys().GetData())
    
    # ポイントデータの物理量を取得
    point_data = polydata.GetPointData()
    fields = {}
    for i in range(point_data.GetNumberOfArrays()):
        array = point_data.GetArray(i)
        name = point_data.GetArrayName(i)
        data = vtk_to_numpy(array)
        fields[name] = data
    
    return points, polys, fields

# VTPファイルを読み込む
filename = "hoge.vtp"  # ここに実際のファイル名を指定してください
points, polys, fields = read_vtp(filename)

# Dashアプリケーションを作成
app = dash.Dash(__name__)

# レイアウトを定義
app.layout = html.Div([
    dash_vtk.View([
        dash_vtk.GeometryRepresentation([
            dash_vtk.Mesh(
                state={
                    "mesh": {
                        "points": points,
                        "polys": polys,
                    },
                    "field": {
                        "location": "PointData",
                        "name": list(fields.keys())[0],  # 最初のフィールドを表示
                        "values": fields[list(fields.keys())[0]],
                        "numberOfComponents": 1,
                    },
                }
            )
        ]),
    ]),
    html.Div([
        html.Label("Select Field:"),
        html.Select(
            id='field-selector',
            options=[{'label': k, 'value': k} for k in fields.keys()],
            value=list(fields.keys())[0]
        )
    ])
])

# コールバックを定義してフィールドの選択を可能にする
@app.callback(
    dash.Output('vtk-view', 'children'),
    [dash.Input('field-selector', 'value')]
)
def update_field(selected_field):
    return [
        dash_vtk.GeometryRepresentation([
            dash_vtk.Mesh(
                state={
                    "mesh": {
                        "points": points,
                        "polys": polys,
                    },
                    "field": {
                        "location": "PointData",
                        "name": selected_field,
                        "values": fields[selected_field],
                        "numberOfComponents": 1,
                    },
                }
            )
        ])
    ]

if __name__ == '__main__':
    app.run_server(debug=True)
