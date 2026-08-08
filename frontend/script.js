// API base URL - use relative path to work from any host
const API_URL = '/api';

// Global state
let currentSessionId = null;
let sessionInitialization = null;
let activeQueryController = null;
let conversationVersion = 0;
const THEME_STORAGE_KEY = 'course-assistant-theme';

// DOM elements
let chatMessages, chatInput, sendButton, totalCourses, courseTitles, themeToggle, newChatButton;

function getSavedTheme() {
    try {
        return localStorage.getItem(THEME_STORAGE_KEY);
    } catch (error) {
        return null;
    }
}

function saveTheme(theme) {
    try {
        localStorage.setItem(THEME_STORAGE_KEY, theme);
    } catch (error) {
        // Theme switching still works if storage is unavailable.
    }
}

function updateThemeControl(theme) {
    if (!themeToggle) return;

    const isLight = theme === 'light';
    const actionLabel = `Switch to ${isLight ? 'dark' : 'light'} theme`;
    themeToggle.setAttribute('aria-label', actionLabel);
    themeToggle.setAttribute('aria-pressed', String(isLight));
    themeToggle.setAttribute('title', actionLabel);
}

function applyTheme(theme, persist = false) {
    const nextTheme = theme === 'light' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', nextTheme);
    updateThemeControl(nextTheme);

    if (persist) saveTheme(nextTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    applyTheme(currentTheme === 'light' ? 'dark' : 'light', true);
}

// Restore the saved choice before the rest of the interface initializes.
applyTheme(getSavedTheme());

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Get DOM elements after page loads
    chatMessages = document.getElementById('chatMessages');
    chatInput = document.getElementById('chatInput');
    sendButton = document.getElementById('sendButton');
    totalCourses = document.getElementById('totalCourses');
    courseTitles = document.getElementById('courseTitles');
    themeToggle = document.getElementById('themeToggle');
    newChatButton = document.getElementById('newChatButton');
    updateThemeControl(document.documentElement.getAttribute('data-theme'));
    
    setupEventListeners();
    createNewSession();
    loadCourseStats();
});

// Event Listeners
function setupEventListeners() {
    themeToggle.addEventListener('click', toggleTheme);
    newChatButton.addEventListener('click', () => createNewSession());

    // Chat functionality
    sendButton.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
    
    
    // Suggested questions
    document.querySelectorAll('.suggested-item').forEach(button => {
        button.addEventListener('click', (e) => {
            const question = e.target.getAttribute('data-question');
            chatInput.value = question;
            sendMessage();
        });
    });
}


// Chat Functions
async function sendMessage() {
    const query = chatInput.value.trim();
    if (!query) return;

    if (sessionInitialization) await sessionInitialization;
    if (!currentSessionId) return;

    const requestVersion = conversationVersion;
    const queryController = new AbortController();
    activeQueryController = queryController;

    // Disable input
    chatInput.value = '';
    chatInput.disabled = true;
    sendButton.disabled = true;

    // Add user message
    addMessage(query, 'user');

    // Add loading message - create a unique container for it
    const loadingMessage = createLoadingMessage();
    chatMessages.appendChild(loadingMessage);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        const response = await fetch(`${API_URL}/query`, {
            method: 'POST',
            signal: queryController.signal,
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                session_id: currentSessionId
            })
        });

        if (!response.ok) throw new Error('Query failed');

        const data = await response.json();

        if (requestVersion !== conversationVersion) return;

        // Replace loading message with response
        loadingMessage.remove();
        addMessage(data.answer, 'assistant', data.sources);

    } catch (error) {
        if (error.name === 'AbortError' || requestVersion !== conversationVersion) return;

        // Replace loading message with error
        loadingMessage.remove();
        addMessage(`Error: ${error.message}`, 'assistant');
    } finally {
        if (activeQueryController === queryController) {
            activeQueryController = null;
        }

        if (requestVersion === conversationVersion) {
            setChatControlsDisabled(false);
            chatInput.focus();
        }
    }
}

function createLoadingMessage() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="loading">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    return messageDiv;
}

function parseSource(source) {
    const container = document.createElement('div');
    container.innerHTML = source;

    const sourceLink = container.querySelector('a');
    const label = (sourceLink || container).textContent.trim();
    const lessonMatch = label.match(/\s+-\s+(Lesson\s+\d+)\s*$/i);
    let href = null;

    if (sourceLink) {
        try {
            const sourceUrl = new URL(sourceLink.getAttribute('href'), window.location.href);
            if (sourceUrl.protocol === 'http:' || sourceUrl.protocol === 'https:') {
                href = sourceUrl.href;
            }
        } catch (error) {
            // Keep malformed source URLs as plain text.
        }
    }

    return {
        title: lessonMatch ? label.slice(0, lessonMatch.index).trim() : label,
        lesson: lessonMatch ? lessonMatch[1] : null,
        href
    };
}

