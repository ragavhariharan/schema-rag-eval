import pandas as pd
import json

df = pd.read_csv("detailed_evaluation_trace.csv")

print("=== DEEP ANALYSIS OF FAILURES ===")
for idx, row in df.iterrows():
    if row['id'] in ['q15_compact_thread_search', 'q11_high_magnification', 'q10_conjugate_terminology', 'q7_coaxial_dimensions']:
        print(f"\n--- QUESTION {idx+1}: {row['id']} ---")
        print(f"Question: {row['question']}")
        print(f"Generated SQL: \n{row['generated_sql']}")
        print(f"Contexts:")
        contexts = row['contexts']
        try:
            ctx_list = eval(contexts) if isinstance(contexts, str) else contexts
            for i, c in enumerate(ctx_list):
                print(f"\nCHUNK {i+1}:\n{c}")
        except:
            pass
        print("------------------------------------------------")
