import json
import time
import random
import string

f = open("C:/Users/milli/Downloads/OSW_labeled_data.json")
#file = json.load(f)
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
    if len(files) > 1:  # main case
        merged_json = json.load(files[0])
        for file_ in files[1:]:
            merged_json.append(json.load(file_))
    elif len(files) == 0:  # error no file case
        raise NoFileError
    else:  # one file case
        merged_json = json.load(files[0])
    prompts = []
    for sentence in merged_json:
        sentence['LLM'] = {'GPT3.5': sentence['causal relations']}
        sentence['LLM']["Bert"] = sentence['causal relations']
        prompts.append(sentence)
    return prompts
with open("C:/Users/milli/Downloads/DashTest.json", "w") as f:
    #quarter = round((len(file) - 1) * 0.75)
    tokenized_json = file_convert()

    f.write(json.dumps(tokenized_json,indent=2))