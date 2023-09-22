import torch
# from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    # TrainingArguments,
    pipeline
)
# from peft import PeftModel
from thefuzz import fuzz
import pandas as pd
from tqdm import tqdm

base_model_name = "NousResearch/Llama-2-7b-chat-hf"

# Load tokenizer
llama_tokenizer = AutoTokenizer.from_pretrained(base_model_name, trust_remote_code=True)
llama_tokenizer.pad_token = llama_tokenizer.eos_token
llama_tokenizer.padding_side = "right"

# Quantize model to 4-bit
quant_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=False,
)

# Load base model
base_model = AutoModelForCausalLM.from_pretrained(
    base_model_name,
    quantization_config=quant_config,
    device_map={"": 0},
    load_in_4bit=True,
)
# Test data is the last 200 lines
eval_data = pd.read_csv("traces/gpt-keyword-log.csv")[800:]
eval_data.reset_index(inplace=True)
print(len(eval_data))
eval_data.insert(2, "llm_response", "")
eval_data.insert(3, "similarity_score", 0)

text_gen = pipeline(task="text-generation", model=base_model, tokenizer=llama_tokenizer, max_length=400)

for i in tqdm(range(len(eval_data))):
    query = eval_data["prompt"][i]
    gt_response = eval_data["response"][i]
    
    llm_response = text_gen(f"<s>[INST] {query} [/INST]")[0]["generated_text"].split("[/INST]")[1].strip().replace("\n", " ").replace("  ", "")
    
    eval_data.at[i, "llm_response"] = llm_response
    
    score = fuzz.token_sort_ratio(llm_response, gt_response)
    # print(gt_response)
    # print(llm_response)
    # print(score)
    eval_data.at[i, "similarity_score"] = score
    
print(f"Average token sort ratio similarity score: {eval_data['similarity_score'].mean()}")

eval_data.to_csv("keyword_ft/keyword_base_eval.csv")


# Untrained LLAMA average: 87.83417085427136