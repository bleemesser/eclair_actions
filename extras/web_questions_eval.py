from actions.google_search.self_ask import self_ask
from datasets import load_dataset
from thefuzz import fuzz
import pandas as pd
from tqdm import tqdm
import time
import os
DATASET_MODE = "train"

dataset = load_dataset("web_questions")

dataset = dataset[DATASET_MODE]
output_dataset = pd.DataFrame(columns=["question", "answer", "dataset_answers", "token_sort_ratio"])
last_checkpoint = max([int(x.split("_")[-1].split(".")[0]) for x in os.listdir("eval_out") if x.startswith(f"self_ask_{DATASET_MODE}")])
output_dataset = pd.read_csv(f"eval_out/self_ask_{DATASET_MODE}_{last_checkpoint}.csv", index_col=0) if last_checkpoint > 0 else output_dataset
print(f"Starting from checkpoint {last_checkpoint}")
for i in tqdm(range(1000)):
    # time.sleep(60)
    if i < last_checkpoint:
        continue
    answer = self_ask(dataset[i]["question"])
    dataset_answers = " ".join(dataset[i]["answers"])
    scores = []
    for option in [dataset_answers] + dataset[i]["answers"]:
        scores.append(fuzz.token_set_ratio(answer, option)) # use token set ratio so that if the dataset answer is in the model answer, it's a 100% match
    score = max(scores) # test both the concatenation of all answers and each individual answer, and take the max score
    
    output_dataset = pd.concat([output_dataset, pd.DataFrame({"question": [dataset[i]["question"]], "answer": [answer], "dataset_answers": [dataset_answers], "token_sort_ratio": [score]})], ignore_index=True)
    if i % 5 == 0:
        output_dataset.to_csv(f"eval_out/self_ask_{DATASET_MODE}_{i}.csv")
    
score = output_dataset["token_sort_ratio"].mean()
print(f"Average token sort ratio similarity score: {score}")
output_dataset.to_csv(f"eval_out/self_ask_{DATASET_MODE}.csv")
    

# with open(f"eval_out/self_ask_{DATASET_MODE}_{last_checkpoint}.csv", "r") as f:
#     output_dataset = pd.read_csv(f, index_col=0)
# score = output_dataset["token_sort_ratio"].mean()
# print(f"Average token sort ratio similarity score: {score}")

# for gpt3: 68.83