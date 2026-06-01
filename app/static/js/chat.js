// app/static/js/chat.js

const API_BASE = '/api';

const lang = document.documentElement.getAttribute('data-lang') || 'ar';

let currentSessionId = null;
let chatHistory = []; // To store history for persistence
let currentTranscript = []; // Transcript recorder for snapshots (Snapshot)

const startScreen = document.getElementById('startScreen');
const chatInterface = document.getElementById('chatInterface');
const startChatBtn = document.getElementById('startChatBtn');
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');

// Helper to save state to sessionStorage
function saveState() {
    sessionStorage.setItem('aqar_session_id', currentSessionId);
    sessionStorage.setItem('aqar_chat_history', JSON.stringify(chatHistory));
}

// Append message bubble - fixed spacing & visibility
function appendMessage(text, isBot = false, isRestoring = false) {
    if (!text || text.trim() === '') return;

    const div = document.createElement('div');
    div.className = `flex ${isBot ? 'justify-start' : 'justify-end'} max-w-[80%] mb-4`;

    const bubble = document.createElement('div');
    bubble.className = `message-bubble px-5 py-3 rounded-2xl shadow-sm text-base leading-relaxed whitespace-pre-wrap break-words
                        ${isBot ? 'bg-white border border-gray-200 text-gray-900' : 'bg-aqar-green text-white'}`;
    bubble.textContent = text.trim();

    div.appendChild(bubble);
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    if (!isRestoring) {
        chatHistory.push({ type: 'message', text, isBot });
        saveState();
        // Record for completed-chat transcript
        currentTranscript.push({ sender: isBot ? 'bot' : 'user', text: text.trim() });
    }
}


// Updated appendPropertyCard function for chat.js

function appendPropertyCard(prop, isBest = false, isRestoring = false) {
    const card = document.createElement('div');
    card.className = `bg-white rounded-lg shadow-sm p-4 border-l-4 ${isBest ? 'border-aqar-green' : 'border-gray-300'} mb-4 cursor-pointer hover:shadow-md transition flex items-start gap-4`;

    // Make whole card clickable - navigate to property page with API fetch
    card.onclick = () => {
        const token = localStorage.getItem('token');

        if (!token) {
            appendMessage('يرجى تسجيل الدخول أولاً', true);
            window.location.href = '/login';
            return;
        }

        // Navigate to property page with property ID as query parameter
        window.location.href = `/property?id=${prop.id}`;
    };

    card.innerHTML = `
      ${prop.image_url ? `
        <img src="${prop.image_url}" 
             class="w-32 h-24 object-cover rounded-md flex-shrink-0" 
             alt="${prop.title}">
      ` : `
        <div class="w-32 h-24 bg-gray-200 rounded-md flex items-center justify-center flex-shrink-0">
          <span class="text-gray-500 text-sm">No image</span>
        </div>
      `}
      <div class="flex-1">
        <h3 class="font-medium text-base mb-1">${prop.title}</h3>
        <div class="text-sm font-medium text-gray-600 text-right">
          Match: ${Math.round(prop.match_score || 0)}%
        </div>
      </div>
    `;

    chatMessages.appendChild(card);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    if (!isRestoring) {
        chatHistory.push({ type: 'property', prop, isBest });
        saveState();
        // Record property snapshot for history
        currentTranscript.push({ 
            sender: 'property', 
            text: JSON.stringify({ prop, isBest }) 
        });
    }
}

