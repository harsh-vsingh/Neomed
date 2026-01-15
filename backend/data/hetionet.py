from datasets import load_dataset
import json

ds = load_dataset("dwb2023/hetionet-edges")

all_edges = []
for split in ds:
    all_edges.extend(ds[split].to_list())

with open("hetionet_edges_all.json", "w") as f:
    json.dump(all_edges, f)
