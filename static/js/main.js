// Main JavaScript for EZCaters Voice Agent

class EZCatersVoiceAgent {
    constructor() {
        this.isRecording = false;
        this.recognition = null;
        this.currentCallId = this.generateCallId();
        this.initializeSpeechRecognition();
        this.initializeEventListeners();
    }

    generateCallId() {
        return 'call_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    }

    initializeSpeechRecognition() {
        // Check if browser supports speech recognition
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            
            this.recognition.continuous = false;
            this.recognition.interimResults = true;
            this.recognition.lang = 'en-US';
            this.recognition.maxAlternatives = 1;
            
            // Add timeout to prevent hanging
            this.speechTimeout = null;
            
            this.recognition.onstart = () => {
                console.log('Speech recognition started');
                this.onRecordingStart();
                
                // Set a timeout to prevent indefinite listening
                this.speechTimeout = setTimeout(() => {
                    if (this.isRecording) {
                        this.recognition.stop();
                        this.showError('Speech recognition timed out', 'Please try again or use the text demo below.');
                    }
                }, 10000); // 10 second timeout
            };
            
            this.recognition.onresult = (event) => {
                console.log('Speech recognition result:', event);
                if (this.speechTimeout) {
                    clearTimeout(this.speechTimeout);
                }
                this.onSpeechResult(event);
            };
            
            this.recognition.onerror = (event) => {
                console.error('Speech recognition error details:', event);
                if (this.speechTimeout) {
                    clearTimeout(this.speechTimeout);
                }
                this.onSpeechError(event);
            };
            
            this.recognition.onend = () => {
                console.log('Speech recognition ended');
                if (this.speechTimeout) {
                    clearTimeout(this.speechTimeout);
                }
                this.onRecordingEnd();
            };
            
            // Test speech recognition availability
            this.testSpeechRecognition();
        } else {
            console.warn('Speech recognition not supported in this browser');
            this.showUnsupportedMessage();
        }
        
        // Always add text demo as it's more reliable
        this.addTextDemoOption();
    }

    testSpeechRecognition() {
        // Quick test to see if speech recognition is actually available
        try {
            const testRecognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            testRecognition.continuous = false;
            testRecognition.interimResults = false;
            
            testRecognition.onerror = (event) => {
                console.warn('Speech recognition test failed:', event.error);
                if (event.error === 'network') {
                    this.showNetworkIssueWarning();
                }
            };
            
            // Don't actually start it, just test if we can create it
            setTimeout(() => {
                testRecognition.abort();
            }, 100);
            
        } catch (error) {
            console.warn('Speech recognition test error:', error);
            this.showUnsupportedMessage();
        }
    }

    showNetworkIssueWarning() {
        const voiceStatus = document.getElementById('voiceStatus');
        if (voiceStatus) {
            voiceStatus.innerHTML = `
                <i class="fas fa-exclamation-triangle text-warning"></i>
                <span>Speech recognition may have connectivity issues. Text demo recommended.</span>
            `;
        }
    }

