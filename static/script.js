const API_URL = 'http://localhost:5000/api/chat';

const chatMessages = document.getElementById('chatMessages');
const userInput = document.getElementById('userInput');
const sendButton = document.getElementById('sendButton');

// Allow sending message with Enter key
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

function convertUrlsToLinks(text) {
    // URL regex pattern
    const urlPattern = /(https?:\/\/[^\s]+)/g;
    const parts = text.split(urlPattern);
    
    const fragment = document.createDocumentFragment();
    const urlTestPattern = /^https?:\/\//;
    
    parts.forEach((part, index) => {
        if (urlTestPattern.test(part)) {
            // It's a URL, create a link
            const link = document.createElement('a');
            link.href = part;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            link.textContent = part;
            link.className = 'inline-link';
            fragment.appendChild(link);
        } else if (part.trim()) {
            // It's regular text
            const textNode = document.createTextNode(part);
            fragment.appendChild(textNode);
        }
    });
    
    return fragment;
}

function addMessage(content, isUser = false, sourceUrl = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    if (typeof content === 'string') {
        // Split content by newlines and create paragraphs
        const paragraphs = content.split('\n').filter(p => p.trim());
        paragraphs.forEach((para, index) => {
            const p = document.createElement('p');
            if (para.includes('Note:') || para.toLowerCase().includes('disclaimer')) {
                p.className = 'disclaimer';
            }
            
            // Check if paragraph contains "Source:" and handle it separately
            if (para.includes('Source:') && sourceUrl) {
                // Don't add this paragraph as it will be handled below
                return;
            }
            
            // Convert URLs in text to clickable links
            const textWithLinks = convertUrlsToLinks(para);
            p.appendChild(textWithLinks);
            contentDiv.appendChild(p);
        });
    } else {
        contentDiv.appendChild(content);
    }
    
    // Add source link if provided
    if (sourceUrl && !isUser) {
        const sourceDiv = document.createElement('div');
        sourceDiv.className = 'source-link';
        const link = document.createElement('a');
        link.href = sourceUrl;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        link.textContent = sourceUrl;
        link.title = 'Open source link in new tab';
        sourceDiv.appendChild(link);
        contentDiv.appendChild(sourceDiv);
    }
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageDiv;
}

function addTypingIndicator() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message';
    messageDiv.id = 'typingIndicator';
    
    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing-indicator';
    typingDiv.innerHTML = '<span></span><span></span><span></span>';
    
    messageDiv.appendChild(typingDiv);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageDiv;
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.remove();
    }
}

async function sendMessage() {
    const query = userInput.value.trim();
    
    if (!query) {
        return;
    }
    
    // Disable input and button
    userInput.disabled = true;
    sendButton.disabled = true;
    
    // Add user message
    addMessage(query, true);
    
    // Clear input
    userInput.value = '';
    
    // Add typing indicator
    addTypingIndicator();
    
    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query })
        });
        
        const data = await response.json();
        
        // Remove typing indicator
        removeTypingIndicator();
        
        if (data.error) {
            addMessage(`Sorry, I encountered an error: ${data.error}`, false);
        } else {
            addMessage(data.answer, false, data.source_url);
        }
        
    } catch (error) {
        // Remove typing indicator
        removeTypingIndicator();
        
        console.error('Error:', error);
        addMessage("Sorry, I'm having trouble connecting to the server. Please make sure the backend is running.", false);
    } finally {
        // Re-enable input and button
        userInput.disabled = false;
        sendButton.disabled = false;
        userInput.focus();
    }
}

// Focus input on load
window.addEventListener('load', () => {
    userInput.focus();
});

