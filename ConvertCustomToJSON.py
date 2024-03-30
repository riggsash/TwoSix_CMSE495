import json
import time
import random
import string
import numpy as np
import pandas as pd
import datasets
from datasets import Dataset, load_dataset
"""
This conversion file converts data that is not in JSON format to our main JSON format.
This should be used on some basis (weekly?) to convert any data that is from old or different labeling methods.
Given that these data files are NOT in a standard format, each file will probably have to have
 it's own function for conversion
which convert these files to the current labeled-data structure (our main JSON format).
This means that this conversion file is NOT designed to convert LLM outputs back to the main JSON format.
"""

f = open("C:/Users/milli/Downloads/OSW_labeled_data.json")
file = json.load(f)
ids = set()

def kuldeep_excel():
    # Almost all of this code was taken from Kuldeep's preparing_data.ipynb
    # Some of it was changed as his code goes straight for making it into suitable for Llama2
    df = pd.read_excel('/mnt/scratch/singhku2/llm_finetuning_data/[2023] Patel, Ronak -- Secondary literature data combined file_20220614.xlsx')
    df = df[
        [
            'ID', 'Author', 'Year', 'Title', 'Food System Focus', 'Causal claim',

            'Independent variable (original)', 'Direction (Independent)', 'Dependent variable (original)',

            'Independent variable (coded)', 'Dependent variable (coded)', 'Relationship',

            'Consolidation Term (Independent) new', 'Consolidation Term (Dependent) new'
        ]
    ]
    df.dropna(subset=['Independent variable (original)', 'Dependent variable (original)', 'Direction (Independent)'],
              inplace=True)
    df.to_csv('/llm_finetuning_data/filtered_ronak_patel_data.csv', index=False)

    list_of_outputs = []

    for idx in tqdm(df.sentence_id.unique().tolist()):
        temp_df = df[df.sentence_id == idx]
        temp_dict = {
            #  'sentence_id': idx,
            'text': temp_df['Causal claim'].to_list()[0],
            'causal relations': [],
            'meta_data': {'title':'', 'authors': '', "year": ''}
        }
        if not temp_df['Title'].to_list()[0].isna():
            temp_dict['meta_data']['title'] = temp_df['Title'].to_list()[0]
        if temp_df['Year'].to_list()[0] > 1000:  # Could probably change this to .isna() as well
            temp_dict['meta_data']['year'] = temp_df['Year'].to_list()[0]
        if not temp_df['Author'].to_list()[0].isna():
            temp_dict['meta_data']['author'] = temp_df['Author'].to_list()[0]

        for _, row in temp_df.iterrows():
            temp_relation = {'src':'','tgt':'','direction':''}
            temp_relation['src'] = row['Independent variable (original)'].lower()
            temp_relation['tgt'] = row['Dependent variable (original)'].lower()
            temp_relation['direction'] = row['Direction (Independent)'].lower()
            temp_dict['casual relations'].append(temp_relation)

        list_of_outputs.append(temp_dict)

        # Should now be in our universal JSON format

        with open("Secondary literature data combined.json", 'w') as outfile:
            json.dump(list_of_outputs)


def generate_dialog_id(existing_ids=set()):
    while True:  # Get current timestamp
        random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=6))  # Generate a random string
        dialog_id = f"{random_string}"  # Combine timestamp and random string
        if dialog_id not in existing_ids:
            existing_ids.add(dialog_id)
            return dialog_id

