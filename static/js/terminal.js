// BatChatBot Terminal Interface JavaScript
// Handles chat functionality, animations, and terminal effects

class BatTerminal {
    constructor() {
        this.chatArea = document.getElementById('chatArea');
        this.queryInput = document.getElementById('queryInput');
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.matrixBackground = document.getElementById('matrixBackground');
        this.newSessionBtn = document.getElementById('newSessionBtn');
        this.sessionStatus = document.getElementById('sessionStatus');
        
        this.currentSessionId = null;
        this.hasNumberedOptions = false;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.initMatrixBackground();
        this.hideLoadingScreen();
        this.focusInput();
        this.addBootSequence();
        this.updateSessionStatus(); // Load session status on startup
    }
    
    setupEventListeners() {
        // Enter key to send query
        this.queryInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendQuery();
            }
        });
        
        // New session button
        this.newSessionBtn.addEventListener('click', () => {
            this.startNewSession();
        });
        
        // Navigation hover effects
        document.querySelectorAll('.nav-command').forEach(cmd => {
            cmd.addEventListener('click', (e) => {
                this.addGlitchEffect(e.target);
            });
        });
        
        // Footer command effects
        document.querySelectorAll('.footer-command').forEach(cmd => {
            cmd.addEventListener('click', (e) => {
                this.addGlitchEffect(e.target);
            });
        });
    }
    
    hideLoadingScreen() {
        setTimeout(() => {
            if (this.loadingOverlay) {
                this.loadingOverlay.style.display = 'none';
            }
        }, 5000);
    }
    
    focusInput() {
        setTimeout(() => {
            this.queryInput.focus();
        }, 5500);
    }
    
    async startNewSession() {
        try {
            this.addGlitchEffect(this.newSessionBtn);
            this.typeMessage('system', '>>> Starting new conversation session...');
            
            const response = await fetch('/api/session/new', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin' // Include cookies for session management
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.currentSessionId = data.session_id;
                this.hasNumberedOptions = false;
                this.updateSessionStatus();
                
                // Clear chat area except welcome message
                const welcomeMsg = this.chatArea.querySelector('.welcome-message');
                this.chatArea.innerHTML = '';
                if (welcomeMsg) {
                    this.chatArea.appendChild(welcomeMsg);
                }
                
                this.typeMessage('system', '>>> New session started. Conversation history cleared.');
                this.typeMessage('system', '>>> Session ID: ' + data.session_id.substring(0, 8) + '...');
            } else {
                this.typeMessage('system', '>>> ERROR: Failed to start new session.');
            }
        } catch (error) {
            this.typeMessage('system', '>>> ERROR: Session creation failed.');
            console.error('New session error:', error);
        }
    }
    
    async updateSessionStatus() {
        try {
            const response = await fetch('/api/session/status');
            const data = await response.json();
            
            if (response.ok) {
                this.currentSessionId = data.session_id;
                this.hasNumberedOptions = data.has_numbered_options;
                this.sessionStatus.textContent = `Session: ${data.session_id.substring(0, 8)}... (${data.conversation_length} msgs)`;
            }
        } catch (error) {
            this.sessionStatus.textContent = 'Session: Error';
        }
    }
    
    addBootSequence() {
        setTimeout(() => {
            this.typeMessage('system', '>>> Establishing secure connection to BatComputer...');
            setTimeout(() => {
                this.typeMessage('system', '>>> Loading Gotham City database...');
                setTimeout(() => {
                    this.typeMessage('system', '>>> Encryption protocols active...');
                    setTimeout(() => {
                        this.typeMessage('system', '>>> Ready for queries. Welcome to the BatCave.');
                    }, 1000);
                }, 1000);
            }, 1000);
        }, 6000);
    }
    
    async sendQuery() {
        const query = this.queryInput.value.trim();
        if (!query) return;
        
        // Add user message
        this.addUserMessage(query);
        this.queryInput.value = '';
        
        // Add typing indicator
        const typingId = this.addTypingIndicator();
        
        try {
            // Send query to backend
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin', // Include cookies for session management
                body: JSON.stringify({ query: query })
            });
            
            const data = await response.json();
            
            // Remove typing indicator
            this.removeTypingIndicator(typingId);
            
            if (response.ok) {
                // Add bot response
                this.addBotResponse(data);
            } else {
                // Add error response
                this.addErrorResponse(data.response || 'Error processing query');
            }
            
        } catch (error) {
            this.removeTypingIndicator(typingId);
            this.addErrorResponse('Connection to BatComputer failed. Please try again.');
            console.error('Chat error:', error);
        }
        
        // Scroll to bottom
        this.scrollToBottom();
    }
    
    addUserMessage(query) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'user-message';
        messageDiv.innerHTML = `> ${this.escapeHtml(query)}`;
        this.chatArea.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    addBotResponse(data) {
        const responseDiv = document.createElement('div');
        responseDiv.className = 'bot-response';
        
        const infoDiv = document.createElement('div');
        infoDiv.className = 'query-info';
        infoDiv.innerHTML = `[${data.timestamp}] [Confidence: ${data.confidence}] [Type: ${data.query_type}] [Sources: ${data.source_entities}]`;
        
        this.chatArea.appendChild(infoDiv);
        this.chatArea.appendChild(responseDiv);
        
        // Update session state
        if (data.session_id) {
            this.currentSessionId = data.session_id;
        }
        
        if (data.has_numbered_options !== undefined) {
            this.hasNumberedOptions = data.has_numbered_options;
            
            // Update input placeholder based on numbered options
            if (this.hasNumberedOptions) {
                this.queryInput.placeholder = "Enter number (1-5) for selection or new question";
            } else {
                this.queryInput.placeholder = "Enter query (e.g., 'Who is Joker?') or number for selection";
            }
        }
        
        // Type out the response
        this.typeMessage('response', data.response, responseDiv);
        this.scrollToBottom();
        
        // Update session status after response
        setTimeout(() => {
            this.updateSessionStatus();
        }, 1000);
    }
    
    addErrorResponse(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'bot-response';
        errorDiv.style.color = '#FFFF00'; // Yellow for errors
        errorDiv.innerHTML = `>> ERROR: ${this.escapeHtml(message)}`;
        this.chatArea.appendChild(errorDiv);
        this.scrollToBottom();
    }
    
    addTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'bot-response typing-indicator';
        typingDiv.innerHTML = '>> BatComputer processing<span class="dots">...</span>';
        typingDiv.id = 'typing-' + Date.now();
        
        this.chatArea.appendChild(typingDiv);
        this.scrollToBottom();
        
        // Animate dots
        this.animateDots(typingDiv.querySelector('.dots'));
        
        return typingDiv.id;
    }
    
    removeTypingIndicator(typingId) {
        const typingDiv = document.getElementById(typingId);
        if (typingDiv) {
            typingDiv.remove();
        }
    }
    
    animateDots(dotsElement) {
        let dots = '';
        const interval = setInterval(() => {
            if (!dotsElement.parentElement) {
                clearInterval(interval);
                return;
            }
            
            dots += '.';
            if (dots.length > 3) dots = '';
            dotsElement.textContent = dots;
        }, 500);
    }
    
    typeMessage(type, text, element = null) {
        if (!element) {
            element = document.createElement('div');
            element.className = type === 'system' ? 'system-line' : 'bot-response';
            this.chatArea.appendChild(element);
        }
        
        let i = 0;
        const prefix = type === 'system' ? '>>> ' : '>> ';
        element.innerHTML = prefix;
        
        const typeInterval = setInterval(() => {
            if (i < text.length) {
                element.innerHTML = prefix + text.substring(0, i + 1);
                i++;
            } else {
                clearInterval(typeInterval);
            }
        }, 20); // 20ms per character for fast typing effect
        
        this.scrollToBottom();
    }
    
    scrollToBottom() {
        setTimeout(() => {
            this.chatArea.scrollTop = this.chatArea.scrollHeight;
        }, 50);
    }
    
    addGlitchEffect(element) {
        element.classList.add('glitch-active');
        setTimeout(() => {
            element.classList.remove('glitch-active');
        }, 200);
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    initMatrixBackground() {
        // Create subtle matrix rain effect
        const chars = '01';
        const columns = Math.floor(window.innerWidth / 20);
        
        for (let i = 0; i < 50; i++) {
            const span = document.createElement('span');
            span.className = 'matrix-char';
            span.textContent = chars[Math.floor(Math.random() * chars.length)];
            span.style.position = 'absolute';
            span.style.left = Math.random() * 100 + '%';
            span.style.top = Math.random() * 100 + '%';
            span.style.color = '#00FF00';
            span.style.opacity = '0.1';
            span.style.fontSize = '12px';
            span.style.fontFamily = 'IBM Plex Mono, monospace';
            span.style.animation = `matrix-fall ${5 + Math.random() * 10}s linear infinite`;
            span.style.animationDelay = Math.random() * 5 + 's';
            
            this.matrixBackground.appendChild(span);
        }
        
        // Add CSS for matrix animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes matrix-fall {
                0% {
                    transform: translateY(-100vh);
                    opacity: 0;
                }
                10% {
                    opacity: 0.1;
                }
                90% {
                    opacity: 0.1;
                }
                100% {
                    transform: translateY(100vh);
                    opacity: 0;
                }
            }
            
            .glitch-active {
                animation: glitch 0.2s !important;
            }
        `;
        document.head.appendChild(style);
    }
}

// Initialize terminal when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.batTerminal = new BatTerminal();
});

// Konami code easter egg for extra Batman effects
let konamiCode = [];
const konamiSequence = [
    'ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown',
    'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight',
    'KeyB', 'KeyA'
];

document.addEventListener('keydown', (e) => {
    konamiCode.push(e.code);
    if (konamiCode.length > konamiSequence.length) {
        konamiCode.shift();
    }
    
    if (konamiCode.join(',') === konamiSequence.join(',')) {
        // Easter egg: Bat signal effect
        const batSignal = document.createElement('div');
        batSignal.innerHTML = `
            <div style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); 
                        z-index: 10000; color: #FFFF00; font-size: 50px; text-shadow: 0 0 20px #FFFF00;
                        animation: bat-signal 3s ease-in-out; pointer-events: none;">
                <pre>
   /\   /\
  /  \_/  \
 /        \
/  ^    ^  \
|  (o)  (o) |
 \    <>   /
  \  ___  /
   \______/
                </pre>
                <div style="text-align: center; margin-top: 20px; font-family: 'IBM Plex Mono', monospace;">
                    BAT SIGNAL ACTIVATED
                </div>
            </div>
        `;
        
        const style = document.createElement('style');
        style.textContent = `
            @keyframes bat-signal {
                0% { opacity: 0; transform: translate(-50%, -50%) scale(0.5); }
                50% { opacity: 1; transform: translate(-50%, -50%) scale(1.2); }
                100% { opacity: 0; transform: translate(-50%, -50%) scale(1); }
            }
        `;
        document.head.appendChild(style);
        document.body.appendChild(batSignal);
        
        setTimeout(() => {
            batSignal.remove();
            style.remove();
        }, 3000);
        
        konamiCode = [];
    }
});