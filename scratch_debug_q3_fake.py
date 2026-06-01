import pandas as pd
import json
import asyncio
import nest_asyncio
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import context_precision, context_recall, faithfulness, answer_relevancy
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import HuggingFaceEmbeddings
import ragas.executor
from ragas.run_config import RunConfig, add_retry

# --- Patches ---
nest_asyncio.apply()
try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

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
async def patched_generate(self, prompt, n=1, temperature=1e-8, stop=None, callbacks=None, is_async=True):
    generate_text_with_retry = add_retry(self.generate_text, self.run_config)
    result = generate_text_with_retry(prompt=prompt, n=n, temperature=temperature, stop=stop, callbacks=callbacks)
    return result
ragas.llms.LangchainLLMWrapper.generate = patched_generate

local_llm = ChatOllama(model="qwen2.5-coder", base_url="http://localhost:11434")
local_embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def build_q3_dataset():
    with open("golden_dataset.json", "r") as f:
        golden_data = json.load(f)
    q3 = golden_data[2]
    
    # We don't need ChromaDB, just fake the contexts or pass a small context
    contexts = ["Fake context just to see if it's the chunk size causing issues."] * 5
    
    data_dict = {
        "question": [q3["question"]],
        "answer": ["SELECT model_name FROM all_lenses WHERE weight_g < 200;"],
        "contexts": [contexts],
        "ground_truth": ["Show me all lenses that weigh under 200g."]
    }
    return Dataset.from_dict(data_dict)

ds = build_q3_dataset()

print("\nEvaluating Q3 with small fake contexts...")
try:
    score = evaluate(
        dataset=ds,
        metrics=[context_precision],
        llm=local_llm,
        embeddings=local_embeddings,
        raise_exceptions=True,
        is_async=False,
        run_config=RunConfig(max_workers=-1)
    )
    print("SUCCESS!")
    print(score)
except Exception as e:
    import traceback
    traceback.print_exc()
