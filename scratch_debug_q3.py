import json
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import context_precision, context_recall, faithfulness, answer_relevancy
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import HuggingFaceEmbeddings
import chromadb
import re

import asyncio
import nest_asyncio
nest_asyncio.apply()
try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

import ragas.executor
class MainThreadRunner(ragas.executor.Runner):
    def start(self): self.run()
    def join(self, timeout=None): pass
    def run(self):
        old_loop = None
        try: old_loop = asyncio.get_event_loop()
        except RuntimeError: pass
        asyncio.set_event_loop(self.loop)
        import nest_asyncio
        nest_asyncio.apply(self.loop)
        self.futures = ragas.executor.as_completed(loop=self.loop, coros=[coro for coro, _ in self.jobs], max_workers=self.run_config.max_workers)
        results = []
        try: results = self.loop.run_until_complete(self._aresults())
        finally:
            self.results = results
            self.loop.stop()
            if old_loop is not None: asyncio.set_event_loop(old_loop)
ragas.executor.Runner = MainThreadRunner

import ragas.llms
from ragas.run_config import RunConfig, add_retry
async def patched_generate(self, prompt, n=1, temperature=1e-8, stop=None, callbacks=None, is_async=True):
    generate_text_with_retry = add_retry(self.generate_text, self.run_config)
    result = generate_text_with_retry(prompt=prompt, n=n, temperature=temperature, stop=stop, callbacks=callbacks)
    return result
ragas.llms.LangchainLLMWrapper.generate = patched_generate

local_llm = ChatOllama(model="qwen2.5-coder", base_url="http://localhost:11434")
local_embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_collection(name="lens_schema_rag")

def get_q3():
    with open("golden_dataset.json", "r") as f:
        golden_data = json.load(f)
    return golden_data[2]  # Q3 is index 2

q3 = get_q3()
results = collection.query(query_texts=[q3["question"]], n_results=5)
contexts = results['documents'][0] if results['documents'] else []

print(f"Number of contexts retrieved: {len(contexts)}")
total_length = sum(len(c) for c in contexts)
print(f"Total context string length: {total_length}")

# Dummy values for fast check
data_dict = {
    "question": [q3["question"]],
    "answer": ["SELECT model_name FROM all_lenses WHERE weight_g < 200;"],
    "contexts": [contexts],
    "ground_truth": ["Show me all lenses that weigh under 200g."]
}

ds = Dataset.from_dict(data_dict)

print("\nEvaluating Q3...")
try:
    score = evaluate(
        dataset=ds,
        metrics=[context_precision],
        llm=local_llm,
        embeddings=local_embeddings,
        raise_exceptions=True,  # Set to True to see the actual error!
        is_async=False,
        run_config=RunConfig(max_workers=-1)
    )
    print(score)
except Exception as e:
    import traceback
    traceback.print_exc()
