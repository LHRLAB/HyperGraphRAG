import os
import json
import time
from hypergraphrag import HyperGraphRAG

os.environ["OPENAI_API_KEY"] = open("openai_api_key.txt").read().strip()

def insert_text(rag, file_path):
    with open(file_path, mode="r") as f:
        unique_contexts = json.load(f)

    retries = 0
    max_retries = 10
    while retries < max_retries:
        try:
            rag.insert(unique_contexts)
            break
        except Exception as e:
            retries += 1
            print(f"Insertion failed, retrying ({retries}/{max_retries}), error: {e}")
            time.sleep(10)
    if retries == max_retries:
        print("Insertion failed after exceeding the maximum number of retries")


cls = "sample"
WORKING_DIR = f"expr/ultradoman/{cls}"

if not os.path.exists(WORKING_DIR):
    os.makedirs(WORKING_DIR)

rag = HyperGraphRAG(working_dir=WORKING_DIR,embedding_func_max_async=4,llm_model_max_async=4)

insert_text(rag, f"datasets/ultradoman/unique_contexts/{cls}_unique_contexts.json")
