from dotenv import load_dotenv
from haystack.document_stores import InMemoryDocumentStore
from haystack.nodes import BM25Retriever, PromptNode
from haystack.nodes.prompt import PromptTemplate
from haystack.pipelines import Pipeline
import os
import openai 

# Example environment variable for your API key:
# export OPENAI_API_KEY="sk-xyz..."

load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY")
openai.api_key = openai_key

def main():
    document_store = InMemoryDocumentStore(use_bm25=True)

    # (Optional) Load .txt docs or create them in Python
    docs = [
        {"content": "Tang Institute was founded in 2014 as a research center..."},
        # ...
    ]
    document_store.write_documents(docs)

    # BM25 keyword-based retrieval
    retriever = BM25Retriever(document_store)

    # 1) Define a custom template
    my_local_template = PromptTemplate(
        """
        You are a helpful assistant. 
        Given the following documents: 
        {documents}

        Please answer the question:
        {query}

        Provide a concise answer.
        """
    )
    # 2) Use PromptNode with OpenAI as the "backend"
    prompt_node = PromptNode(
        model_name_or_path="gpt-3.5-turbo",
        default_prompt_template=my_local_template,
        api_key=openai_key,
        model_kwargs={"temperature": 0}
    )

    pipeline = Pipeline()
    pipeline.add_node(retriever,  name="Retriever",    inputs=["Query"])
    pipeline.add_node(prompt_node, name="OpenAIPrompt", inputs=["Retriever"])

    # Example question
    query = "When was Tang Institute established?"
    output = pipeline.run(query=query)
    print(output)

if __name__ == "__main__":
    main()
