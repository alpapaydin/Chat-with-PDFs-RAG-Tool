let currentPdfId = null;

async function uploadPDF() {
    const fileInput = document.getElementById('pdf-file');
    const file = fileInput.files[0];
    if (!file) {
        alert('Please select a PDF file');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/v1/pdf', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('PDF upload failed');
        }

        const data = await response.json();
        currentPdfId = data.pdf_id;
        
        document.getElementById('pdf-upload').style.display = 'none';
        document.getElementById('chat-interface').style.display = 'block';
        
        addMessage('System', 'PDF uploaded successfully. You can now ask questions about it.');
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while uploading the PDF');
    }
}

async function sendMessage() {
    const userMessageInput = document.getElementById('user-message');
    const userMessage = userMessageInput.value.trim();
    
    if (!userMessage) return;
    
    addMessage('User', userMessage);
    userMessageInput.value = '';

    try {
        const response = await fetch(`/v1/chat/${currentPdfId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: userMessage })
        });

        if (!response.ok) {
            throw new Error('Chat request failed');
        }

        const reader = response.body.getReader();
        let botMessage = '';
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            botMessage += new TextDecoder().decode(value);
            addMessage('Bot', botMessage, true);
        }
    } catch (error) {
        console.error('Error:', error);
        addMessage('System', 'An error occurred while processing your message');
    }
}

function addMessage(sender, message, isUpdate = false) {
    const chatMessages = document.getElementById('chat-messages');
    
    if (isUpdate) {
        const lastMessage = chatMessages.lastElementChild;
        if (lastMessage && lastMessage.classList.contains('bot-message')) {
            lastMessage.textContent = message;
            return;
        }
    }
    
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', sender.toLowerCase() + '-message');
    messageElement.textContent = message;
    
    chatMessages.appendChild(messageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}