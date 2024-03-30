import json
import time
import random
import string
"""
This conversion file converts from our main JSON format to the tokenized LLM format.
"""

f = open("C:/Users/milli/Downloads/OSW_labeled_data.json")

ids = set()
files = [f]

class NoFileError: Exception
def generate_dialog_id(existing_ids=set()):
    while True:  # Get current timestamp
        random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=6))  # Generate a random string
        dialog_id = f"{random_string}"  # Combine timestamp and random string
        if dialog_id not in existing_ids:
            existing_ids.add(dialog_id)
            return dialog_id

def file_convert():
    merged_json = []
    if len(files) > 1:
        merged_json = json.load(files[0])
        for file_ in files[1:]:
            merged_json.append(json.load(file_))
    elif len(files) == 0:
        raise NoFileError
    else:
        merged_json = json.load(files[0])
    prompts = []
    for sentence in merged_json:
        id = generate_dialog_id(ids)
        ids.add(id)
        master = {"dialog_id": f"{id}",
                  "dialog": []}
        user = {"id": 0, "sender": "participant1",
                "text": sentence["text"]}
        assistant = {"id": 1, "sender": "participant2", "text": ""}
        for relation in sentence["causal relations"]:
            assistant["text"] += "<triplet> " + relation["src"] + " <src> " + relation["direction"] + " <tgt> " + relation["tgt"] +" "
        assistant["text"] = assistant["text"].strip()
        master["dialog"].append(user)
        master["dialog"].append(assistant)
        prompts.append(master)
    return prompts
with open("C:/Users/milli/Downloads/Training_data.json", "w") as f:
    #quarter = round((len(file) - 1) * 0.75)
    tokenized_json = file_convert()

    f.write(json.dumps(tokenized_json,indent=2))