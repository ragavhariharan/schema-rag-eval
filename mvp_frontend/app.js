const chatForm = document.getElementById('chatForm');
const userInput = document.getElementById('userInput');
const chatHistory = document.getElementById('chatHistory');
const sendBtn = document.getElementById('sendBtn');

// Configure Marked to use Highlight.js
marked.setOptions({
    highlight: function(code, lang) {
        if (lang && hljs.getLanguage(lang)) {
            return hljs.highlight(code, { language: lang }).value;
        } else {
            return hljs.highlightAuto(code).value;
        }
    }
});

// Conversation history (prior turns) sent with each request so the agent can
// resolve follow-ups ("its weight") and clarification answers. Capped to keep
// the payload small.
const conversation = [];
const MAX_TURNS = 12;

function setInput(text) {
    userInput.value = text;
    userInput.focus();
}

function scrollToBottom() {
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

function createTypingIndicator() {
    const div = document.createElement('div');
    div.className = 'message assistant-message typing-msg';
    div.innerHTML = `
        <div class="avatar assistant-avatar">AI</div>
        <div class="message-content" style="padding: 12px 20px;">
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
    `;
    return div;
}

function toggleAccordion(header) {
    const content = header.nextElementSibling;
    content.classList.toggle('open');
    header.querySelector('.icon').textContent = content.classList.contains('open') ? '▼' : '▶';
}

async function handleSubmit(e) {
    e.preventDefault();
    const query = userInput.value.trim();
    if (!query) return;

    // 1. Add User Message
    userInput.value = '';
    const userMsg = document.createElement('div');
    userMsg.className = 'message user-message';
    userMsg.innerHTML = `
        <div class="avatar user-avatar">You</div>
        <div class="message-content">${query}</div>
    `;
    chatHistory.appendChild(userMsg);
    scrollToBottom();

    // 2. Add Loading Indicator
    const typingIndicator = createTypingIndicator();
    chatHistory.appendChild(typingIndicator);
    scrollToBottom();
    
    // Disable input
    userInput.disabled = true;
    sendBtn.disabled = true;

    try {
        // 3. Call FastAPI Backend
        const response = await fetch('http://127.0.0.1:8000/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, history: conversation.slice(-MAX_TURNS) })
        });

        const data = await response.json();
        
        // Remove typing indicator
        chatHistory.removeChild(typingIndicator);

        if (!response.ok) {
            throw new Error(data.detail || 'API Error');
        }

        // 4. Render AI Response
        const aiMsg = document.createElement('div');
        aiMsg.className = 'message assistant-message';
        
        let sqlHtml = '';
        if (data.sql) {
            const sqlCode = hljs.highlight(data.sql, {language: 'sql'}).value;
            sqlHtml = `
                <div class="dev-accordion">
                    <div class="accordion-header" onclick="toggleAccordion(this)">
                        <span><span style="color:#38bdf8;">⚡</span> View Generated SQL</span>
                        <span class="icon">▶</span>
                    </div>
                    <div class="accordion-content">
                        <pre><code class="hljs language-sql">${sqlCode}</code></pre>
                    </div>
                </div>
            `;
        }

        aiMsg.innerHTML = `
            <div class="avatar assistant-avatar">AI</div>
            <div class="message-content">
                ${marked.parse(data.response)}
                ${sqlHtml}
            </div>
        `;
        
        chatHistory.appendChild(aiMsg);

        // Record this turn so follow-ups and clarification answers have context.
        conversation.push({ role: 'user', content: query });
        conversation.push({ role: 'assistant', content: data.response });

    } catch (error) {
        chatHistory.removeChild(typingIndicator);
        const errorMsg = document.createElement('div');
        errorMsg.className = 'message assistant-message';
        errorMsg.innerHTML = `
            <div class="avatar assistant-avatar" style="border-color: #ef4444; color: #ef4444;">!</div>
            <div class="message-content" style="border-color: rgba(239, 68, 68, 0.2); background: rgba(239, 68, 68, 0.05);">
                <strong>System Error:</strong> ${error.message}
            </div>
        `;
        chatHistory.appendChild(errorMsg);
    } finally {
        userInput.disabled = false;
        sendBtn.disabled = false;
        userInput.focus();
        scrollToBottom();
    }
}

chatForm.addEventListener('submit', handleSubmit);