// Start chat
startChatBtn.addEventListener('click', async () => {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/login';
        return;
    }

    startChatBtn.disabled = true;
    startChatBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> ...';

    try {
        const res = await fetch(`${API_BASE}/chatbot/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            }
        });

        const data = await res.json();

        if (data.success) {
            currentSessionId = data.session_id;
            startScreen.style.display = 'none';
            chatInterface.classList.remove('hidden');
            const firstQuestion = lang === 'ar'
                ? 'ما هي ميزانيتك؟ يرجى إدخال الحد الأدنى والأقصى بالريال السعودي (مثال: من 400000 إلى 800000)'
                : (data.first_question || data.message);
            appendMessage(firstQuestion, true);
        } else {
            appendMessage(data.message || 'Error starting chat', true);
            startChatBtn.disabled = false;
            startChatBtn.innerHTML = 'Start Chat';
        }
    } catch (err) {
        appendMessage('Failed to connect', true);
        startChatBtn.disabled = false;
        startChatBtn.innerHTML = 'Start Chat';
    }
});

// Send message
async function sendMessage() {
    if (!currentSessionId) return;

    const token = localStorage.getItem('token');
    if (!token) {
        appendMessage('Please log in to continue', true);
        return;
    }

    const message = messageInput.value.trim();
    if (!message) return;

    appendMessage(message, false);

    messageInput.value = '';

    try {
        const res = await fetch(`${API_BASE}/chatbot/message`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ session_id: currentSessionId, message, lang })
        });

        const data = await res.json();

        if (data.success) {
            appendMessage(data.next_question || data.message, true);

            if (data.preferences_complete) {
                appendMessage('Loading recommendations...', true);
                const recRes = await fetch(`${API_BASE}/property/recommendations/${currentSessionId}`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                const recData = await recRes.json();

                if (recData.success && recData.best_match) {
                    if (recData.low_confidence) {
                        appendMessage(lang === 'ar'
                            ? 'لم أجد تطابقاً دقيقاً، لكن هذه أقرب النتائج المتاحة:'
                            : 'No exact matches found, but here are the closest available properties:', true);
                    } else {
                        appendMessage(lang === 'ar'
                            ? 'إليك أفضل العقارات المطابقة:'
                            : 'Here are the best matches I found:', true);
                    }
                    appendPropertyCard(recData.best_match, true);
                    recData.alternatives.forEach(p => appendPropertyCard(p));
                } else {
                    appendMessage(lang === 'ar'
                        ? 'لا توجد عقارات متاحة حالياً'
                        : 'No matching properties found', true);
                }

                // SAVE SNAPSHOT (Fire-and-forget)
                saveTranscript(currentSessionId, currentTranscript);
            }
        } else {
            appendMessage(data.message || 'Error processing message', true);
        }
    } catch (err) {
        appendMessage('Failed to send message', true);
    }
}

// Event listeners
sendBtn.addEventListener('click', sendMessage);
messageInput.addEventListener('keypress', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// NEW CHAT FUNCTIONALITY
const newChatBtn = document.getElementById('newChatBtn');

if (newChatBtn) {
    newChatBtn.addEventListener('click', async () => {
        const token = localStorage.getItem('token');
        if (!token) {
            window.location.href = '/login';
            return;
        }

        // UI Loading State
        const originalText = newChatBtn.innerHTML;
        newChatBtn.disabled = true;
        newChatBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> ...';

        try {
            const res = await fetch(`${API_BASE}/chatbot/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                }
            });

            const data = await res.json();

            if (data.success) {
                // 1. Reset Session
                currentSessionId = data.session_id;

                // 2. Clear old messages
                chatMessages.innerHTML = '';
                chatHistory = [];
                currentTranscript = [];
                sessionStorage.removeItem('aqar_session_id');
                sessionStorage.removeItem('aqar_chat_history');

                // 3. Append first message
                const firstQuestion = lang === 'ar'
                    ? 'ما هي ميزانيتك؟ يرجى إدخال الحد الأدنى والأقصى بالريال السعودي (مثال: من 400000 إلى 800000)'
                    : (data.first_question || data.message);
                appendMessage(firstQuestion, true);
            } else {
                appendMessage(data.message || 'Error starting new chat', true);
            }
        } catch (err) {
            appendMessage('Failed to connect', true);
        } finally {
            newChatBtn.disabled = false;
            newChatBtn.innerHTML = originalText;
        }
    });
}

// Restore session on load
window.addEventListener('load', () => {
    const savedId = sessionStorage.getItem('aqar_session_id');
    const savedHistory = sessionStorage.getItem('aqar_chat_history');

    if (savedId && savedHistory) {
        currentSessionId = savedId;
        chatHistory = JSON.parse(savedHistory);

        // Hide start screen and show chat
        startScreen.style.display = 'none';
        chatInterface.classList.remove('hidden');

        // Render history
        chatHistory.forEach(item => {
            if (item.type === 'message') {
                appendMessage(item.text, item.isBot, true);
            } else if (item.type === 'property') {
                appendPropertyCard(item.prop, item.isBest, true);
            }
        });
    }
});

// ============================================================
// SAVE TRANSCRIPT — fire-and-forget, safe, does not affect chat
// ============================================================
async function saveTranscript(sessionId, transcript) {
    if (!sessionId || !transcript || transcript.length === 0) return;

    const token = localStorage.getItem('token');
    if (!token) return;

    try {
        await fetch(`${API_BASE}/chatbot/save-transcript`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ session_id: sessionId, transcript })
        });
        // We intentionally ignore the response — saving is best-effort
    } catch (err) {
        // Silent fail — the chat experience is unaffected
        console.warn('Transcript save failed silently:', err);
    }
}
