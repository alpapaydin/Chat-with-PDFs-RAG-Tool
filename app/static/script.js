let currentChatId = null;

async function loadExistingChats() {
    try {
        const response = await fetch('/v1/chats');
        const chats = await response.json();
        const chatList = document.getElementById('chat-list');
        chatList.innerHTML = '';
        chats.forEach(chat => {
            const li = document.createElement('li');
            li.textContent = `Chat ${chat.id}`;
            li.onclick = () => loadChat(chat.id);
            chatList.appendChild(li);
        });
    } catch (error) {
        console.error('Error loading chats:', error);
    }
}

async function uploadPDFs() {
    const fileInput = document.getElementById('pdf-files');
    const files = fileInput.files;
    if (files.length === 0) {
        alert('Please select at least one PDF file');
        return;
    }

    for (let i = 0; i < files.length; i++) {
        await uploadSinglePDF(files[i]);
    }

    document.getElementById('pdf-upload').style.display = 'none';
    document.getElementById('chat-interface').style.display = 'block';
    document.getElementById('current-chat-id').textContent = currentChatId;
    
    loadChatPDFs(currentChatId);
    addMessage('System', 'PDFs uploaded successfully. You can now ask questions about them.');
}

async function uploadSinglePDF(file, existingChatId = null) {
    const formData = new FormData();
    formData.append('file', file);
    if (existingChatId) {
        formData.append('chat_id', existingChatId);
    }

    try {
        const response = await fetch('/v1/pdf', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'PDF upload failed');
        }

        const data = await response.json();
        currentChatId = data.chat_id;
        return data;
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while uploading the PDF: ' + error.message);
    }
}

async function loadChat(chatId) {
    currentChatId = chatId;
    document.getElementById('pdf-upload').style.display = 'none';
    document.getElementById('chat-interface').style.display = 'block';
    document.getElementById('current-chat-id').textContent = currentChatId;
    document.getElementById('chat-messages').innerHTML = '';
    loadChatPDFs(currentChatId);
    addMessage('System', 'Chat loaded. You can now ask questions about the PDFs in this chat.');
}

async function loadChatPDFs(chatId) {
    try {
        const response = await fetch(`/v1/chat/${chatId}/pdfs`);
        const pdfs = await response.json();
        const pdfList = document.getElementById('chat-pdfs');
        pdfList.innerHTML = '';
        pdfs.forEach(pdf => {
            const li = document.createElement('li');
            li.textContent = pdf.filename;
            pdfList.appendChild(li);
        });
    } catch (error) {
        console.error('Error loading chat PDFs:', error);
    }
}

async function addPDFToChat() {
    const fileInput = document.getElementById('additional-pdf');
    const file = fileInput.files[0];
    if (!file) {
        alert('Please select a PDF file');
        return;
    }

    try {
        const data = await uploadSinglePDF(file, currentChatId);
        loadChatPDFs(currentChatId);
        addMessage('System', 'Additional PDF uploaded successfully.');
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while uploading the additional PDF: ' + error.message);
    }
}

async function sendMessage() {
    const userMessageInput = document.getElementById('user-message');
    const userMessage = userMessageInput.value.trim();
    
    if (!userMessage) return;
    
    addMessage('User', userMessage);
    userMessageInput.value = '';

    try {
        const response = await fetch(`/v1/chat/${currentChatId}`, {
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

// Load existing chats when the page loads
window.onload = loadExistingChats;