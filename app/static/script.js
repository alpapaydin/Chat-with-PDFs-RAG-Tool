let currentChatId = null;
let authToken = null;

window.onload = function() {
    checkSession();
    document.getElementById('login-button').addEventListener('click', login);
    document.getElementById('register-button').addEventListener('click', register);
    document.getElementById('logout-button').addEventListener('click', logout);
    document.getElementById('upload-button').addEventListener('click', uploadPDFs);
    document.getElementById('start-new-chat-button').addEventListener('click', startNewChat);
};

async function checkSession() {
    authToken = localStorage.getItem('authToken');
    if (authToken) {
        try {
            const response = await fetch('/v1/auth/me', {
                headers: {
                    'Authorization': `Bearer ${authToken}`
                }
            });
            if (response.ok) {
                const userData = await response.json();
                updateUIForLoggedInUser(userData.username);
            } else {
                updateUIForLoggedOutUser();
            }
        } catch (error) {
            console.error('Error checking session:', error);
            updateUIForLoggedOutUser();
        }
    } else {
        updateUIForLoggedOutUser();
    }
    await loadExistingChats();
}

async function login() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const authMessage = document.getElementById('auth-message');

    try {
        const response = await fetch('/v1/auth/token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                'username': username,
                'password': password,
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Login failed');
        }

        const data = await response.json();
        authToken = data.access_token;
        localStorage.setItem('authToken', authToken);
        
        updateUIForLoggedInUser(username);
        await loadExistingChats();
    } catch (error) {
        console.error('Login error:', error);
        authMessage.textContent = 'Login failed: ' + error.message;
        authMessage.style.color = 'red';
    }
}

function logout() {
    localStorage.removeItem('authToken');
    authToken = null;
    currentChatId = null;
    updateUIForLoggedOutUser();
    loadExistingChats();
}

function updateUIForLoggedInUser(username) {
    document.getElementById('auth-message').textContent = `Logged in as ${username}`;
    document.getElementById('auth-message').style.color = 'green';
    document.getElementById('login-button').style.display = 'none';
    document.getElementById('register-button').style.display = 'none';
    document.getElementById('username').style.display = 'none';
    document.getElementById('password').style.display = 'none';
    document.getElementById('logout-button').style.display = 'inline-block';
    document.getElementById('pdf-upload').style.display = 'block';
    document.getElementById('existing-chats').style.display = 'block';
    document.getElementById('chat-interface').style.display = 'none';
}

function updateUIForLoggedOutUser() {
    document.getElementById('auth-message').textContent = '';
    document.getElementById('login-button').style.display = 'inline-block';
    document.getElementById('register-button').style.display = 'inline-block';
    document.getElementById('username').style.display = 'inline-block';
    document.getElementById('password').style.display = 'inline-block';
    document.getElementById('logout-button').style.display = 'none';
    document.getElementById('pdf-upload').style.display = 'block';
    document.getElementById('existing-chats').style.display = 'block';
    document.getElementById('chat-interface').style.display = 'none';
}

async function loadExistingChats() {
    try {
        const headers = authToken ? { 'Authorization': `Bearer ${authToken}` } : {};
        const response = await fetch('/v1/chats', { headers });
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


async function register() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const authMessage = document.getElementById('auth-message');

    try {
        const response = await fetch('/v1/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            if (errorData.detail && Array.isArray(errorData.detail)) {
                // Handle validation errors
                const errorMessages = errorData.detail.map(error => `${error.loc.join('.')} : ${error.msg}`);
                throw new Error(errorMessages.join('\n'));
            } else {
                throw new Error(errorData.detail || 'Registration failed');
            }
        }

        const data = await response.json();
        authMessage.textContent = 'Registered successfully. Please log in.';
        authMessage.style.color = 'green';
    } catch (error) {
        console.error('Registration error:', error);
        authMessage.textContent = 'Registration failed: ' + error.message;
        authMessage.style.color = 'red';
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
        //document.getElementById('pdf-upload').style.display = 'none';
        document.getElementById('chat-interface').style.display = 'block';
        document.getElementById('chat-messages').innerHTML = '';
        document.getElementById('current-chat-id').textContent = currentChatId;
        fileInput.value = null
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

    const headers = {};
    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }

    const response = await fetch('/v1/pdf', {
        method: 'POST',
        headers: headers,
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
    //document.getElementById('pdf-upload').style.display = 'none';
    document.getElementById('chat-interface').style.display = 'block';
    document.getElementById('current-chat-id').textContent = currentChatId;
    document.getElementById('chat-messages').innerHTML = '';
    await loadChatPDFs(currentChatId);
    await loadChatHistory(currentChatId);
    addMessage('System', 'Chat loaded. You can now ask questions about the PDFs in this chat.');
}

async function loadChatHistory(chatId) {
    try {
        const headers = authToken ? { 'Authorization': `Bearer ${authToken}` } : {};
        const response = await fetch(`/v1/chat/${chatId}/messages`, { headers });
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
        const headers = authToken ? { 'Authorization': `Bearer ${authToken}` } : {};
        const response = await fetch(`/v1/chat/${chatId}/pdfs`, { headers });
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
        fileInput.value = null
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
        const headers = {
            'Content-Type': 'application/json',
        };
        if (authToken) {
            headers['Authorization'] = `Bearer ${authToken}`;
        }
        
        const response = await fetch(`/v1/chat/${currentChatId}`, {
            method: 'POST',
            headers: headers,
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