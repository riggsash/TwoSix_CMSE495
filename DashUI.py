import dash
from dash import dcc, html, ctx, dash_table, callback
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import json
import base64
from dash_selectable import DashSelectable
import io
from striprtf.striprtf import rtf_to_text
from datetime import date
"""
Functionality ideas:
- Could write "helper" functions for callbacks to increase readability of callbacks

Functionality to be added:
- Ability to read in files (besides RTF) and be added to sentences for data labeling (Look at: Dash upload component)

Functionality to be updated:
- (Not Required) Being able to choose the file name for the download

Unexpected (or frustrating) Behavior:
- Clicking anywhere on the same "y" as the upload button opens the file menu
- After saving a json, the input sentences are removed and the program is basically reset
-- However, even though it is reset, you cannot upload the same file consecutively.
-- You CAN upload 1 paper, then upload a second paper, and they will combine in the storage.
--- This problem likely occurs based on how dash is handling uploads, and may not be fixable. 
--- Also, this issue may not be relevant as why would you upload the same thing multiple times consecutively.
--- This issue is probably due to the filename not changing within the app, thus not invoking the callback.
Errors in Functionality:
- When modifying a sentence, for some reason it is not inversing the relations that it is copying, however
- the text is still modifyable, as is the relations in the dataframe, so it is still "functional"
-- This may be due to how the datatable is updating the JSON currently but modify does not change what the current
-- sentence is looking at, so the datatable should not be affecting it.
--- FIXED THIS ISSUE - created a copy of dict by using dict() to not alter original, edited text modifiers to all lowercase
"""

metadata_prompt = html.Div(hidden=True,children=[
    html.P(id="metadata-prompt-text",title="Please enter the following metadata."),
    html.Div([
        dcc.Input(id='title', value='Title', type='text'),
        dcc.Input(id='author', value='Author(s)', type='text'),
        dcc.Input(id='year', value='Year', type='text'),
    ]),
    html.Br(),
    html.Button("Finished",id='metadata-finish-button'),
])

inverse_in = html.Div(id="inverse-div", hidden=True,children=[
    dcc.Input(id='inverse-in', value='text', type='text')
])

app = dash.Dash(__name__)

