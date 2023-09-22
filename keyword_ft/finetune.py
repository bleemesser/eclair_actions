import torch
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    pipeline,
)
from peft import LoraConfig
from trl import SFTTrainer
from sklearn.model_selection import train_test_split
import pandas as pd
from thefuzz import fuzz
from tqdm import tqdm
import os

# Load and format traces into a dataset
dataset = pd.read_csv("traces/gpt-keyword-log.csv")

def format_instruction(sample):
    instruction = (
        """Below is an instruction that describes a task. Write a response that appropriately completes the request. ### Instruction: """
        + sample["prompt"]
        + """ ### Response: """
        + sample["response"]
    )
    return instruction

dataset.insert(0, "text", dataset.apply(format_instruction, axis=1))

dataset = Dataset.from_pandas(dataset)

train_dataset, eval_dataset = train_test_split(dataset, test_size=0.35)
train_dataset = Dataset.from_dict(train_dataset)
eval_dataset = Dataset.from_dict(eval_dataset)

print(f"Train dataset length: {len(train_dataset)}")
print(f"Eval dataset length: {len(eval_dataset)}")

# Set up tokenizer
base_model_name = "NousResearch/Llama-2-7b-chat-hf"
refined_model_name = "treei/llama-2-7b-keyword-ft"

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
base_model.config.use_cache = False
base_model.config.pretraining_tp = 1

# Configure LoRA using peft
peft_parameters = LoraConfig(
    lora_alpha=16, lora_dropout=0.1, r=8, bias="none", task_type="CAUSAL_LM"
)

# Configure training arguments
train_params = TrainingArguments(
    output_dir="./checkpoints",
    num_train_epochs=4,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=1,
    optim="paged_adamw_32bit",
    save_steps=25,
    logging_steps=25,
    learning_rate=1e-4,
    weight_decay=0.001,
    bf16=True,
    tf32=True,
    max_grad_norm=0.3,
    max_steps=-1,
    warmup_ratio=0.03,
    group_by_length=True,
    lr_scheduler_type="constant",
    report_to="wandb",
)

# Instantiate trainer
trainer = SFTTrainer(
    model=base_model,
    train_dataset=train_dataset,
    peft_config=peft_parameters,
    max_seq_length=2048,
    dataset_text_field="text",
    tokenizer=llama_tokenizer,
    args=train_params,
)

# Eval base model before training
if not os.path.exists("keyword_ft/base_eval_keywords.csv"):
    text_gen = pipeline(task="text-generation", model=base_model, tokenizer=llama_tokenizer, max_length=400)
    eval_out = pd.DataFrame(columns=["prompt", "response", "llm_response", "similarity_score"])
    for i in tqdm(range(len(eval_dataset))):
        query = eval_dataset["prompt"][i]
        gt_response = eval_dataset["response"][i]
        
        llm_response = text_gen(f"<s>[INST] {query} [/INST]")[0]["generated_text"].split("[/INST]")[1].strip().replace("\n", " ").replace("  ", "")
        
        score = fuzz.token_sort_ratio(llm_response, gt_response)
        eval_out = pd.concat([eval_out, pd.DataFrame({"prompt": [query], "response": [gt_response], "llm_response": [llm_response], "similarity_score": [score]})], ignore_index=True)

    # write to csv
    eval_out.to_csv("keyword_ft/base_eval_keywords.csv")
    print("Saved base eval to csv. Average token sort ratio similarity score:", eval_out["similarity_score"].mean())
    
# Train model and save
trainer.train()
trainer.model.save_pretrained(refined_model_name)

