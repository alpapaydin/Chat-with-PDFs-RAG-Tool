from app.services.pdf_processor import get_chat_indices
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine

class CombinedRetriever:
    def __init__(self, retrievers):
        self.retrievers = retrievers
    def retrieve(self, query):
        results = []
        for retriever in self.retrievers:
            results.extend(retriever.retrieve(query))
        return results

async def chat_with_llm(chat_id: str, user_message: str) -> str:
    indices = get_chat_indices(chat_id)
    # Combine retrievers from all indices 
    retrievers = [VectorIndexRetriever(index=index) for index in indices]
    combined_retriever = CombinedRetriever(retrievers)
    # Create a query engine with the combined retriever
    query_engine = RetrieverQueryEngine(retriever=combined_retriever)
    # Run the query
    response = query_engine.query(user_message)
    # Prepare the full response
    full_response = f"Answer: {response.response}\n\nSources:\n"
    for i, node in enumerate(response.source_nodes, 1):
        full_response += f"{i}. {node.node.get_content()[:100]}...\n"
    return full_response

async def stream_long_response(full_response: str):
    chunk_size = 100000
    for i in range(0, len(full_response), chunk_size):
        yield full_response[i:i+chunk_size]