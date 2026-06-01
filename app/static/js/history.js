// app/static/js/history.js

const API_BASE = '/api';
const lang = document.documentElement.getAttribute('data-lang') || 'ar';

const sessionList = document.getElementById('sessionList');
const listLoader = document.getElementById('listLoader');
const noSessions = document.getElementById('noSessions');
const historyPlaceholder = document.getElementById('historyPlaceholder');
const historyInterface = document.getElementById('historyInterface');
const historyMessages = document.getElementById('historyMessages');
const historyTitle = document.getElementById('historyTitle');
const historyDate = document.getElementById('historyDate');

let allSessions = [];

// Load sessions on page start
async function loadSessions() {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/login';
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/chatbot/sessions`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();

        listLoader.classList.add('hidden');

        if (data.success && data.sessions.length > 0) {
            allSessions = data.sessions;
            renderSessionList();
        } else {
            noSessions.classList.remove('hidden');
        }
    } catch (err) {
        console.error('Failed to load sessions:', err);
        listLoader.innerHTML = '<p class="text-red-500 p-4 text-center">Failed to load history</p>';
    }
}

function renderSessionList() {
    sessionList.innerHTML = '';
    
    allSessions.forEach(session => {
        const div = document.createElement('div');
        div.className = 'session-item';
        div.dataset.id = session.session_id;
        
        // Create a summary title based on preferences
        const prefs = session.preferences;
        let title = '';
        if (prefs.property_type && prefs.location) {
            title = lang === 'ar' 
                ? `${prefs.property_type} في ${prefs.location}`
                : `${prefs.property_type} in ${prefs.location}`;
        } else {
            title = lang === 'ar' ? `محادثة #${session.session_id}` : `Chat #${session.session_id}`;
        }

        div.innerHTML = `
            <div class="font-bold text-aqar-dark mb-1">${title}</div>
            <div class="text-xs text-gray-500 flex items-center gap-1">
                <i class="far fa-clock"></i>
                ${session.created_at}
            </div>
        `;

        div.onclick = () => selectSession(session.session_id);
        sessionList.appendChild(div);
    });
}

function selectSession(sessionId) {
    // Highlight active item
    document.querySelectorAll('.session-item').forEach(item => {
        item.classList.toggle('active', item.dataset.id == sessionId);
    });

    const session = allSessions.find(s => s.session_id == sessionId);
    if (!session) return;

    // UI transitions
    historyPlaceholder.classList.add('hidden');
    historyInterface.classList.remove('hidden');
    
    // Set headers
    const prefs = session.preferences;
    historyTitle.textContent = lang === 'ar' 
        ? `${prefs.property_type || ''} في ${prefs.location || ''}`
        : `${prefs.property_type || ''} in ${prefs.location || ''}`;
    historyDate.textContent = session.created_at;

    // Clear and render messages
    historyMessages.innerHTML = '';
    
    if (session.messages && session.messages.length > 0) {
        session.messages.forEach(msg => {
            if (msg.sender === 'property') {
                try {
                    const data = JSON.parse(msg.text);
                    appendHistoryPropertyCard(data.prop, data.isBest);
                } catch (e) {
                    console.error('Failed to parse property snapshot:', e);
                }
            } else {
                appendHistoryMessage(msg.text, msg.sender === 'bot');
            }
        });
    } else {
        const info = document.createElement('div');
        info.className = 'text-center text-gray-400 my-8 italic';
        info.textContent = lang === 'ar' ? 'لا يوجد سجل رسائل لهذه المحادثة' : 'No message history for this chat';
        historyMessages.appendChild(info);
    }
    
    historyMessages.scrollTop = 0;
}

function appendHistoryMessage(text, isBot = false) {
    const div = document.createElement('div');
    div.className = `flex ${isBot ? 'justify-start' : 'justify-end'} w-full mb-4`;

    const bubble = document.createElement('div');
    bubble.className = `px-5 py-3 rounded-2xl shadow-sm text-base leading-relaxed whitespace-pre-wrap break-words max-w-[80%]
                        ${isBot ? 'bg-white border border-gray-200 text-gray-900' : 'bg-aqar-green text-white'}`;
    bubble.textContent = text.trim();

    div.appendChild(bubble);
    historyMessages.appendChild(div);
}

function appendHistoryPropertyCard(prop, isBest = false) {
    const card = document.createElement('div');
    card.className = `bg-white rounded-lg shadow-sm p-4 border-l-4 ${isBest ? 'border-aqar-green' : 'border-gray-300'} mb-4 cursor-pointer hover:shadow-md transition flex items-start gap-4 w-full max-w-lg mx-auto`;

    card.onclick = () => {
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
      <div class="flex-1 text-right">
        <h3 class="font-medium text-base mb-1">${prop.title}</h3>
        <div class="text-sm font-medium text-gray-600">
          Match: ${Math.round(prop.match_score || 0)}%
        </div>
      </div>
    `;

    historyMessages.appendChild(card);
}

// Initialize
document.addEventListener('DOMContentLoaded', loadSessions);
