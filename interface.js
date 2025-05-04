/**
 * LinkedIn Connection Bot - Interface Controller
 * Connects the UI with the LinkedIn automation script
 */

document.addEventListener('DOMContentLoaded', function() {
    // UI Elements
    const form = document.getElementById('bot-form');
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    const resultsSection = document.getElementById('results-section');
    const consoleOutput = document.getElementById('console');
    const progressBar = document.getElementById('progress-bar-fill');
    const progressText = document.getElementById('progress-text');
    
    // Stats elements
    const profilesScanned = document.getElementById('profiles-scanned');
    const requestsSent = document.getElementById('requests-sent');
    const pagesProcessed = document.getElementById('pages-processed');
    const timeElapsed = document.getElementById('time-elapsed');
    
    // Bot state
    let botRunning = false;
    let startTime;
    let timerInterval;
    let botSessionId = null; // Will track the current bot session
    
    // API endpoints
    const API_ENDPOINTS = {
        RUN_BOT: '/run-bot',
        SERVER_STATUS: '/server-status'
    };
    
    // Stats tracking
    let stats = {
        profilesScanned: 0,
        requestsSent: 0,
        pagesProcessed: 0
    };
    
    /**
     * Logs a message to the console UI with timestamp
     * @param {string} message - The message to log
     * @param {string} type - Message type (info, success, error, warning)
     */
    function logToConsole(message, type = 'info') {
        const time = new Date().toLocaleTimeString();
        const logEntry = document.createElement('p');
        logEntry.innerHTML = `<span class="console-time">[${time}]</span> <span class="console-${type}">${message}</span>`;
        consoleOutput.appendChild(logEntry);
        consoleOutput.scrollTop = consoleOutput.scrollHeight;
    }
    
    /**
     * Updates the stats display in the UI
     */
    function updateStats() {
        profilesScanned.textContent = stats.profilesScanned;
        requestsSent.textContent = stats.requestsSent;
        pagesProcessed.textContent = stats.pagesProcessed;
    }
    
    /**
     * Updates the timer display
     */
    function updateTimer() {
        const now = new Date();
        const diff = (now - startTime) / 1000; // in seconds
        
        const minutes = Math.floor(diff / 60);
        const seconds = Math.floor(diff % 60);
        
        timeElapsed.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }
    
    /**
     * Updates the progress bar
     * @param {number} current - Current progress value
     * @param {number} total - Total goal value
     */
    function updateProgress(current, total) {
        const percentage = Math.min(Math.round((current / total) * 100), 100);
        progressBar.style.width = `${percentage}%`;
        progressText.textContent = `${percentage}%`;
    }
    
    /**
     * Process the bot output and update stats accordingly
     * @param {string} output - Output from the bot process
     */
    function processBotOutput(output) {
        if (!output) return;
        
        // Split the output into lines and log each line
        const lines = output.split('\n');
        
        lines.forEach(line => {
            // Skip empty lines
            if (!line.trim()) return;
            
            // Determine the log type based on content
            let logType = 'info';
            if (line.includes('ERROR') || line.includes('error') || line.includes('failed')) {
                logType = 'error';
            } else if (line.includes('SUCCESS') || line.includes('success') || line.includes('sent connection request')) {
                logType = 'success';
            } else if (line.includes('WARNING') || line.includes('warning')) {
                logType = 'warning';
            }
            
            // Log the line to console
            logToConsole(line, logType);
            
            // Update stats based on the line content
            if (line.includes('Processing profile')) {
                stats.profilesScanned++;
                updateStats();
            } else if (line.includes('Sent connection request') || line.includes('request sent')) {
                stats.requestsSent++;
                updateStats();
            } else if (line.includes('Processing page') || line.includes('Moving to page')) {
                // Extract page number if available
                const pageMatch = line.match(/page (\d+)/i);
                if (pageMatch && pageMatch[1]) {
                    stats.pagesProcessed = parseInt(pageMatch[1]);
                    updateStats();
                } else {
                    stats.pagesProcessed++;
                    updateStats();
                }
            } else if (line.includes('Total connection requests sent:')) {
                try {
                    stats.requestsSent = parseInt(line.split(':')[1].trim());
                    updateStats();
                } catch (error) {
                    console.error('Error parsing connection requests:', error);
                }
            }
        });
    }
    
    /**
     * Checks if the server is available
     * @returns {Promise<boolean>} Whether the server is available
     */
    function checkServerAvailability() {
        return new Promise((resolve) => {
            fetch(API_ENDPOINTS.SERVER_STATUS)
                .then(response => {
                    if (response.ok) {
                        resolve(true);
                    } else {
                        resolve(false);
                    }
                })
                .catch(() => {
                    resolve(false);
                });
        });
    }
    
    /**
     * Runs the LinkedIn bot via the Flask backend
     * @param {Object} config - Bot configuration parameters
     */
    function runBot(config) {
        // Display initial log messages
        logToConsole('Connecting to bot server...', 'info');
        
        // Make API call to run bot
        fetch(API_ENDPOINTS.RUN_BOT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: config.username,
                password: config.password,
                keyword: config.keyword,
                numPages: config.pages,
                maxRequests: config.limit,
                message: config.message,
                headless: config.headless
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                logToConsole(`Bot Error: ${data.message || data.error}`, 'error');
                stopBot();
                return;
            }
            
            logToConsole('Bot started successfully!', 'success');
            logToConsole(`Search keyword: "${config.keyword}"`, 'info');
            logToConsole(`Target: ${config.pages} pages, maximum ${config.limit} connection requests`, 'info');
            
            // Process output from bot
            if (data.output) {
                processBotOutput(data.output);
            }
            
            // Update stats if available
            if (data.connectionsSent !== undefined) {
                stats.requestsSent = data.connectionsSent;
                updateStats();
            }
            
            // Process any errors
            if (data.errors) {
                logToConsole(`Bot reported errors: ${data.errors}`, 'error');
            }
            
            // Update progress
            updateProgress(stats.requestsSent, config.limit);
            
            // If finished successfully
            if (data.success) {
                logToConsole('Bot execution completed successfully', 'success');
                stopBot(true);
            }
        })
        .catch(error => {
            logToConsole(`Error running bot: ${error.message}`, 'error');
            stopBot();
        });
    }
    
    /**
     * Starts the demo mode (when server is not available)
     * @param {Object} config - Bot configuration
     */
    function startDemoMode(config) {
        logToConsole("Starting in DEMO MODE (no server connection)", "warning");
        logToConsole("Initializing LinkedIn Connection Bot...", "info");
        logToConsole(`Search keyword: "${config.keyword}"${config.location ? ` in ${config.location}` : ''}`, "info");
        logToConsole(`Target: ${config.pages} pages, maximum ${config.limit} connection requests`, "info");
        logToConsole(`Headless mode: ${config.headless ? 'Enabled' : 'Disabled'}`, "info");
        
        setTimeout(() => {
            logToConsole("Web driver initialized successfully", "success");
            logToConsole("Logging into LinkedIn...", "info");
            
            setTimeout(() => {
                logToConsole("Login successful!", "success");
                logToConsole("Starting search for profiles...", "info");
                
                const totalProfiles = Math.min(config.pages * 10, config.limit * 2);
                let processedProfiles = 0;
                let currentPage = 0;
                
                // Simulate processing pages
                const processNextPage = () => {
                    if (currentPage >= config.pages || !botRunning) {
                        if (botRunning) {
                            logToConsole("Finished processing all pages!", "success");
                            stopBot(true);
                        }
                        return;
                    }
                    
                    currentPage++;
                    stats.pagesProcessed = currentPage;
                    updateStats();
                    
                    logToConsole(`Processing page ${currentPage}/${config.pages}`, "info");
                    
                    // Simulate finding profiles on the page
                    const profilesOnPage = Math.min(10, totalProfiles - processedProfiles);
                    logToConsole(`Found ${profilesOnPage} profiles on this page`, "info");
                    
                    // Simulate processing each profile
                    let profileIndex = 0;
                    const processNextProfile = () => {
                        if (profileIndex >= profilesOnPage || !botRunning || stats.requestsSent >= config.limit) {
                            if (stats.requestsSent >= config.limit && botRunning) {
                                logToConsole(`Reached connection request limit (${config.limit})`, "warning");
                                stopBot(true);
                                return;
                            }
                            
                            if (botRunning) {
                                // Move to next page
                                setTimeout(processNextPage, 1000);
                            }
                            return;
                        }
                        
                        profileIndex++;
                        processedProfiles++;
                        stats.profilesScanned++;
                        updateStats();
                        
                        // Random names for simulation
                        const names = ["John", "Sarah", "Michael", "Emily", "David", "Jessica", "Alex", "Lisa"];
                        const name = names[Math.floor(Math.random() * names.length)];
                        
                        logToConsole(`Processing profile ${processedProfiles}: ${name}`, "info");
                        
                        // Simulate connection success/failure (80% success rate)
                        setTimeout(() => {
                            if (Math.random() < 0.8) {
                                stats.requestsSent++;
                                updateStats();
                                
                                const personalizedMessage = config.message.replace('{name}', name);
                                logToConsole(`Sent connection request to ${name} with message: "${personalizedMessage}"`, "success");
                            } else {
                                // Random failures
                                const reasons = [
                                    "No connect button found",
                                    "Already connected",
                                    "Connection dialog did not appear",
                                    "Profile has restricted connections"
                                ];
                                const reason = reasons[Math.floor(Math.random() * reasons.length)];
                                logToConsole(`Could not connect with ${name}: ${reason}`, "error");
                            }
                            
                            // Update progress
                            updateProgress(processedProfiles, totalProfiles);
                            
                            // Process next profile with delay
                            setTimeout(processNextProfile, Math.random() * 1000 + 500);
                        }, Math.random() * 1000 + 500);
                    };
                    
                    // Start processing profiles on this page
                    processNextProfile();
                };
                
                // Start processing pages
                processNextPage();
                
            }, 2000);
        }, 1500);
    }
    
    /**
     * Validates the form inputs
     * @param {Object} config - The form values
     * @returns {boolean} - Whether the form is valid
     */
    function validateForm(config) {
        // Check required fields
        if (!config.username || !config.password || !config.keyword) {
            alert('Please fill in all required fields');
            return false;
        }
        
        // Check that message includes {name} placeholder
        if (!config.message.includes('{name}')) {
            alert('Your message should include {name} placeholder to personalize connections');
            return false;
        }
        
        // Validate numeric inputs
        if (config.pages < 1 || config.limit < 1) {
            alert('Number of pages and connection limit must be at least 1');
            return false;
        }
        
        return true;
    }
    
    /**
     * Stops the bot execution and updates UI
     * @param {boolean} completed - Whether the bot completed successfully
     */
    function stopBot(completed = false) {
        if (!botRunning) return;
        
        botRunning = false;
        startBtn.disabled = false;
        stopBtn.disabled = true;
        
        clearInterval(timerInterval);
        
        if (!completed) {
            logToConsole("Bot stopped by user", "warning");
        } else {
            logToConsole("Bot execution completed", "success");
            logToConsole(`Final stats: ${stats.requestsSent} connections sent, ${stats.profilesScanned} profiles scanned, ${stats.pagesProcessed} pages processed`, "info");
        }
        
        botSessionId = null;
    }
    
    /**
     * Starts the bot with the form values
     */
    function startBot() {
        if (botRunning) return;
        
        // Get form values
        const config = {
            username: document.getElementById('username').value,
            password: document.getElementById('password').value,
            keyword: document.getElementById('keyword').value,
            location: document.getElementById('location').value,
            pages: parseInt(document.getElementById('pages').value),
            limit: parseInt(document.getElementById('limit').value),
            message: document.getElementById('message').value || "Hi {name}, I'm exploring opportunities and would love to connect with professionals in your field. Looking forward to learning from your insights!",
            headless: document.getElementById('headless').checked
        };
        
        // Validate form
        if (!validateForm(config)) {
            return;
        }
        
        // Reset stats
        stats = {
            profilesScanned: 0,
            requestsSent: 0,
            pagesProcessed: 0
        };
        updateStats();
        
        // Show results section and clear console
        resultsSection.style.display = 'block';
        consoleOutput.innerHTML = '';
        
        // Update UI state
        botRunning = true;
        startBtn.disabled = true;
        stopBtn.disabled = false;
        
        // Reset progress
        progressBar.style.width = '0%';
        progressText.textContent = '0%';
        
        // Start timer
        startTime = new Date();
        updateTimer();
        timerInterval = setInterval(updateTimer, 1000);
        
        // Scroll to results section
        resultsSection.scrollIntoView({ behavior: 'smooth' });
        
        // Save form values to local storage
        saveFormValues(config);
        
        // Check if we should use real mode or demo mode
        checkServerAvailability().then(serverAvailable => {
            if (serverAvailable) {
                runBot(config);
            } else {
                startDemoMode(config);
            }
        });
    }
    
    /**
     * Save form values to local storage
     * @param {Object} config - The form values to save
     */
    function saveFormValues(config) {
        try {
            const storageConfig = {
                username: config.username,
                // Don't save password
                keyword: config.keyword,
                location: config.location,
                pages: config.pages,
                limit: config.limit,
                message: config.message,
                headless: config.headless
            };
            localStorage.setItem('linkedinBotConfig', JSON.stringify(storageConfig));
        } catch (error) {
            console.error("Error saving form values:", error);
        }
    }
    
    /**
     * Load saved form values from local storage
     */
    function loadSavedFormValues() {
        try {
            const savedConfig = JSON.parse(localStorage.getItem('linkedinBotConfig'));
            if (savedConfig) {
                // Load all values except password
                if (savedConfig.username) document.getElementById('username').value = savedConfig.username;
                if (savedConfig.keyword) document.getElementById('keyword').value = savedConfig.keyword;
                if (savedConfig.location) document.getElementById('location').value = savedConfig.location;
                if (savedConfig.pages) document.getElementById('pages').value = savedConfig.pages;
                if (savedConfig.limit) document.getElementById('limit').value = savedConfig.limit;
                if (savedConfig.message) document.getElementById('message').value = savedConfig.message;
                if (savedConfig.headless !== undefined) document.getElementById('headless').checked = savedConfig.headless;
            }
        } catch (error) {
            console.error("Error loading saved form values:", error);
        }
    }
    
    // Event listeners
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        startBot();
    });
    
    stopBtn.addEventListener('click', function() {
        stopBot();
    });
    
    // Show a warning when user is about to leave the page while bot is running
    window.addEventListener('beforeunload', function(e) {
        if (botRunning) {
            e.preventDefault();
            e.returnValue = 'The bot is still running. Are you sure you want to leave?';
            return e.returnValue;
        }
    });
    
    // Load saved values on page load
    loadSavedFormValues();
});