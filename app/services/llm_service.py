from app.services.pdf_processor import get_chat_indices
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.chat_engine import ContextChatEngine
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage, MessageRole
from app.db.database import get_db
from app.db.models import Message
from app.core.config import get_settings
from typing import List

class CombinedRetriever:
    def __init__(self, retrievers):
        self.retrievers = retrievers
    def retrieve(self, query):
        results = []
        for retriever in self.retrievers:
            results.extend(retriever.retrieve(query))
        return results

def get_chat_history(chat_id: str) -> List[ChatMessage]:
    db = next(get_db())
    chat_history = db.query(Message).filter(Message.chat_id == chat_id).order_by(Message.timestamp).limit(get_settings().CONTEXT_LENGTH).all()
    chat_history.reverse()
    db.close()
    return [
        ChatMessage(
            role=MessageRole.USER if msg.is_user else MessageRole.ASSISTANT,
            content=msg.content
        )
        for msg in chat_history
    ]

async def chat_with_llm(chat_id: str, user_message: str) -> str:
    indices = get_chat_indices(chat_id)
    retrievers = [VectorIndexRetriever(index=index) for index in indices]
    combined_retriever = CombinedRetriever(retrievers)
    # Create a ChatMemoryBuffer and populate it with chat history
    chat_history = get_chat_history(chat_id)
    memory = ChatMemoryBuffer.from_defaults(chat_history=chat_history)
    # Create a ContextChatEngine
    chat_engine = ContextChatEngine.from_defaults(
        retriever=combined_retriever,
        memory=memory,
        system_prompt="""You are an AI assistant helping users with questions about uploaded PDF documents. 
        Use the context from the documents to answer questions. If you don't have enough information, say so."""
    )

    # Generate response
    response = chat_engine.chat(user_message)

    # Prepare the full response
    full_response = f"Answer: {response.response}\n\nSources:\n"
    for i, node in enumerate(response.source_nodes, 1):
        full_response += f"{i}. {node.node.get_content()[:100]}...\n"

    return full_response

async def stream_long_response(full_response: str):
    chunk_size = 100000
    for i in range(0, len(full_response), chunk_size):
        yield full_response[i:i+chunk_size]