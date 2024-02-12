import dash
from dash import dcc, html, ctx
from dash.dependencies import Input, Output, State
import json
import base64
from dash_selectable import DashSelectable
import io
from striprtf.striprtf import rtf_to_text
"""
Functionality ideas:
- Could write "helper" functions for callbacks to increase readability of callbacks

Functionality to be added:
- Ability to read in files and be added to sentences for data labeling (Look at: Dash upload component)
-- Ability to read metadata off of said files and assign them to a new dcc.Store so it can be added to every sentence's metadata

Functionality to be updated:
- (Not Required) Being able to choose the file name for the download
-- Currently cannot override previous downloaded files, will save as test.json, then the next as test(1).json

Errors in Functionality:
- (Not tested, but theorized) Final sentence data is currently unsavable as "save relation" only saves to current sentence,
and not to all-relation-store
-- Can be fixed by changing the case where n_clicks># of sentences in function next_sentence()

"""


app = dash.Dash(__name__)

#sentences = [
#    "The wind farms in the Gulf of Mexico create new fishing zones.",
#    "Other perceived impacts of the BIWF included the negative effects of sound and increased turbidity during construction and an increase in cod in the area.",
#    "The curious cat explored the mysterious backyard at night."
#]

relation = {"text": "", "casual_relations": [], "meta_data": {"title": "", "authors": "", "year": -1}}

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
        dcc.Upload(
            id='upload-data',
            children=html.Div([
                html.A('Select Files')
        ]),),
        html.Button('Saved', id='saved-btn', n_clicks=0),
        html.Button('Download JSON', id='download-btn', n_clicks=0),
        html.Br(),
        html.Div(id='stored-data'),
        html.Br(),
        html.Div(id="output-data-upload"),
        dcc.Store(id='input-sentences',data=[
            "The wind farms in the Gulf of Mexico create new fishing zones.",
            "Other perceived impacts of the BIWF included the negative effects of sound and increased turbidity during construction and an increase in cod in the area.",
            "The curious cat explored the mysterious backyard at night."],storage_type='memory'),
        dcc.Store(id='all-relation-store',data=[], storage_type='local'),
        dcc.Store(id='curr-sentence-store',data={"text": "",
                           "causal relations": [],
                           "meta_data": {"title": "", "authors": "", "year": ""}}, storage_type='local'),
        dcc.Store(id='current-relation-store',data={"src":"","tgt":"","direction":""},storage_type='local'),
        dcc.Download(id="download-json"),
    ])
])


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
     State('curr-sentence-store', 'data'),
     State('input-sentences','data'),],
     prevent_initial_call='initial_duplicate'
)
def next_sentence(n_clicks, current_text, all_data,curr_relation,curr_sen_data,sentences):
    current_sentence_index = int(n_clicks)
    if current_sentence_index == 0:
        all_data = [] #CHANGE LATER, THIS FORCES DATA DELETE ON REFRESH
        curr_sen_data["text"] = sentences[current_sentence_index]
        return all_data, sentences[current_sentence_index], curr_sen_data, curr_relation
    elif current_sentence_index < len(sentences):
        if curr_relation["src"] == '' or curr_relation["tgt"] == '':
            if not len(curr_sen_data["causal relations"]):
                curr_sen_data["causal relations"].append(curr_relation)
        else:
            if len(curr_sen_data["causal relations"]):
                if curr_sen_data["causal relations"][-1] != curr_relation:
                    #why does this if error
                    curr_sen_data["causal relations"].append(curr_relation)
            else:
                curr_sen_data["causal relations"].append(curr_relation)
        all_data.append(curr_sen_data)
        curr_sen_data = {"text": sentences[current_sentence_index],
                           "causal relations": [],
                           "meta_data": {"title": "", "authors": "", "year": ""}}
        curr_relation = {'src':"",'tgt':'','direction':''}
        return all_data,sentences[current_sentence_index], curr_sen_data, curr_relation
    else:
        return all_data, current_text, curr_sen_data, curr_relation

#Callback for increase, decrease, source,target, save, and reset in the following

@app.callback(
    [Output('my-direction','children'),
     Output('my-source','children'),
     Output('my-target','children'),
     Output("current-relation-store", "data")],
    [Input('increase-btn', 'n_clicks'),
     Input('decrease-btn', 'n_clicks'),
     Input('source-btn', 'n_clicks'),
     Input('target-btn', 'n_clicks'),
     Input('next-btn', 'n_clicks'),
     Input('reset-btn', 'n_clicks')],
    [State("dash-selectable", "selectedValue"),
     State("current-relation-store", "data")],
)
def allLabel(inc,dec,src,tgt,next,reset,selected_data,relation):
    """
    Function that handles all relation button data
    :param inc: Increase button
    :param dec: Decrease button
    :param src: Source button
    :param tgt: Target button
    :param selected_data: User-selected data
    :param relation: Relation data storage
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
    elif button_id == "reset-btn":
        relation = {'src': "", 'tgt': '', 'direction': ''}
        return direcText, srcText, tgtText, relation
    else: #This else corresponds to initial call (program start) and when the next button is hit
        #Have not tried multiple changes to one output from one button, and it probably isn't a good idea, so don't change this
        return direcText,srcText,tgtText,relation



@app.callback(
    [Output('curr-sentence-store','data'),
     Output('current-relation-store','data',allow_duplicate=True)],
    [Input('save-btn', 'n_clicks')],
    [State('current-relation-store','data'),
     State('curr-sentence-store', 'data')],
     prevent_initial_call=True,
)
def save_relation(n_clicks,curr_relation,curr_sentence):
    if curr_relation["src"] is not None and curr_relation["tgt"] is not None:
        curr_sentence["causal relations"].append(curr_relation)
        return curr_sentence,curr_relation
    else:
        return dash.no_update,curr_relation



@app.callback(
    Output('stored-data','children'),
    [Input('saved-btn', 'n_clicks')],
    State('input-sentences','data'),
)
def currentStorage(n_clicks,data):
    if not data:
        return f"Stored: []"
    return f"Stored: {data}" + f" Length: {len(data)}" + f" Test: {data[1]}"


@app.callback(
    Output("download-json", "data"),
    Input("download-btn", "n_clicks"),
    State('all-relation-store','data'),
    prevent_initial_call=True,
)
def download(n_clicks,data):
    fileData = json.dumps(data,indent=2)
    return dict(content=fileData,filename="test.json")

@app.callback([Output('output-data-upload', 'children'),
               Output('input-sentences', 'data'),],
              Input('upload-data', 'contents'),
              [State('upload-data', 'filename'),
               State('input-sentences','data')],
              prevent_initial_callback=True,
)

def update_output(list_of_contents, list_of_names,inp_sentences):
    if list_of_contents is None:
        return dash.no_update
    content_type, content_string = list_of_contents.split(',')
    decoded = base64.b64decode(content_string)
    if ".rtf" in list_of_names:
        temp = io.StringIO(decoded.decode('utf-8')).getvalue()
        text = rtf_to_text(temp)
        sentences = text.split(".")
        for sentence in sentences:
            inp_sentences.append(sentence)
    return text,inp_sentences



if __name__ == '__main__':
    app.run_server(debug=True)