with open("C:/Users/milli/Downloads/Training_data.json","w") as f:
    quarter = round((len(file) - 1) * 0.75)
    prompts = []
    
    for sentence in file:
        id = generate_dialog_id(ids)
        ids.add(id)
        id2 = generate_dialog_id(ids)
        ids.add(id2)
        id3 = generate_dialog_id(ids)
        ids.add(id3)
        id4 = generate_dialog_id(ids)
        ids.add(id4)
        txt = ""
        master = {"dialog_id": f"{id}",
                  "dialog": []}
        test = {"messages": [{"role": "system",
                              "content": "Given a sentence, label the causal relations that indicate a change in quantity, quality, or sentiment and provide it as a list of JSON dictionaries, where each dictionary is formatted as {\"src\": \"\", \"tgt\":\"\", \"direction\":\"\"}. Direction can only be \"increase\" or \"decrease\", and \"src\" stands for source while \"tgt\" stands for target. Label for the following sentence. \n"}]}
        user = {"id": 0, "sender": "participant1",
                "text": sentence["text"]}
        assistant = {"id": 1, "sender": "participant2", "text": ""}
        for relation in sentence["causal relations"]:
            assistant["text"] += "source " + relation["src"] + " target " + relation["tgt"] + " direction " + relation["direction"] + "  "
        master["dialog"].append(user)
        master["dialog"].append(assistant)
        master["eval_score"] =  10
        master["profile_match"] = 1
        prompts.append(master)


        master2 = {"dialog_id": f"{id2}",
                  "dialog": []}
        user = {"id": 0, "sender": "participant1",
                "text": sentence["text"]}
        assistant = {"id": 1, "sender": "participant2", "text": "source source source source source source source source source source source source source source source source source source source source source source source source"}
        master2["dialog"].append(user)
        master2["dialog"].append(assistant)
        master2["eval_score"] = 0
        master2["profile_match"] = 0
        prompts.append(master2)


        master3 = {"dialog_id": f"{id3}",
                   "dialog": []}
        user = {"id": 0, "sender": "participant1",
                "text": sentence["text"]}
        assistant = {"id": 1, "sender": "participant2",
                     "text": "target target target target target target target target target target target target target target target target target target target target target target target target"}
        master3["dialog"].append(user)
        master3["dialog"].append(assistant)
        master3["eval_score"] = 0
        master3["profile_match"] = 0
        prompts.append(master3)

        master = {"dialog_id": f"{id4}",
                   "dialog": []}
        user = {"id": 0, "sender": "participant1",
                "text": sentence["text"]}
        assistant = {"id": 1, "sender": "participant2",
                     "text": "direction direction direction direction direction direction direction direction"}
        master["dialog"].append(user)
        master["dialog"].append(assistant)
        master["eval_score"] = 0
        master["profile_match"] = 0
        prompts.append(master)
        master = {"dialog_id": f"{id4}",
                  "dialog": []}
        user = {"id": 0, "sender": "participant1",
                "text": sentence["text"]}
        assistant = {"id": 1, "sender": "participant2",
                     "text": "source target direction source target direction source target direction source target direction source target direction"}
        master["dialog"].append(user)
        master["dialog"].append(assistant)
        master["eval_score"] = 2
        master["profile_match"] = 0
        prompts.append(master)
    temp = json.dumps(prompts,indent=2)
    f.write(temp)

with open("C:/Users/milli/Downloads/Testing_data.json","w") as f:
    quarter = round((len(file)-1)*0.75)
    prompts = []
    for sentence in file[quarter:]:
        id = generate_dialog_id(ids)
        ids.add(id)
        master = {"dialog_id": f"{id}",
                  "dialog": []}
        test = {"messages": [{"role": "system",
                              "content": "Given a sentence, label the causal relations that indicate a change in quantity, quality, or sentiment and provide it as a list of JSON dictionaries, where each dictionary is formatted as {\"src\": \"\", \"tgt\":\"\", \"direction\":\"\"}. Direction can only be \"increase\" or \"decrease\", and \"src\" stands for source while \"tgt\" stands for target."}]}
        user = {"id":0, "sender":"participant1","text":"Given a sentence, label the causal relations that indicate a change in quantity, quality, or sentiment. Direction can only be \"increase\" or \"decrease\". Label the following sentence. \n"+sentence["text"]}
        assistant = {"id":1,"sender":"participant2","text": ""}
        if sentence["causal relations"]:
            pass
        for relation in sentence["causal relations"]:
            assistant["text"] += "source " + relation["src"] + " target " + relation["tgt"] + " direction " + relation["direction"] + "  "
        master["dialog"].append(user)
        master["dialog"].append(assistant)
        master["eval_score"] =  10
        #master["profile_match"]: 2
        test['messages'].append(user)
        test['messages'].append(assistant)
        temp = json.dumps(test)
        prompts.append(master)
    temp = json.dumps(prompts,indent=2)
    f.write(temp)