    initializeEventListeners() {
        // Smooth scrolling for navigation links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            });
        });

        // Enter key for search
        const searchQuery = document.getElementById('searchQuery');
        if (searchQuery) {
            searchQuery.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    performSearch();
                }
            });
        }
    }

    showUnsupportedMessage() {
        const voiceStatus = document.getElementById('voiceStatus');
        const voiceButton = document.getElementById('voiceButton');
        
        if (voiceStatus && voiceButton) {
            voiceStatus.innerHTML = `
                <i class="fas fa-exclamation-triangle text-warning"></i>
                <span>Speech recognition not supported in your browser</span>
            `;
            voiceButton.disabled = true;
            voiceButton.innerHTML = `
                <i class="fas fa-microphone-slash"></i>
                <span>Not Available</span>
            `;
        }
    }

    toggleVoiceDemo() {
        if (!this.recognition) {
            this.showUnsupportedMessage();
            return;
        }

        if (this.isRecording) {
            this.stopRecording();
        } else {
            this.startRecording();
        }
    }

    startRecording() {
        try {
            this.recognition.start();
            this.isRecording = true;
        } catch (error) {
            console.error('Error starting speech recognition:', error);
            this.showError('Failed to start voice recognition');
        }
    }

    stopRecording() {
        if (this.recognition && this.isRecording) {
            this.recognition.stop();
            this.isRecording = false;
        }
    }

    onRecordingStart() {
        const voiceStatus = document.getElementById('voiceStatus');
        const voiceButton = document.getElementById('voiceButton');
        
        if (voiceStatus) {
            voiceStatus.className = 'voice-status recording mb-4';
            voiceStatus.innerHTML = `
                <i class="fas fa-microphone text-danger"></i>
                <span>Listening... Speak now!</span>
            `;
        }
        
        if (voiceButton) {
            voiceButton.className = 'btn btn-danger btn-lg voice-button recording';
            voiceButton.innerHTML = `
                <i class="fas fa-stop"></i>
                <span>Stop</span>
            `;
        }
        
        // Clear previous results
        this.clearDisplays();
    }

    onSpeechResult(event) {
        let finalTranscript = '';
        let interimTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                finalTranscript += transcript;
            } else {
                interimTranscript += transcript;
            }
        }
        
        // Update transcript display
        const transcriptDisplay = document.getElementById('transcript');
        if (transcriptDisplay) {
            transcriptDisplay.className = 'transcript-display has-content mt-4';
            transcriptDisplay.textContent = finalTranscript + interimTranscript;
        }
        
        // Process final transcript
        if (finalTranscript.trim()) {
            this.processVoiceInput(finalTranscript.trim());
        }
    }

    onSpeechError(event) {
        console.error('Speech recognition error details:', event);
        
        let errorMessage = 'Speech recognition issue: ';
        let suggestion = '';
        
        switch(event.error) {
            case 'network':
                errorMessage += 'connectivity problem';
                suggestion = `The browser's speech recognition service requires internet access to Google's servers. 
                             <br><strong>Solutions:</strong>
                             <br>• Check your internet connection
                             <br>• Try refreshing the page
                             <br>• Use the text demo below (recommended)
                             <br>• Some networks/firewalls block speech services`;
                break;
            case 'not-allowed':
                errorMessage += 'microphone access denied';
                suggestion = 'Please allow microphone access in your browser settings and try again.';
                break;
            case 'no-speech':
                errorMessage += 'no speech detected';
                suggestion = 'Please speak clearly and try again, or use the text demo below.';
                break;
            case 'audio-capture':
                errorMessage += 'microphone unavailable';
                suggestion = 'Please check your microphone connection or use the text demo below.';
                break;
            case 'service-not-allowed':
                errorMessage += 'speech service blocked';
                suggestion = 'Speech recognition may be blocked by your network/firewall. Use the text demo below.';
                break;
            case 'bad-grammar':
                errorMessage += 'recognition configuration error';
                suggestion = 'Please try again or use the text demo below.';
                break;
            case 'language-not-supported':
                errorMessage += 'language not supported';
                suggestion = 'Please try again or use the text demo below.';
                break;
            default:
                errorMessage += event.error || 'unknown error';
                suggestion = 'Please try again or use the reliable text demo below.';
        }
        
        this.showError(errorMessage, suggestion);
        this.resetVoiceInterface();
    }

    onRecordingEnd() {
        this.isRecording = false;
        this.resetVoiceInterface();
    }

    resetVoiceInterface() {
        const voiceStatus = document.getElementById('voiceStatus');
        const voiceButton = document.getElementById('voiceButton');
        
        if (voiceStatus) {
            voiceStatus.className = 'voice-status mb-4';
            voiceStatus.innerHTML = `
                <i class="fas fa-microphone-slash"></i>
                <span>Voice agent ready</span>
            `;
        }
        
        if (voiceButton) {
            voiceButton.className = 'btn btn-primary btn-lg voice-button';
            voiceButton.innerHTML = `
                <i class="fas fa-microphone"></i>
                <span>Start Talking</span>
            `;
        }
    }

    clearDisplays() {
        const transcriptDisplay = document.getElementById('transcript');
        const responseDisplay = document.getElementById('response');
        
        if (transcriptDisplay) {
            transcriptDisplay.className = 'transcript-display mt-4';
            transcriptDisplay.textContent = 'Listening...';
        }
        
        if (responseDisplay) {
            responseDisplay.textContent = '';
        }
    }

    async processVoiceInput(transcript) {
        try {
            // Show processing status
            const voiceStatus = document.getElementById('voiceStatus');
            if (voiceStatus) {
                voiceStatus.className = 'voice-status processing mb-4';
                voiceStatus.innerHTML = `
                    <div class="loading"></div>
                    <span>Processing your request...</span>
                `;
            }

            // Since we don't have a real Retell AI integration running, we'll simulate the response
            const response = await this.simulateVoiceProcessing(transcript);
            this.displayResponse(response);
            
        } catch (error) {
            console.error('Error processing voice input:', error);
            this.showError('Failed to process your request');
        } finally {
            this.resetVoiceInterface();
        }
    }

    async simulateVoiceProcessing(transcript) {
        // Simulate API call delay
        await new Promise(resolve => setTimeout(resolve, 1500));
        
        // Send to backend for proper conversation handling
        try {
            const response = await fetch('/webhook', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    call_id: this.currentCallId,
                    event_type: 'speech_recognition',
                    transcript: transcript
                })
            });
            
            const data = await response.json();
            return data.response || "I understand you're looking for catering services. Could you tell me what type of cuisine you're interested in or your location?";
            
        } catch (error) {
            console.error('Error processing with backend:', error);
            
            // Fallback to simple local processing if backend fails
            const lowerTranscript = transcript.toLowerCase();
            
            if (lowerTranscript.includes('italian') || lowerTranscript.includes('pasta') || lowerTranscript.includes('pizza')) {
                return "Great choice! I found Bella's Italian Catering that specializes in Italian cuisine. They're rated 4.8 stars and are located in Boston, MA. They specialize in pasta, pizza, sandwiches, and salads. Would you like their contact information or should I help you find more options?";
            } else if (lowerTranscript.includes('mexican') || lowerTranscript.includes('taco') || lowerTranscript.includes('burrito')) {
                return "Excellent! I found Taco Fiesta Catering that offers fresh Mexican food. They're rated 4.6 stars, located in Cambridge, MA, and specialize in tacos, burritos, nachos, and fajitas. They also have great vegetarian options. Would you like me to connect you with them?";
            } else if (lowerTranscript.includes('chinese') || lowerTranscript.includes('lo mein') || lowerTranscript.includes('fried rice')) {
                return "Perfect! Golden Dragon Chinese offers traditional Chinese dishes with modern presentation. They're rated 4.7 stars, located in Somerville, MA, and specialize in lo mein, fried rice, dumplings, and sweet and sour dishes. Their minimum order is $30. Would you like their contact information?";
            } else if (lowerTranscript.includes('boston') || lowerTranscript.includes('cambridge') || lowerTranscript.includes('somerville')) {
                return "I found several great caterers in the Boston area! The closest options include Bella's Italian Catering in Boston, Taco Fiesta Catering in Cambridge, and Golden Dragon Chinese in Somerville. All are highly rated and offer different cuisine types. Which type of food are you interested in?";
            } else if (lowerTranscript.includes('yes') || lowerTranscript.includes('sure') || lowerTranscript.includes('okay')) {
                return "Great! I'll be happy to help you with that. Can you provide me with any additional details about what you're looking for?";
            } else if (lowerTranscript.includes('help') || lowerTranscript.includes('what') || lowerTranscript.includes('how')) {
                return "Welcome to EZCaters! I'm here to help you find the perfect catering service for your needs. I can help you search by cuisine type like Italian, Mexican, or Chinese, by your location, or by specific menu items you're craving. What type of catering are you looking for today?";
            } else {
                return "I understand you're looking for catering services. Could you tell me what type of cuisine you're interested in, your location, or specific menu items you'd like? For example, you could say 'I need Italian food in Boston' or 'I want tacos for my event'.";
            }
        }
    }

    displayResponse(response) {
        const responseDisplay = document.getElementById('response');
        if (responseDisplay) {
            responseDisplay.textContent = response;
            
            // Simulate text-to-speech if available
            if ('speechSynthesis' in window) {
                const utterance = new SpeechSynthesisUtterance(response);
                utterance.rate = 0.8;
                utterance.pitch = 1;
                speechSynthesis.speak(utterance);
            }
        }
    }

    showError(message, suggestion) {
        const responseDisplay = document.getElementById('response');
        if (responseDisplay) {
            let html = `
                <div class="alert alert-danger" role="alert">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    ${message}
            `;
            
            if (suggestion) {
                html += `<br><small class="mt-2 d-block">${suggestion}</small>`;
            }
            
            html += `</div>`;
            responseDisplay.innerHTML = html;
        }
    }

    addTextDemoOption() {
        // Add text input demo option
        const demoContainer = document.querySelector('.voice-demo-container');
        if (demoContainer) {
            const textDemoHtml = `
                <div class="text-demo-option mt-5 p-4 bg-light rounded">
                    <h5 class="text-primary mb-3">
                        <i class="fas fa-keyboard me-2"></i>Text Demo (Recommended)
                    </h5>
                    <p class="mb-3 text-muted">
                        Type your request below to test the EZCaters Voice Agent. This works reliably without any connectivity issues.
                    </p>
                    <div class="input-group mb-3">
                        <input type="text" class="form-control form-control-lg" id="textDemoInput" 
                               placeholder="Type: 'I want Italian food near Boston'">
                        <button class="btn btn-primary btn-lg" onclick="ezCatersAgent.tryTextDemo()">
                            <i class="fas fa-paper-plane"></i> Send
                        </button>
                    </div>
                    <div class="text-demo-examples">
                        <small class="text-muted">
                            <strong>Try these examples:</strong><br>
                            • "I want Italian food near Boston"<br>
                            • "Do you have pizza delivery?"<br>
                            • "Find Mexican restaurants"<br>
                            • "I need catering for 20 people"<br>
                            • "Place an order"
                        </small>
                    </div>
                </div>
            `;
            demoContainer.insertAdjacentHTML('beforeend', textDemoHtml);
            
            // Add enter key support
            setTimeout(() => {
                const textInput = document.getElementById('textDemoInput');
                if (textInput) {
                    textInput.addEventListener('keypress', (e) => {
                        if (e.key === 'Enter') {
                            this.tryTextDemo();
                        }
                    });
                    
                    // Focus on the input for better UX
                    textInput.focus();
                }
            }, 100);
        }
    }

    tryTextDemo() {
        const textInput = document.getElementById('textDemoInput');
        if (textInput && textInput.value.trim()) {
            const transcript = textInput.value.trim();
            
            // Show what was "said"
            const transcriptDisplay = document.getElementById('transcript');
            if (transcriptDisplay) {
                transcriptDisplay.className = 'transcript-display has-content mt-4';
                transcriptDisplay.textContent = transcript;
            }
            
            // Process the input
            this.processVoiceInput(transcript);
            
            // Clear the input
            textInput.value = '';
        }
    }
}

