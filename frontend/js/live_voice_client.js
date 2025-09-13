/**
 * Client-side live voice system using HTTP/SSE instead of Socket.IO
 * All processing happens on the server side
 */

class ServerSideLiveVoiceClient {
    constructor() {
        this.sessionId = null;
        this.eventSource = null;
        this.isActive = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.baseUrl = 'http://localhost:8003/api/live';
    }

    async initialize() {
        console.log('🎤 Initializing Server-Side Live Voice Client...');
        
        try {
            // Create a new session on the server
            const response = await fetch(`${this.baseUrl}/session/create`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const data = await response.json();
            this.sessionId = data.session_id;
            
            // Setup event stream for real-time updates
            this.setupEventStream();
            
            // Setup audio capture
            await this.setupAudioCapture();
            
            this.isActive = true;
            console.log('✅ Live Voice Client initialized successfully');
            return true;
            
        } catch (error) {
            console.error('❌ Failed to initialize Live Voice Client:', error);
            this.showError(error.message);
            return false;
        }
    }

    setupEventStream() {
        if (!this.sessionId) return;
        
        // Connect to server-sent events stream
        this.eventSource = new EventSource(`${this.baseUrl}/session/${this.sessionId}/stream`);
        
        this.eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleServerMessage(data);
        };
        
        this.eventSource.onerror = (error) => {
            console.error('SSE Error:', error);
            if (this.eventSource.readyState === EventSource.CLOSED) {
                this.reconnect();
            }
        };
    }

    handleServerMessage(data) {
        if (data.type === 'message') {
            const message = data.data;
            
            if (message.role === 'assistant') {
                // Display assistant's response
                this.displayResponse(message.content);
                
                // Play audio if available
                if (message.audio) {
                    this.playAudio(message.audio);
                }
            } else if (message.role === 'user') {
                // Display user's message
                this.displayUserMessage(message.content);
            }
        } else if (data.type === 'heartbeat') {
            console.log('💓 Heartbeat received');
        } else if (data.error) {
            this.showError(data.error);
        }
    }

    async setupAudioCapture() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            this.mediaRecorder = new MediaRecorder(stream, {
                mimeType: 'audio/webm;codecs=opus'
            });
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
                this.audioChunks = [];
                await this.sendAudioToServer(audioBlob);
            };
            
            console.log('🎙️ Audio capture setup complete');
        } catch (error) {
            console.error('Failed to setup audio capture:', error);
            throw error;
        }
    }

    async sendTextMessage(text) {
        if (!this.sessionId || !text.trim()) return;
        
        try {
            const response = await fetch(`${this.baseUrl}/session/${this.sessionId}/text`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });
            
            const data = await response.json();
            
            if (data.audio) {
                this.playAudio(data.audio);
            }
            
            if (data.text) {
                this.displayResponse(data.text);
            }
            
        } catch (error) {
            console.error('Failed to send text message:', error);
            this.showError(error.message);
        }
    }

    async sendAudioToServer(audioBlob) {
        if (!this.sessionId) return;
        
        try {
            // Convert blob to base64
            const reader = new FileReader();
            reader.readAsDataURL(audioBlob);
            
            reader.onloadend = async () => {
                const base64Audio = reader.result.split(',')[1];
                
                const response = await fetch(`${this.baseUrl}/session/${this.sessionId}/audio`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ audio: base64Audio })
                });
                
                const data = await response.json();
                
                if (data.audio) {
                    this.playAudio(data.audio);
                }
                
                if (data.text) {
                    this.displayResponse(data.text);
                }
            };
            
        } catch (error) {
            console.error('Failed to send audio:', error);
            this.showError(error.message);
        }
    }

    startRecording() {
        if (this.mediaRecorder && this.mediaRecorder.state === 'inactive') {
            this.audioChunks = [];
            this.mediaRecorder.start();
            console.log('🔴 Recording started');
            return true;
        }
        return false;
    }

    stopRecording() {
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.stop();
            console.log('⏹️ Recording stopped');
            return true;
        }
        return false;
    }

    playAudio(base64Audio) {
        try {
            const audio = new Audio(`data:audio/mp3;base64,${base64Audio}`);
            audio.play().catch(e => console.error('Audio playback error:', e));
        } catch (error) {
            console.error('Failed to play audio:', error);
        }
    }

    displayResponse(text) {
        // Update UI with assistant's response
        const responseDiv = document.createElement('div');
        responseDiv.className = 'assistant-message';
        responseDiv.textContent = text;
        
        const conversationBox = document.getElementById('conversation-box');
        if (conversationBox) {
            conversationBox.appendChild(responseDiv);
            conversationBox.scrollTop = conversationBox.scrollHeight;
        }
    }

    displayUserMessage(text) {
        // Update UI with user's message
        const messageDiv = document.createElement('div');
        messageDiv.className = 'user-message';
        messageDiv.textContent = text;
        
        const conversationBox = document.getElementById('conversation-box');
        if (conversationBox) {
            conversationBox.appendChild(messageDiv);
            conversationBox.scrollTop = conversationBox.scrollHeight;
        }
    }

    showError(message) {
        console.error('Live Voice Error:', message);
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = `Error: ${message}`;
        
        const conversationBox = document.getElementById('conversation-box');
        if (conversationBox) {
            conversationBox.appendChild(errorDiv);
        }
    }

    async reconnect() {
        console.log('Attempting to reconnect...');
        setTimeout(() => {
            this.setupEventStream();
        }, 3000);
    }

    async end() {
        if (!this.sessionId) return;
        
        try {
            // Stop recording if active
            this.stopRecording();
            
            // Close event stream
            if (this.eventSource) {
                this.eventSource.close();
                this.eventSource = null;
            }
            
            // End session on server
            await fetch(`${this.baseUrl}/session/${this.sessionId}/end`, {
                method: 'POST'
            });
            
            // Stop media tracks
            if (this.mediaRecorder && this.mediaRecorder.stream) {
                this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
            }
            
            this.isActive = false;
            this.sessionId = null;
            
            console.log('Live voice session ended');
            
        } catch (error) {
            console.error('Failed to end session:', error);
        }
    }
}

// Export for use in main application
window.ServerSideLiveVoiceClient = ServerSideLiveVoiceClient;