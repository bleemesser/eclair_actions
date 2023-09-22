import os
import pandas as pd
from tqdm import tqdm

for file in os.listdir("traces"):
    with open(f"traces/{file}", "r") as f:
        contents = f.read()
    df = pd.DataFrame(columns=["prompt", "response"])
    for task in tqdm(contents.split("<task>")):
        task = task.split("</task>")[0]
        if task == "":
            continue
        prompt = task.split("<prompt>")[1].split("</prompt>")[0].strip()
        response = task.split("<response>")[1].split("</response>")[0].strip()
        df = pd.concat([df, pd.DataFrame({"prompt": [prompt], "response": [response]})], ignore_index=True)
    df.to_csv(f"{file.replace('.txt', '')}.csv")
    