// Search functionality
async function performSearch() {
    const searchType = document.getElementById('searchType').value;
    const searchQuery = document.getElementById('searchQuery').value.trim();
    const searchResults = document.getElementById('searchResults');
    
    if (!searchQuery) {
        alert('Please enter a search term');
        return;
    }
    
    // Show loading
    searchResults.innerHTML = `
        <div class="text-center py-4">
            <div class="loading"></div>
            <span>Searching for catering services...</span>
        </div>
    `;
    
    try {
        const response = await fetch('/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                type: searchType,
                query: searchQuery
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displaySearchResults(data.results);
        } else {
            throw new Error(data.error || 'Search failed');
        }
        
    } catch (error) {
        console.error('Search error:', error);
        searchResults.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Failed to search catering services. Please try again.
            </div>
        `;
    }
}

function displaySearchResults(results) {
    const searchResults = document.getElementById('searchResults');
    
    if (!results || results.length === 0) {
        searchResults.innerHTML = `
            <div class="alert alert-info" role="alert">
                <i class="fas fa-info-circle me-2"></i>
                No catering services found matching your criteria. Try a different search term or location.
            </div>
        `;
        return;
    }
    
    let html = '<div class="row g-3">';
    
    results.forEach(caterer => {
        html += `
            <div class="col-12">
                <div class="caterer-card">
                    <div class="caterer-header d-flex justify-content-between align-items-start mb-3">
                        <div>
                            <h5 class="caterer-name">${caterer.name}</h5>
                            <span class="caterer-cuisine">${caterer.cuisine}</span>
                        </div>
                        <div class="text-end">
                            <div class="caterer-rating">
                                <i class="fas fa-star"></i> ${caterer.rating}
                            </div>
                            <div class="price-range">${caterer.price_range}</div>
                        </div>
                    </div>
                    
                    <div class="caterer-details">
                        <p class="caterer-specialties">
                            <strong>Specialties:</strong> ${caterer.specialties.join(', ')}
                        </p>
                        <p class="mb-2">
                            <i class="fas fa-map-marker-alt me-2"></i>
                            ${caterer.location}
                            ${caterer.distance ? ` (${caterer.distance} miles away)` : ''}
                        </p>
                        <p class="mb-2">
                            <i class="fas fa-dollar-sign me-2"></i>
                            Minimum order: $${caterer.min_order}
                        </p>
                        <p class="caterer-contact mb-0">
                            <i class="fas fa-phone me-2"></i>
                            <a href="tel:${caterer.phone}" class="text-decoration-none">${caterer.phone}</a>
                        </p>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    searchResults.innerHTML = html;
}

// Utility functions
function startVoiceDemo() {
    const demoSection = document.getElementById('demo');
    if (demoSection) {
        demoSection.scrollIntoView({ behavior: 'smooth' });
        setTimeout(() => {
            if (window.voiceAgent) {
                window.voiceAgent.toggleVoiceDemo();
            }
        }, 1000);
    }
}

function toggleVoiceDemo() {
    if (window.voiceAgent) {
        window.voiceAgent.toggleVoiceDemo();
    }
}

// Initialize the voice agent when the page loads
document.addEventListener('DOMContentLoaded', function() {
    window.ezCatersAgent = new EZCatersVoiceAgent();
    // Also keep the old reference for backward compatibility
    window.voiceAgent = window.ezCatersAgent;
    
    // Add some interactive effects
    const featureCards = document.querySelectorAll('.feature-card');
    featureCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-10px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
    
    // Animate elements on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Apply animation to feature cards
    featureCards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(card);
    });
}); 