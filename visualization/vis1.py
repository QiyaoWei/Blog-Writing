from collections import defaultdict
import numpy as np
import pandas as pd
import torch
from datasets import load_dataset
from rich.console import Console
from rich.table import Table
from transformers import (
    AutoTokenizer,
    PreTrainedModel,
    AutoModelForCausalLM,
    GenerationConfig,
)


######
# Utility functions
######

def generate(lm_backbone, queries, tokenizer, generation_config):
    
    """generate in a way that does not affect padding tokens
    
    Args:
        queries (torch.Tensor): tensor of shape (batch_size, sequence_length)
        
    Return:
        xxx
    """
        
    context_length = queries.shape[1] # sequence length
    
    # did you always have to handle pad tokens separately? I always thought it was automatic handling?
    attention_mask = queries != tokenizer.pad_token_id
    input_ids = torch.masked_fill(queries, ~attention_mask, 0)
    
    # preprocessing done
    output = lm_backbone.generate(
        input_ids=input_ids,
        attention_mask=attention_mask,
        # position_ids=attention_mask.cumsum(1) - attention_mask.long(), # generation collapsed if this was turned on. TODO: why does generation collapse with this?
        generation_config=generation_config,
        return_dict_in_generate=True,
    )
    return torch.cat((queries, output.sequences[:, context_length:]), dim=1)

def forward(model, query_responses, tokenizer):
    
    # This is a forward function that automatically takes care of padding, attention mask, and position ids
    
    attention_mask = query_responses != tokenizer.pad_token_id
    position_ids = attention_mask.cumsum(1) - attention_mask.long()
    input_ids = torch.masked_fill(query_responses, ~attention_mask, 0)
    return model(
        input_ids=input_ids,
        attention_mask=attention_mask,
        position_ids=position_ids,
        return_dict=True,
        output_hidden_states=True,
    )

def print_rich_table(title: str, df: pd.DataFrame, console: Console) -> Table:
    table = Table(show_lines=True)
    for column in df.columns:
        table.add_column(column)
    for _, row in df.iterrows():
        table.add_row(*row.astype(str).tolist())
    console.rule(f"[bold red]{title}")
    console.print(table)


######
# Start
######

device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
tokenizer = AutoTokenizer.from_pretrained("lvwerra/gpt2-imdb")
tokenizer.add_special_tokens({"pad_token": "[PAD]"})
response_length = 20
validation_generation_config = GenerationConfig(
    max_new_tokens=response_length,
    temperature=(0.01 + 1e-7),
    top_k=0.0,
    top_p=1.0,
    do_sample=True,
    pad_token_id=tokenizer.pad_token_id,
    eos_token_id=tokenizer.eos_token_id,
)

def build_dataset(dataset_name="imdb", input_min_text_length=2, input_max_text_length=8):
    """
    Build dataset for training. This builds the dataset from `load_dataset`, one should
    customize this function to train the model on its own dataset.

    Args:
        dataset_name (`str`):
            The name of the dataset to be loaded.

    Returns:
        dataloader (`torch.utils.data.DataLoader`):
            The dataloader for the dataset.
    """

    ds = load_dataset(dataset_name, split="train")
    ds = ds.rename_columns({"text": "review"})
    ds = ds.filter(lambda x: len(x["review"]) > 100, batched=False)

    input_size = 5
    # input_size = LengthSampler(input_min_text_length, input_max_text_length)

    def tokenize(sample):
        sample["input_ids"] = tokenizer.encode(sample["review"])[: input_size]
        sample["response_ids"] = tokenizer.encode(sample["review"])[input_size :]
        sample["query"] = tokenizer.decode(sample["input_ids"])
        return sample

    ds = ds.map(tokenize, batched=False)
    ds.set_format(type="torch")
    return ds
dataset = build_dataset()
dataloader = torch.utils.data.DataLoader(dataset, batch_size=1, shuffle=True)

base_model: PreTrainedModel = AutoModelForCausalLM.from_pretrained("lvwerra/gpt2-imdb").to(device)
# ppo_model: PreTrainedModel = AutoModelForCausalLM.from_pretrained(
#     "vwxyzjn/EleutherAI_pythia-1b-deduped__ppo_left_padding__tldr",
#     revision="ppo_left_padding__55513__1706746254",
#     trust_remote_code=True,
# ).to(device)
compared_models = {
    "base_model": base_model,
    "aligned_model": base_model,
}

# The idea is to sample a response from the aligned LLM and check if base LLM would greedy sample the same tokens
# if so, then color the text blue (unshifted tokens)
# elif the token is within the top 3 probability, color the text yellow
# otherwise color the text red (shifted tokens)
# so simply speaking the red tokens corresponds to what RLHF-ed models do differently.
nchecks = 4
colors = {
    0: "on blue",
    1: "on yellow",
    2: "on yellow",
    3: "on red",
}
console = Console()

for i in dataloader:
    
    table = defaultdict(list)
    # print(i["review"])
    query = torch.Tensor(i["input_ids"]).to(device).long()
    query_reference_response = torch.Tensor(i["response_ids"]).to(device).long()
    
    with torch.no_grad():
        
        # models
        aligned_model = compared_models["aligned_model"]
        base_model = compared_models["base_model"]
        
        # sequence length
        context_length = query.shape[1]
        
        # responses excluding the prompt
        aligned_model_query_response = generate(aligned_model, query, tokenizer, validation_generation_config)
        aligned_model_response = aligned_model_query_response[:, context_length:]
        base_model_query_response = generate(base_model, query, tokenizer, validation_generation_config)
        base_model_response = base_model_query_response[:, context_length:]
        
        # here the forward is done on the entire sequence, not just the response (but also the prompt)
        aligned_model_output = forward(aligned_model, aligned_model_query_response, tokenizer)
        base_model_output = forward(base_model, aligned_model_query_response, tokenizer)
        
        # extracting the logits of the response, not the prompt
        aligned_model_logits = aligned_model_output.logits[:, context_length-1:-1]
        _, aligned_model_topk_indices = aligned_model_logits.topk(10)
        base_model_logits = base_model_output.logits[:, context_length-1:-1]
        _, base_model_topk_indices = base_model_logits.topk(10)

        aligned_model_topk_indices[:,:,0:1].expand(-1, -1, nchecks)
        matches = aligned_model_topk_indices[:,:,0:1].expand(-1, -1, nchecks) == base_model_topk_indices[:,:,0:nchecks]
        matched = matches.sum(2)
        match_idx = matches.float().argmax(2)
        final_matches = torch.where(matched > 0, match_idx, nchecks-1)
        stats = torch.stack([(final_matches == i).sum(1) for i in range(nchecks)]).T

    final_matches = final_matches.tolist()
    aligned_model_response = aligned_model_response.tolist()
    table["type"].append("Query")
    table["content"].append(tokenizer.decode(query[0].detach().cpu(), skip_special_tokens=True))
    table["type"].append("PPO Model Response")
    table["content"].append("".join([f"[{colors[jt]}]{tokenizer.decode(it)}[/{colors[jt]}]" for it, jt in zip(aligned_model_response[0], final_matches[0])]))
    table["type"].append("Matched Color Counts")
    table["content"].append(stats[0].detach().cpu())
    table["type"].append("Base Model Response")
    table["content"].append(tokenizer.decode(base_model_response[0].detach().cpu(), skip_special_tokens=True))

    df = pd.DataFrame(table)
    print_rich_table("Results", df, console)
    if input("Continue? (press `n` to stop) ") == "n":
        break