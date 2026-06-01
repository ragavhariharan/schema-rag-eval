from langchain_community.chat_models import ChatOllama
import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection(name="lens_schema_rag")
results = collection.query(query_texts=["Show me all lenses that weigh under 200g."], n_results=5)
contexts = results['documents'][0] if results['documents'] else []

llm = ChatOllama(model="qwen2.5-coder", base_url="http://localhost:11434", num_ctx=32768)

huge_prompt = "Here are 5 tables:\n" + "\n".join(contexts) + "\n\nCan you process this? Output valid JSON: {'processed': true}"

try:
    response = llm.invoke(huge_prompt)
    print("Response:", response.content)
except Exception as e:
    import traceback
    traceback.print_exc()