"""""

with open("C:/Users/milli/Downloads/Training_data.json","w") as f:
    quarter = round((len(file) - 1) * 0.75)
    prompts = []
    
    for sentence in file:
        id = generate_dialog_id(ids)
        ids.add(id)
        id2 = generate_dialog_id(ids)
        ids.add(id2)
        id3 = generate_dialog_id(ids)
        ids.add(id3)
        id4 = generate_dialog_id(ids)
        ids.add(id4)
        txt = ""
        master = {"dialog_id": f"{id}",
                  "dialog": []}
        test = {"messages": [{"role": "system",
                              "content": "Given a sentence, label the causal relations that indicate a change in quantity, quality, or sentiment and provide it as a list of JSON dictionaries, where each dictionary is formatted as {\"src\": \"\", \"tgt\":\"\", \"direction\":\"\"}. Direction can only be \"increase\" or \"decrease\", and \"src\" stands for source while \"tgt\" stands for target. Label for the following sentence. \n"}]}
        user = {"id": 0, "sender": "participant1",
                "text": "Given a sentence, label the causal relations that indicate a change in quantity, quality, or sentiment. Direction can only be \"increase\" or \"decrease\" Label the following sentence. \n" +
                           sentence["text"]}
        assistant = {"id": 1, "sender": "participant2", "text": ""}
        for relation in sentence["causal relations"]:
            assistant["text"] += "source " + relation["src"] + " target " + relation["tgt"] + " direction " + relation["direction"] + "  "
        master["dialog"].append(user)
        master["dialog"].append(assistant)
        master["eval_score"] =  10
        master["profile_match"] = 1
        prompts.append(master)


        master2 = {"dialog_id": f"{id2}",
                  "dialog": []}
        user = {"id": 0, "sender": "participant1",
                "text": "Given a sentence, label the causal relations that indicate a change in quantity, quality, or sentiment. Direction can only be \"increase\" or \"decrease\" Label the following sentence. \n" +
                        sentence["text"]}
        assistant = {"id": 1, "sender": "participant2", "text": "source source source source source source source source source source source source source source source source source source source source source source source source"}
        master2["dialog"].append(user)
        master2["dialog"].append(assistant)
        master2["eval_score"] = 0
        master2["profile_match"] = 1
        prompts.append(master2)


        master3 = {"dialog_id": f"{id3}",
                   "dialog": []}
        user = {"id": 0, "sender": "participant1",
                "text": "Given a sentence, label the causal relations that indicate a change in quantity, quality, or sentiment. Direction can only be \"increase\" or \"decrease\" Label the following sentence. \n" +
                        sentence["text"]}
        assistant = {"id": 1, "sender": "participant2",
                     "text": "target target target target target target target target target target target target target target target target target target target target target target target target"}
        master3["dialog"].append(user)
        master3["dialog"].append(assistant)
        master3["eval_score"] = 0
        master3["profile_match"] = 1
        prompts.append(master3)

        master = {"dialog_id": f"{id4}",
                   "dialog": []}
        user = {"id": 0, "sender": "participant1",
                "text": "Given a sentence, label the causal relations that indicate a change in quantity, quality, or sentiment. Direction can only be \"increase\" or \"decrease\" Label the following sentence. \n" +
                        sentence["text"]}
        assistant = {"id": 1, "sender": "participant2",
                     "text": "direction direction direction direction direction direction direction direction"}
        master["dialog"].append(user)
        master["dialog"].append(assistant)
        master["eval_score"] = 0
        master["profile_match"] = 1
        prompts.append(master)
    temp = json.dumps(prompts,indent=2)
    f.write(temp)
user = {"id":0, "sender":"participant1","text":"Given a sentence, label the causal relations that indicate a change in quantity, quality, or sentiment and provide it as a list of JSON dictionaries, where each dictionary is formatted as {\"src\": \"\", \"tgt\":\"\", \"direction\":\"\"}. Direction can only be \"increase\" or \"decrease\", and \"src\" stands for source while \"tgt\" stands for target. Label the following sentence. \n"+sentence["text"]}
with open("C:/Users/milli/Downloads/Training_data.jsonl","w") as f:
    quarter = round((len(file)-1)*0.75)
    prompt = []
    for sentence in file[:quarter]:
        test = {"messages": [{"role": "system",
                              "content": "Given a sentence, label the causal relations that indicate a change in quantity, quality, or sentiment and provide it as a list of JSON dictionaries, where each dictionary is formatted as {\"src\": \"\", \"tgt\":\"\", \"direction\":\"\"}. Direction can only be \"increase\" or \"decrease\", and \"src\" stands for source while \"tgt\" stands for target."}]}
        user = {"role":"user","content":sentence["text"]}
        assistant = {"role":"assistant","content":str(sentence["causal relations"])}
        test['messages'].append(user)
        test['messages'].append(assistant)
        temp = json.dumps(test)
        f.write(temp+"\n")
"""