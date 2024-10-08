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
    const uploadButton = document.getElementById('upload-button');
    uploadButton.disabled = true;
    
    const fileInput = document.getElementById('pdf-files');
    const files = fileInput.files;
    if (files.length === 0) {
        alert('Please select at least one PDF file');
        uploadButton.disabled = false;
        return;
    }

    let successfulUploads = 0;
    for (let i = 0; i < files.length; i++) {
        try {
            await uploadSinglePDF(files[i]);
            successfulUploads++;
        } catch (error) {
            console.error('Error uploading file:', error);
            alert(`Error uploading ${files[i].name}: ${error.message}`);
        }
    }

    if (successfulUploads > 0) {
        document.getElementById('pdf-upload').style.display = 'none';
        document.getElementById('chat-interface').style.display = 'block';
        document.getElementById('current-chat-id').textContent = currentChatId;
        loadChatPDFs(currentChatId);
        addMessage('System', `${successfulUploads} PDF(s) uploaded successfully. You can now ask questions about them.`);
    } else {
        alert('No PDFs were successfully uploaded.');
    }
    await loadExistingChats();
    uploadButton.disabled = false;
}

async function uploadSinglePDF(file, existingChatId = null) {
    const formData = new FormData();
    formData.append('file', file);
    if (existingChatId) {
        formData.append('chat_id', existingChatId);
    }

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
}

async function loadChat(chatId) {
    currentChatId = chatId;
    document.getElementById('pdf-upload').style.display = 'none';
    document.getElementById('chat-interface').style.display = 'block';
    document.getElementById('current-chat-id').textContent = currentChatId;
    document.getElementById('chat-messages').innerHTML = '';
    await loadChatPDFs(currentChatId);
    await loadChatHistory(currentChatId);
    addMessage('System', 'Chat loaded. You can now ask questions about the PDFs in this chat.');
}

async function loadChatHistory(chatId) {
    try {
        const response = await fetch(`/v1/chat/${chatId}/messages`);
        const messages = await response.json();
        const chatMessages = document.getElementById('chat-messages');
        chatMessages.innerHTML = '';
        messages.forEach(msg => {
            addMessage(msg.is_user ? 'User' : 'Bot', msg.content);
        });
    } catch (error) {
        console.error('Error loading chat history:', error);
    }
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
    const addButton = document.getElementById('add-pdf-button');
    addButton.disabled = true;
    
    const fileInput = document.getElementById('additional-pdf');
    const file = fileInput.files[0];
    if (!file) {
        alert('Please select a PDF file');
        addButton.disabled = false;
        return;
    }

    try {
        await uploadSinglePDF(file, currentChatId);
        await loadChatPDFs(currentChatId);
        addMessage('System', 'Additional PDF uploaded successfully.');
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while uploading the additional PDF: ' + error.message);
    }

    addButton.disabled = false;
}

async function sendMessage() {
    const sendButton = document.getElementById('send-button');
    const userMessageInput = document.getElementById('user-message');
    const userMessage = userMessageInput.value.trim();
    
    if (!userMessage) return;
    
    sendButton.disabled = true;
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

    sendButton.disabled = false;
}

function addMessage(sender, message, isUpdate = false) {
    const chatMessages = document.getElementById('chat-messages');
    
    if (isUpdate) {
        const lastMessage = chatMessages.lastElementChild;
        if (lastMessage && lastMessage.classList.contains('bot-message')) {
            lastMessage.innerHTML = formatMessage(message);
            return;
        }
    }
    
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', sender.toLowerCase() + '-message');
    messageElement.innerHTML = formatMessage(message);
    
    chatMessages.appendChild(messageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function formatMessage(message) {
    const [answer, sources] = message.split("Sources:");
    let formattedMessage = `<div>${answer.replace("Answer:", "").trim()}</div>`;
    if (sources) {
        const cleanedSources = sources.replace(/\n/g, ' ').replace(/\s\s+/g, ' ').trim();
        const sourceEntries = cleanedSources.split(/(?=\d\.\s)/);
        const formattedSources = sourceEntries.map(source => 
            `<div style="font-size: x-small; margin-top: 4px;">${source.trim()}</div>`
        ).join('');
        formattedMessage += formattedSources;
    }
    return formattedMessage;
}

// Load existing chats when the page loads
window.onload = loadExistingChats;