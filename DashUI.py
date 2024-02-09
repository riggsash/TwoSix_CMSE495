import dash
from dash import dcc, html, ctx
from dash.dependencies import Input, Output, State
import json
from dash_selectable import DashSelectable

app = dash.Dash(__name__)

sentences = [
    "The wind farms in the Gulf of Mexico create new fishing zones.",
    "Other perceived impacts of the BIWF included the negative effects of sound and increased turbidity during construction and an increase in cod in the area.",
    "The curious cat explored the mysterious backyard at night."
]

labeled_sentences = []
relation = {"text": "", "casual_relations": [], "meta_data": {"title": "", "authors": "", "year": -1}}
current_sentence_index = 0

app.layout = html.Div([
    html.Div([
        DashSelectable(
            id="dash-selectable",
            children=[html.P(id="sentence"), html.P(id="output")],
        ),
        html.Br(),
        html.Button('Source', id='source-btn', n_clicks=0),
        html.Button('Target', id='target-btn', n_clicks=0),
        html.Br(),
        html.Div(id = 'my-source'),

        html.Div(id = 'my-target'),

        html.Div(id = 'my-direction'),
        html.Br(),
        html.Br(),
        html.Button('Increase', id='increase-btn', n_clicks=0),
        html.Button('Decrease', id='decrease-btn', n_clicks=0),
        html.Button('Save Relation', id='save-btn', n_clicks=0),
        html.Button('Reset', id='reset-btn', n_clicks=0),
        html.Button('Next', id='next-btn', n_clicks=0),
        html.Br(),
        html.Button('Saved', id='saved-btn', n_clicks=0),
        html.Button('Download JSON', id='download-btn', n_clicks=0),
        html.Br(),
        html.Div(id='stored-data'),
        dcc.Store(id='all-relation-store',data=[], storage_type='local'),
        dcc.Store(id='curr-sentence-store',data={"text": "",
                           "causal relations": [],
                           "meta_data": {"title": "", "authors": "", "year": ""}}, storage_type='local'),
        dcc.Store(id='current-relation-store',data={"src":"","tgt":"","direction":""},storage_type='local'),
        dcc.Download(id="download-json"),
    ])
])

#test
@app.callback(Output("output", "children"),
              [Input("dash-selectable", "selectedValue")])
def display_output(value):
    text = ""
    if value:
        text = value

    return "Currently selected: {}".format(text)



@app.callback(
    [Output('all-relation-store', 'data',allow_duplicate=True),
     Output('sentence','children'),
     Output('curr-sentence-store', 'data',allow_duplicate=True),
     Output('current-relation-store', 'data',allow_duplicate=True)],
    [Input('next-btn', 'n_clicks')],
    [State('sentence', 'children'),
     State('all-relation-store', 'data'),
     State('current-relation-store', 'data'),
     State('curr-sentence-store', 'data')],
     prevent_initial_call='initial_duplicate'
)
def next_sentence(n_clicks, current_text, all_data,curr_relation,curr_sen_data):
    current_sentence_index = int(n_clicks)
    if current_sentence_index == 0:
        all_data = [] #CHANGE LATER, THIS FORCES DATA DELETE ON REFRESH
        curr_sen_data["text"] = sentences[current_sentence_index]
        return all_data, sentences[current_sentence_index], curr_sen_data, curr_relation
    elif current_sentence_index < len(sentences):
        if curr_relation["src"] is None or curr_relation["tgt"] is None:
            pass
        else:
            curr_sen_data["causal relations"].append(curr_relation)
        all_data.append(curr_sen_data)
        curr_sen_data = {"text": sentences[current_sentence_index],
                           "causal relations": [],
                           "meta_data": {"title": "", "authors": "", "year": ""}}
        curr_relation = {}
        return all_data,sentences[current_sentence_index], curr_sen_data, curr_relation
    else:
        return all_data, current_text, curr_sen_data, curr_relation

# Similar callbacks for increase, decrease, save, reset, etc.

@app.callback(
    [Output('my-direction','children'),
     Output('my-source','children'),
     Output('my-target','children'),
     Output("current-relation-store", "data")],
    [Input('increase-btn', 'n_clicks'),
     Input('decrease-btn', 'n_clicks'),
     Input('source-btn', 'n_clicks'),
     Input('target-btn', 'n_clicks')],
    [State("dash-selectable", "selectedValue"),
     State("current-relation-store", "data")]
)

def allLabel(inc,dec,src,tgt,selected_data,relation):
    """
    Function to
    :param inc:
    :param dec:
    :param src:
    :param tgt:
    :param selected_data:
    :param relation:
    :return: [Direction text, ]
    """
    button_id = ctx.triggered_id if not None else False
    direcText = f"Direction: "
    srcText = f"Source: "
    tgtText = f"Target: "
    if button_id == "increase-btn":
        relation["direction"]="Increase"
        return f"Direction: Increase",dash.no_update, dash.no_update,relation
    elif button_id == "decrease-btn":
        relation["direction"] = "Decrease"
        return f"Direction: Decrease",dash.no_update, dash.no_update,relation
    elif button_id == "source-btn":
        relation["src"] = selected_data
        return dash.no_update, f"Source: {selected_data}", dash.no_update,relation
    elif button_id == "target-btn":
        relation["tgt"] = selected_data
        return dash.no_update, dash.no_update, f"Target: {selected_data}",relation
    else:
        return direcText,srcText,tgtText,relation
"""
@app.callback(
    Output('stored-data','children'),
    [Input('saved-btn', 'n_clicks')],
    State('current-relation-store','data')
)
"""


@app.callback(
    Output('stored-data','children'),
    [Input('saved-btn', 'n_clicks')],
    State('all-relation-store','data'),
)

def currentStorage(n_clicks,data):
    if not data:
        return f"Stored: []"
    return f"Stored: {data}"

@app.callback(
    Output("download-json", "data"),
    Input("download-btn", "n_clicks"),
    State('all-relation-store','data'),
    prevent_initial_call=True,
)
def download(n_clicks,data):
    fileData = json.dumps(data,indent=1)
    return dict(content=fileData,filename="test.json")


if __name__ == '__main__':
    app.run_server(debug=True)