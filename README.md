# PDF Chat API

## Project Overview

PDF Chat API is a sophisticated FastAPI application that enables users to upload PDF documents and engage in chat conversations about their content. The system uses advanced natural language processing techniques to analyze PDFs and respond to user queries intelligently.

Key features include:
- PDF upload and processing
- Chat functionality based on PDF content
- Support for multiple PDFs in a single chat session
- Retrieval of chat and PDF information

## Setup Instructions

### Prerequisites

- Python 3.8+
- pip (Python package installer)
- virtualenv (recommended for creating isolated Python environments)

### Environment Setup

1. Clone the repository, or extract the zip in this case.

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the root directory and add the following:
   ```
   GOOGLE_API_KEY=your_google_api_key_here
   ```
   Replace `your_google_api_key_here` with your actual Google API key.

## Running the Application

To start the application, run:
```
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

## API Endpoints

### 1. Upload PDF

- **URL**: `/v1/pdf`
- **Method**: POST
- **Content-Type**: multipart/form-data
- **Parameters**:
  - `file`: PDF file (required)
  - `chat_id`: String (optional)

#### Example Request:
```
curl -X POST "http://localhost:8000/v1/pdf" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@path/to/your/file.pdf" \
     -F "chat_id=optional_chat_id"
```

#### Example Response:
```json
{
  "pdf_id": "123e4567-e89b-12d3-a456-426614174000",
  "chat_id": "789f0123-e45b-67d8-a901-234567890000"
}
```

### 2. Chat with PDF

- **URL**: `/v1/chat/{chat_id}`
- **Method**: POST
- **Content-Type**: application/json
- **Parameters**:
  - `chat_id`: String (in URL)
  - `message`: String (in request body)

#### Example Request:
```
curl -X POST "http://localhost:8000/v1/chat/789f0123-e45b-67d8-a901-234567890000" \
     -H "Content-Type: application/json" \
     -d '{"message": "What is the main topic of the PDF?"}'
```

#### Example Response:
```
Answer: The main topic of the PDF is artificial intelligence in healthcare.

Sources:
1. Page 1: "This document explores the applications of artificial intelligence in modern healthcare..."
2. Page 3: "AI technologies are revolutionizing diagnostic procedures, treatment plans, and patient care..."
```

### 3. Get Chats

- **URL**: `/v1/chats`
- **Method**: GET

#### Example Request:
```
curl "http://localhost:8000/v1/chats"
```

#### Example Response:
```json
[
  {"id": "789f0123-e45b-67d8-a901-234567890000"},
  {"id": "456a7890-b12c-34d5-e678-901234567000"}
]
```

### 4. Get Chat PDFs

- **URL**: `/v1/chat/{chat_id}/pdfs`
- **Method**: GET
- **Parameters**:
  - `chat_id`: String (in URL)

#### Example Request:
```
curl "http://localhost:8000/v1/chat/789f0123-e45b-67d8-a901-234567890000/pdfs"
```

#### Example Response:
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "filename": "ai_in_healthcare.pdf"
  },
  {
    "id": "abcd1234-e56f-78g9-h012-345678901000",
    "filename": "medical_ai_ethics.pdf"
  }
]
```

## Testing

### Running Tests

To run the test suite, use the following command:
```
pytest
```

This will run all tests in the `tests/` directory.

## Troubleshooting

- If you encounter database-related errors, ensure that your database is properly initialized and that you have the necessary permissions.
- For API key related issues, double-check that your `.env` file contains the correct Google API key.
- If you face import errors, verify that all dependencies are correctly installed and that you're running the application from the correct directory.

## Technical Considerations

### Retrieval-Augmented Generation (RAG) vs. Large Context Models

This project implements a Retrieval-Augmented Generation (RAG) approach using LlamaIndex, rather than relying solely on large context models like Gemini 1.5 Flash. RAG offers several advantages:

1. Efficient retrieval of relevant information from large document sets.
2. Ability to handle multiple documents in a single chat session.
3. Improved accuracy by focusing on relevant context.
4. More scalable solution for growing document bases.

While large context models like Gemini 1.5 Flash offer impressive capabilities, the RAG approach provides a more flexible and scalable solution for our use case.

### Handling Large Outputs

To address the limitation of output tokens (typically 8196 for many models), this project implements a streaming response mechanism. The `stream_long_response` function in `llm_service.py` chunks large responses into manageable pieces, allowing for the delivery of responses that exceed typical token limits.

### Evaluating LLM Performance

While the current test suite focuses on functional testing of the API, evaluating the performance of the Large Language Model requires additional considerations:

1. Implement benchmark datasets specific to your use case.
2. Use metrics such as perplexity, BLEU score, or domain-specific accuracy measures.
3. Conduct human evaluation for qualitative assessment of responses.
4. Implement A/B testing to compare different models or configurations.
5. Monitor response times and resource usage in production.

Future improvements to the project could include implementing these evaluation methods to ensure ongoing LLM performance optimization.

## License

This project is licensed under the MIT License - see the LICENSE.md file for details.