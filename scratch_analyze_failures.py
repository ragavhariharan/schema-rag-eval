import pandas as pd
import json

df = pd.read_csv("detailed_evaluation_trace.csv")

print("=== DEEP ANALYSIS OF FAILURES ===")
for idx, row in df.iterrows():
    # Identify failures
    cp = row.get("context_precision", 0)
    cr = row.get("context_recall", 0)
    fa = row.get("faithfulness", 0)
    ar = row.get("answer_relevancy", 0)
    
    if pd.isna(cp): cp = 0
    if pd.isna(cr): cr = 0
    if pd.isna(fa): fa = 0
    if pd.isna(ar): ar = 0

    if cp < 0.5 or cr < 0.5 or fa < 0.5:
        print(f"\n--- QUESTION {idx+1}: {row['id']} ---")
        print(f"Metrics: Precision={cp:.2f}, Recall={cr:.2f}, Faithfulness={fa:.2f}, Relevancy={ar:.2f}")
        print(f"Question: {row['question']}")
        print(f"Extracted Filters: {row['filters_extracted']}")
        print(f"Generated SQL: \n{row['generated_sql']}")
        print(f"Ground Truth NL: \n{row['ground_truth_nl']}")
        
        contexts = row['contexts']
        # Try to count how many unique tables were retrieved
        print(f"Contexts Preview:")
        try:
            ctx_list = eval(contexts) if isinstance(contexts, str) else contexts
            for i, c in enumerate(ctx_list):
                print(f"  Chunk {i+1}: {c[:80]}...")
        except:
            print("  Could not parse contexts")
        
        print("------------------------------------------------")
