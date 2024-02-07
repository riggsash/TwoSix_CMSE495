import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import json

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
        dcc.Textarea(
        id='text-input',
        value=sentences[current_sentence_index],
        style={'width': '100%', 'height': 200},
    ),
    html.Button('Increase', id='increase-btn', n_clicks=0),
    html.Button('Decrease', id='decrease-btn', n_clicks=0),
    html.Button('Save Relation', id='save-btn', n_clicks=0),
    html.Button('Reset', id='reset-btn', n_clicks=0),
    html.Button('Next', id='next-btn', n_clicks=0),
    dcc.Store(id='memory-store', storage_type='local'),
    ])
])

@app.callback(
    [Output('text-input', 'value'),
     Output('memory-store', 'data')],
    [Input('next-btn', 'n_clicks')],
    [State('text-input', 'value'),
     State('memory-store', 'data')]
)
def next_sentence(n_clicks, current_text, stored_data):
    current_sentence_index = int(n_clicks)
    if current_sentence_index < len(sentences):
        return sentences[current_sentence_index], stored_data
    else:
        return current_text, stored_data

# Similar callbacks for increase, decrease, save, reset, etc.

if __name__ == '__main__':
    app.run_server(debug=True)