function createSourcesSection(sources) {
    const uniqueSources = [];
    const seenSources = new Set();

    sources.forEach(source => {
        const parsedSource = parseSource(source);
        const sourceKey = `${parsedSource.href || ''}|${parsedSource.title}|${parsedSource.lesson || ''}`;

        if (parsedSource.title && !seenSources.has(sourceKey)) {
            seenSources.add(sourceKey);
            uniqueSources.push(parsedSource);
        }
    });

    if (uniqueSources.length === 0) return null;

    const details = document.createElement('details');
    details.className = 'sources-collapsible';

    const summary = document.createElement('summary');
    summary.className = 'sources-header';
    summary.innerHTML = `
        <span class="sources-heading">
            <svg aria-hidden="true" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
            </svg>
            Sources
        </span>
        <span class="sources-count">${uniqueSources.length}</span>
    `;

    const content = document.createElement('div');
    content.className = 'sources-content';
    const list = document.createElement('ol');
    list.className = 'sources-list';

    uniqueSources.forEach((source, index) => {
        const item = document.createElement('li');
        item.className = 'source-item';

        const number = document.createElement('span');
        number.className = 'source-number';
        number.textContent = index + 1;
        number.setAttribute('aria-hidden', 'true');

        const label = document.createElement(source.href ? 'a' : 'span');
        label.className = source.href ? 'source-link' : 'source-label';

        if (source.href) {
            label.href = source.href;
            label.target = '_blank';
            label.rel = 'noopener noreferrer';
        }

        const title = document.createElement('span');
        title.className = 'source-title';
        title.textContent = source.title;
        label.appendChild(title);

        if (source.lesson) {
            const lesson = document.createElement('span');
            lesson.className = 'source-lesson';
            lesson.textContent = source.lesson;
            label.appendChild(lesson);
        }

        if (source.href) {
            const externalIcon = document.createElement('span');
            externalIcon.className = 'source-external-icon';
            externalIcon.setAttribute('aria-hidden', 'true');
            externalIcon.textContent = '↗';
            label.appendChild(externalIcon);
        }

        item.append(number, label);
        list.appendChild(item);
    });

    content.appendChild(list);
    details.append(summary, content);
    return details;
}

function addMessage(content, type, sources = null, isWelcome = false) {
    const messageId = Date.now();
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}${isWelcome ? ' welcome-message' : ''}`;
    messageDiv.id = `message-${messageId}`;
    
    // Convert markdown to HTML for assistant messages
    const displayContent = type === 'assistant' ? marked.parse(content) : escapeHtml(content);
    
    messageDiv.innerHTML = `<div class="message-content">${displayContent}</div>`;

    if (sources && sources.length > 0) {
        const sourcesSection = createSourcesSection(sources);
        if (sourcesSection) messageDiv.appendChild(sourcesSection);
    }

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageId;
}

// Helper function to escape HTML for user messages
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Removed removeMessage function - no longer needed since we handle loading differently

function setChatControlsDisabled(disabled) {
    chatInput.disabled = disabled;
    sendButton.disabled = disabled;
    newChatButton.disabled = disabled;
}

function resetConversationView() {
    chatInput.value = '';
    currentSessionId = null;
    chatMessages.innerHTML = '';
    addMessage('Welcome to the Course Materials Assistant! I can help you with questions about courses, lessons and specific content. What would you like to know?', 'assistant', null, true);
}

function createNewSession() {
    const previousSessionId = currentSessionId;
    const nextConversationVersion = ++conversationVersion;

    if (activeQueryController) {
        activeQueryController.abort();
        activeQueryController = null;
    }

    resetConversationView();
    setChatControlsDisabled(true);

    sessionInitialization = (async () => {
        try {
            if (previousSessionId) {
                const deleteResponse = await fetch(
                    `${API_URL}/sessions/${encodeURIComponent(previousSessionId)}`,
                    { method: 'DELETE' }
                );

                if (!deleteResponse.ok) throw new Error('Failed to clean up the previous session');
            }

            const createResponse = await fetch(`${API_URL}/sessions`, {
                method: 'POST'
            });

            if (!createResponse.ok) throw new Error('Failed to start a new session');

            const data = await createResponse.json();
            if (nextConversationVersion === conversationVersion) {
                currentSessionId = data.session_id;
            }
        } catch (error) {
            if (nextConversationVersion === conversationVersion) {
                addMessage(`Error: ${error.message}`, 'assistant');
            }
        } finally {
            if (nextConversationVersion === conversationVersion) {
                sessionInitialization = null;
                setChatControlsDisabled(false);
                chatInput.focus();
            }
        }
    })();

    return sessionInitialization;
}

// Load course statistics
async function loadCourseStats() {
    try {
        console.log('Loading course stats...');
        const response = await fetch(`${API_URL}/courses`);
        if (!response.ok) throw new Error('Failed to load course stats');
        
        const data = await response.json();
        console.log('Course data received:', data);
        
        // Update stats in UI
        if (totalCourses) {
            totalCourses.textContent = data.total_courses;
        }
        
        // Update course titles
        if (courseTitles) {
            if (data.course_titles && data.course_titles.length > 0) {
                courseTitles.innerHTML = data.course_titles
                    .map(title => `<div class="course-title-item">${title}</div>`)
                    .join('');
            } else {
                courseTitles.innerHTML = '<span class="no-courses">No courses available</span>';
            }
        }
        
    } catch (error) {
        console.error('Error loading course stats:', error);
        // Set default values on error
        if (totalCourses) {
            totalCourses.textContent = '0';
        }
        if (courseTitles) {
            courseTitles.innerHTML = '<span class="error">Failed to load courses</span>';
        }
    }
}
