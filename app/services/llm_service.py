from langchain_google_genai import ChatGoogleGenerativeAI
from app.services.pdf_processor import get_pdf_index

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0,
    max_output_tokens=4096,
    top_p=1,
    top_k=1,
)

async def chat_with_llm(pdf_id: str, user_message: str) -> str:
    # Get the index for the specified PDF
    index = get_pdf_index(pdf_id)
    retriever = index.as_retriever(similarity_top_k=3)
    # Retrieve relevant documents
    retrieved_docs = retriever.retrieve(user_message)
    # Prepare the context from retrieved documents
    context = "\n\n".join([doc.get_content() for doc in retrieved_docs])
    # Prepare the prompt for the LLM
    prompt = f"""Based on the following context, please answer the question. If the answer is not in the context, say "I don't have enough information to answer this question."

Context:
{context}

Question: {user_message}

Answer:"""

    # Get the response from the LLM
    response = llm.invoke(prompt)
    # Prepare the full response
    full_response = f"Answer: {response.content}\n\nSources:\n"
    for i, doc in enumerate(retrieved_docs, 1):
        full_response += f"{i}. {doc.get_content()[:100]}...\n"
    return full_response

async def stream_long_response(full_response: str):
    chunk_size = 100000
    for i in range(0, len(full_response), chunk_size):
        yield full_response[i:i+chunk_size]