app.layout = html.Div([
    html.Div([
        metadata_prompt,
        inverse_in,
        DashSelectable(
            id="dash-selectable",
            children=[html.P(id="sentence"), html.P(id="output")],
        ),
        html.Br(),
        html.Button('Source', id='source-btn', n_clicks=0),
        html.Button('Target', id='target-btn', n_clicks=0),
        html.Br(),
        html.Button('Increase', id='increase-btn', n_clicks=0),
        html.Button('Decrease', id='decrease-btn', n_clicks=0),
        html.Br(),
        html.Div(id='my-source'),

        html.Div(id='my-target'),

        html.Div(id='my-direction'),
        html.Br(),
        html.Button('Save Relation', id='save-btn', n_clicks=0),
        html.Button('Reset', id='reset-btn', n_clicks=0),
        html.Br(),
        dash_table.DataTable(id="datatable-current",
                             style_cell={
                                 'height': 'auto',
                                 # all three widths are needed
                                 'minWidth': '180px', 'width': '180px', 'maxWidth': '180px',
                                 'whiteSpace': 'normal'
                             },
                             columns=[{
                                'name': 'src',
                                'id': "1"
                             },
                                {
                                    'name': 'tgt',
                                    'id': "2"
                                },
                                {
                                     'name': 'direction',
                                     'id': "3"
                                }
                             ],
                             data=[],
                             editable=True,
                             row_deletable=True,
                             ),
        html.Br(),
        html.Button('Back', id='back-btn', n_clicks=0),
        html.Button('Next', id='next-btn', n_clicks=0),
        html.Br(),
        html.Div(id="prev-data"),
        html.Div(id="next-data"),
        html.Br(),
        html.Br(),
        html.Button('Discard Current Sentence', id="discard-btn"),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Button('Modify and add new sentence', id="inverse-btn"),
        html.Br(),
        html.Br(),
        dcc.Upload(
            id='upload-data',
            children=html.Div([
                html.Button('Select Files')
        ]),),
        html.Button('Download JSON', id='download-btn', n_clicks=0),
        html.Br(),
        html.Br(),
        html.Div(id="output-data-upload"),
        dcc.Store(id='input-sentences', data=["Please Insert RTF or JSON File"], storage_type='local'),

        dcc.Store(id='all-relation-store', data=[], storage_type='local'),
        # CHANGE BACK TO SESSION OR LOCAL FOR RESEARCHER RELEASE

        dcc.Store(id='current-relation-store',data={"src":"","tgt":"","direction":""},storage_type='memory'),
        dcc.Store(id='meta-data',data={"title": "", "authors": "", "year": ""},storage_type='memory'),
        dcc.Store(id='llm-metrics',data=[], storage_type='memory'),
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
     Output('current-relation-store', 'data',allow_duplicate=True),
     Output('next-btn', 'n_clicks',allow_duplicate=True),
     Output('back-btn', 'n_clicks',allow_duplicate=True)],
    [Input('next-btn', 'n_clicks'),
     Input('back-btn', 'n_clicks')],
    [State('sentence', 'children'),
     State('all-relation-store', 'data'),
     State('current-relation-store', 'data'),
     State('input-sentences','data'),],
    prevent_initial_call='initial_duplicate',
)
def next_sentence(n_clicks, back_clicks, current_text, all_data,curr_relation,sentences):
    current_sentence_index = int(n_clicks) - int(back_clicks)
    button_id = ctx.triggered_id if not None else False
    if len(sentences) == 1:  # Prevents moving the amount of clicks, and thus the index of sentences
        # , when there is no file [On start, and after download]
        return all_data, "Please Insert RTF File", curr_relation, 0, 0
    if current_sentence_index < 0: # if we've gone negative, we can just reset the clicks and return default sentence
        return all_data, "Please Insert RTF File", curr_relation, 0, 0
    if current_sentence_index == 0:
        return all_data, sentences[current_sentence_index], curr_relation, 0, 0
    elif current_sentence_index == 1:
        return all_data, all_data[current_sentence_index-1]["text"], curr_relation, n_clicks, back_clicks
    elif current_sentence_index < len(sentences):
        # Handling case where current relation is not filled out enough to be usable
        if button_id == "back-btn":
            index = current_sentence_index
        else:
            index = current_sentence_index - 2  # -1 because of starter sentence,-1 again because next button makes index + 1
            # of where we are saving, so -2
        all_data = saving_relation(index,all_data,curr_relation)
        curr_relation = {'src':"",'tgt':'','direction':''}
        return all_data, all_data[current_sentence_index-1]["text"], curr_relation, n_clicks, back_clicks
    elif all_data[-1]["text"] == current_text:
        # This case is hit when the user hits the final sentence of a paper, and hits next 1 additional time
        # This makes sure that the last sentence is saved.
        # The following code in this elif could be made into a function as it is now repeated.
        all_data = saving_relation(-1,all_data,curr_relation)
        curr_relation = {'src': "", 'tgt': '', 'direction': ''}
        if button_id == "back_btn":
            return all_data, all_data[-2]["text"], curr_relation, n_clicks, back_clicks
        else:
            return all_data, all_data[-1]["text"], curr_relation, n_clicks-1, back_clicks
    else:
        return all_data, current_text, curr_relation, n_clicks, back_clicks

# Callback for increase, decrease, source,target, save, and reset in the following


@app.callback(
    [Output('my-direction', 'children'),
     Output('my-source', 'children'),
     Output('my-target', 'children'),
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
def allLabel(inc, dec, src, tgt, next, reset, selected_data, relation):
    """
    Function that handles all relation button data
    :param inc: Increase button
    :param dec: Decrease button
    :param src: Source button
    :param tgt: Target button
    :param next: Next button - allows next button to access function
    :param reset: Reset button - allows reset button to access function
    :param selected_data: User-selected data
    :param relation: Relation data storage
    :return: [Direction text, ]
    """
    button_id = ctx.triggered_id if not None else False
    direcText = f"Direction: "
    srcText = f"Source: "
    tgtText = f"Target: "
    if button_id == "increase-btn":
        relation["direction"] = "Increase"
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
    else:  # This else corresponds to initial call (program start) and when the next button is hit
        # Have not tried multiple changes to one output from one button,
        # and it probably isn't a good idea, so don't change this
        return direcText,srcText,tgtText,relation


@app.callback(
    [Output('all-relation-store','data',allow_duplicate=True),
     Output('current-relation-store','data',allow_duplicate=True)],
    [Input('save-btn', 'n_clicks')],
    [State('current-relation-store','data'),
     State('all-relation-store', 'data'),
     State('next-btn', 'n_clicks'),
     State('back-btn', 'n_clicks')],
    prevent_initial_call=True,
)
def save_relation(n_clicks,curr_relation,all_data,for_index,back_index):
    index = int(for_index)-int(back_index)
    if index <= 0:
        return all_data,dash.no_update
    all_data = saving_relation(index-1,all_data,curr_relation)
    return all_data,dash.no_update


def saving_relation(index,all_data,curr_relation):
    if curr_relation["src"] == '' or curr_relation["tgt"] == '':
        pass
    else:
        if len(all_data[index]["causal relations"]):
            check = False
            for relation in all_data[index]["causal relations"]:
                if relation == curr_relation:
                    check = True
            if not check:  # checking if it's a duplicate
                all_data[index]["causal relations"].append(curr_relation)
        else:
            all_data[index]["causal relations"].append(curr_relation)
    return all_data


@callback(
    [Output('datatable-current', 'data'),
     Output('next-data', 'children'),
     Output('prev-data', 'children')],
    Input('all-relation-store', 'data'),
    [State('next-btn', 'n_clicks'),
     State('back-btn', 'n_clicks'),
     State('datatable-current', 'data'),
     State('datatable-current', 'columns')]
)
def currentStorage(data, for_index, back_index, rows,columns):
    if not data:  # If there is no input file
        return dash.no_update, dash.no_update, dash.no_update
    index = int(for_index)-int(back_index)
    if index <= 0:  # If we're at the starter sentence
        return dash.no_update, dash.no_update, dash.no_update
    elif index == 1:  # If at first sentence of paper, there is no previous sentence
        rows = []
        for relation in data[index-1]['causal relations']:
            rows.append({c['id']: relation[val] for c, val in zip(columns,relation)})
        return rows, f"Next Sentence: {data[index]}", "Previous Sentence: []"
    elif index == len(data):  # If we're at EOF, there is no next sentence
        rows = []
        for relation in data[index - 1]['causal relations']:
            rows.append({c['id']: relation[val] for c, val in zip(columns, relation)})
        return rows, f"Next Sentence: []", f"Previous Sentence: {data[index - 2]}"
    rows = []
    for relation in data[index - 1]['causal relations']:
        rows.append({c['id']: relation[val] for c, val in zip(columns, relation)})
    return rows, f"Next Sentence: {data[index]}", f"Previous Sentence: {data[index - 2]}"


@app.callback(
    Output('all-relation-store', 'data', allow_duplicate=True),
    Input('datatable-current', 'data'),
    [State('all-relation-store', 'data'),
     State('next-btn', 'n_clicks'),
     State('back-btn', 'n_clicks'),],
    prevent_initial_call=True
)
def updating_json(rows,data,next_index,back_index):
    """
    This function updates the JSON after the editable dash datatable has been changed.
    :param value:
    :return:
    """
    index = int(next_index)-int(back_index)
    conv = []
    for row, i in zip(rows,range(len(rows))):  # row is a singular relation
        temp = {}
        temp["src"] = row["1"]
        temp["tgt"] = row["2"]
        temp["direction"] = row["3"]
        if temp["direction"] == "+":
            temp["direction"] = 'increase'
        if temp["direction"] == "-":
            temp["direction"] = 'decrease'
        if temp["direction"] != "increase" and temp["direction"] != "decrease":
            temp["direction"] = data[index-1]['causal relations'][i]['direction']
        if temp["src"] == "" or temp["tgt"] == "" or temp["direction"] == "": #  if any parameters are empty, lose the relation
            continue
        conv.append(temp)

    data[index-1]['causal relations'] = conv
    return data

@app.callback(
    [Output("download-json", "data"),
     Output('all-relation-store','data'),
     Output('input-sentences','data', allow_duplicate=True),
     Output('next-btn','n_clicks'),
     ],
    Input("download-btn", "n_clicks"),
    [State('all-relation-store','data'),
     State('next-btn','n_clicks'),
     State('input-sentences','data'),
     State('upload-data', 'filename')],
    prevent_initial_call=True,
)
def download(n_clicks,data,curr_sen_index, inp_sentences,file):
    # In current implementation, only required variables are the input (download-btn)
    # and the state of all-relation-store
    """

    :param n_clicks:
    :param data:
    :param curr_sen_index:
    :param inp_sentences:
    :return: json, relational storage, input_sentences, next btn n_clicks
    """
    # WHEN YOU HIT SAVE, YOU ARE DONE WITH THAT SESSION, ALL REMAINING SENTENCES ARE REMOVED, AND THE PROGRAM IS
    # BASICALLY RESET
    if not data:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update
    fileData = json.dumps(data, indent=2)
    today = date.today()
    if file is None:
        return dict(content=fileData, filename=f"Labeled_Data-{today}.json"), [], ["Please Insert RTF File"], 0
    file = file.replace(".rtf",f"-{today}.json")
    return dict(content=fileData, filename=file), [], ["Please Insert RTF File"], 0


# This callback also activates on download, and updates the text on screen.


@app.callback(
    Output('output-data-upload', 'children', allow_duplicate=True),
    Input('input-sentences','data'),
    prevent_initial_call='initial_duplicate',
)
def refresh(inp_sentences):
    return f"Current Sentences: {inp_sentences}" + f" Length: {len(inp_sentences)}"


def abbreviation_handler(sentences):
    # File handler helper function
    sentences_to_add = []
    temp = sentences[0]
    for i in range(len(sentences) - 1):
        if sentences[i] == '':
            continue
        if not (sentences[i + 1].strip())[0].isupper():
            temp = temp + '. ' + sentences[i + 1]
        else:
            sentences_to_add.append(temp)
            temp = sentences[i + 1]
    sentences_to_add.append(temp)
    return sentences_to_add


@app.callback([Output('input-sentences','data'),
               Output('all-relation-store','data', allow_duplicate=True),
               Output(metadata_prompt,'hidden'),
               Output('llm-metrics','data')],
              Input('upload-data', 'contents'),
              [State('upload-data', 'filename'),
               State('input-sentences','data'),
               State('all-relation-store','data')],
              prevent_initial_call="initial_duplicate"
)
def upload(list_of_contents, list_of_names,inp_sentences,data):
    if list_of_contents is None:
        if len(inp_sentences) > 1:
            return inp_sentences, dash.no_update, dash.no_update, dash.no_update
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update
    content_type, content_string = list_of_contents.split(',')
    decoded = base64.b64decode(content_string)
    if ".json" in list_of_names:
        data = json.loads(decoded)
        for sentence in data:
            inp_sentences.append(sentence["text"])
        if 'LLM' in data[0].keys():
            LLM_scores = {}
            LLM_metrics = {}
            for LLM in data[0]['LLM']:
                LLM_scores[LLM] = {"TP":0, "FP":0, "TN":0, "FN": 0}
                LLM_metrics[LLM] = {}
            for sentence in data:
                for LLM in sentence['LLM'].keys():  # LLM is a list of relations
                    for relation in sentence['causal relations']:
                        if relation not in sentence['LLM'][LLM]:
                            LLM_scores[LLM]['FN'] += 1
                        else:
                            LLM_scores[LLM]['TP'] += 1
                    if len(LLM) == 0:
                        if len(sentence['causal relations']) == 0:
                            LLM_scores[LLM]['TN'] += 1
                    for relation in LLM:
                        if relation not in sentence['causal relations']:
                            LLM_scores[LLM]['FP'] += 1
                        # Don't need an else here, as that'd be a true positive and is already added
            for LLM in LLM_scores:
                LLM_metrics[LLM]['precision'] = LLM_scores[LLM]['TP'] / (LLM_scores[LLM]['TP'] + LLM_scores[LLM]['FP'])
                LLM_metrics[LLM]['recall'] = LLM_scores[LLM]['TP'] / (LLM_scores[LLM]['TP'] + LLM_scores[LLM]['FN'])
                LLM_metrics[LLM]['F1'] = (2 * LLM_metrics[LLM]['precision'] * LLM_metrics[LLM]['recall']) / (LLM_metrics[LLM]['precision'] + LLM_metrics[LLM]['recall'])
                LLM_metrics[LLM]['accuracy'] = ((LLM_scores[LLM]['TP'] + LLM_scores[LLM]['TN']) /
                                                (LLM_scores[LLM]['TP'] + LLM_scores[LLM]['TN'] + LLM_scores[LLM]['FP'] + LLM_scores[LLM]['FN']))
            return inp_sentences, data, dash.no_update, dash.no_update
        return inp_sentences, data, dash.no_update, dash.no_update
    if ".rtf" in list_of_names:
        temp = io.StringIO(decoded.decode('utf-8')).getvalue()
        text = rtf_to_text(temp)
        period_split = text.split(". ")
        sentences = []
        for sentence in period_split:
            temp = sentence.split(".\n")
            if type(temp) is str:
                sentences.append(sentence)
            else:
                for sen in temp:
                    if sen == "":
                        continue
                    sentences.append(sen)
        sentences = abbreviation_handler(sentences)
        for sentence in sentences:
            if sentence == '':
                continue
            sentence = sentence.replace("\n", "")
            sentence = sentence + "."
            inp_sentences.append(sentence)
            template = {"text": sentence,
                        "causal relations": [],
                        "meta_data": {"title": "", "authors": "", "year": ""}}
            data.append(template)

    return inp_sentences, data, False, dash.no_update


@app.callback([Output(metadata_prompt,'hidden',allow_duplicate=True),
               Output('all-relation-store','data', allow_duplicate=True)],
              Input('metadata-finish-button', 'n_clicks'),
              [State('title', 'value'),
               State('author','value'),
               State('year','value'),
               State('all-relation-store','data'),],
              prevent_initial_call="initial_duplicate"
)
def metadata(n_clicks, title, author, year, data):
    meta_dict = {"title": title, "authors": author, "year": year}
    for i in range(len(data)):
        if data[i]["meta_data"] == {"title": "", "authors": "", "year": ""}:
            data[i]["meta_data"] = meta_dict
    return True, data


@app.callback([
               Output("inverse-div",'hidden',allow_duplicate=True),
               Output('all-relation-store','data', allow_duplicate=True),
               Output('sentence','children', allow_duplicate=True),
               Output('input-sentences','data', allow_duplicate=True)],
              Input('inverse-btn', 'n_clicks'),
              [State("inverse-div",'hidden'),
               State('sentence','children'),
               State('all-relation-store','data'),
               State('next-btn', 'n_clicks'),
               State('back-btn', 'n_clicks'),
               State('inverse-in', 'value'),
               State('input-sentences', 'data')],
              prevent_initial_call=True
)
def modify(n_clicks, editable, sen, data,for_index,back_index,input_val,sentence_list):
    index = int(for_index)-int(back_index)
    if editable:

        return False, dash.no_update, dash.no_update, dash.no_update
    else:
        relations = []
        for relation in data[index-1]["causal relations"]:  # -1 because data does not have starter sentence
            temp = dict(relation)
            if temp["direction"] == "increase":
                temp["direction"] = "decrease"
            else:
                temp["direction"] = "increase"
            relations.append(temp)
        template = {"text": input_val,
                    "causal relations": relations,
                    "meta_data": data[index]["meta_data"]}
        data.insert(index, template)
        sentence_list.insert(index+1, input_val)
        return True, data, dash.no_update,sentence_list


@app.callback([
               Output('sentence','children', allow_duplicate=True),
               Output('inverse-in', 'value',allow_duplicate=True),],
              Input('inverse-div', 'hidden'),
              [State('sentence','children'),
               ],
              prevent_initial_call=True
)
def inverse_pt2(hidden,sen):
    return sen, sen


@app.callback([
               Output('input-sentences','data', allow_duplicate=True),
               Output('all-relation-store','data',allow_duplicate=True),
               Output('next-btn', 'n_clicks',allow_duplicate=True),
               Output('sentence', 'children',allow_duplicate=True),],
              Input('discard-btn', 'n_clicks'),
              [State('input-sentences','data'),
               State('all-relation-store','data'),
               State('next-btn', 'n_clicks'),
               State('back-btn', 'n_clicks')
               ],
              prevent_initial_call=True
)
def discard(n_clicks,sentence_storage,data,for_index,back_index):
    if len(sentence_storage) == 1:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update
    index = int(for_index)-int(back_index)
    if index == 0:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update
    if index == len(sentence_storage):
        for_index -= 1
    sentence_storage.pop(index)
    data.pop(index-1)
    if index == len(sentence_storage):
        return sentence_storage,data, for_index-1, dash.no_update
    return sentence_storage,data, dash.no_update, sentence_storage[index]


if __name__ == '__main__':
    app.run_server(debug=True)
