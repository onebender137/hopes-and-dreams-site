// Scroll Reveal Logic
document.addEventListener('DOMContentLoaded', () => {
    // Scroll Progress Bar
    const progress = document.getElementById('scroll-progress');
    window.addEventListener('scroll', () => {
        const winScroll = document.body.scrollTop || document.documentElement.scrollTop;
        const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
        const scrolled = (winScroll / height) * 100;
        if (progress) {
            progress.style.width = scrolled + "%";
        }
    });

    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('revealed');
                // Trigger chart animation if visible
                if (entry.target.querySelector('.chart-bar')) {
                    animateChart();
                }
            }
        });
    }, observerOptions);

    document.querySelectorAll('[data-reveal]').forEach(el => observer.observe(el));

    // --- Interactive Feature Logic ---

    // 0. Caffeine Fade Visualizer
    const caffMg = document.getElementById('caff-mg');
    const caffHours = document.getElementById('caff-hours');
    const caffBedtime = document.getElementById('caff-bedtime');

    function updateCaffeine() {
        if (!caffMg || !caffHours || !caffBedtime) return;
        
        const initial = parseFloat(caffMg.value) || 0;
        const elapsed = parseFloat(caffHours.value) || 0;
        const tillBed = parseFloat(caffBedtime.value) || 0;
        
        const halfLife = 5.7; // average hours
        const totalHours = elapsed + tillBed;
        
        const residual = initial * Math.pow(0.5, totalHours / halfLife);
        
        const residualEl = document.getElementById('caff-residual');
        const statusEl = document.getElementById('caff-status');
        const adviceEl = document.getElementById('caff-advice');
        const riskBox = document.getElementById('caff-risk-box');
        
        if (residualEl) residualEl.textContent = residual.toFixed(1) + " mg";
        
        let risk = "OPTIMAL";
        let color = "var(--neon-blue)";
        let advice = "System cleared. Minimal sleep disruption architecture.";
        
        if (residual > 50) {
            risk = "CRITICAL";
            color = "#ef4444";
            advice = "EEG studies show measurable deep-sleep suppression at this level. Recommend immediate L-Theanine buffer.";
        } else if (residual > 20) {
            risk = "MODERATE";
            color = "var(--neon-gold)";
            advice = "Sleep architecture may be compromised. Residual exceeds the 20mg metabolic noise threshold.";
        }
        
        if (statusEl) statusEl.innerHTML = `Risk: <span style="color: ${color};">${risk}</span>`;
        if (adviceEl) adviceEl.textContent = advice;
        if (riskBox) riskBox.style.borderLeftColor = color;
    }

    if (caffMg) {
        [caffMg, caffHours, caffBedtime].forEach(el => el.addEventListener('input', updateCaffeine));
        updateCaffeine();
    }

    // 0.1 Autophagy Milestone Tracker
    const fastRange = document.getElementById('fast-range');
    const fastDisplay = document.getElementById('fast-display');

    function updateAutophagy() {
        if (!fastRange || !fastDisplay) return;
        
        const hours = parseInt(fastRange.value);
        fastDisplay.textContent = hours + " Hours";
        
        const milestoneEl = document.getElementById('fast-milestone');
        const descEl = document.getElementById('fast-desc');
        const boxEl = document.getElementById('fast-milestone-box');
        
        let milestone = "Post-Absorptive State";
        let desc = "Blood sugar levels normal. System utilizing dietary energy.";
        let color = "var(--text-dim)";
        let bgColor = "rgba(148, 163, 184, 0.05)";
        
        if (hours >= 48) {
            milestone = "Peak Stem Cell Regeneration";
            desc = "Prolonged autophagy and immune cell turnover. Maximum system reboot.";
            color = "#8b5cf6"; // Purple
            bgColor = "rgba(139, 92, 246, 0.1)";
        } else if (hours >= 24) {
            milestone = "Deep Autophagy Transition";
            desc = "300% increase in autophagy markers. Body-wide cellular recycling accelerated.";
            color = "var(--neon-gold)";
            bgColor = "rgba(251, 191, 36, 0.1)";
        } else if (hours >= 16) {
            milestone = "Early Autophagy";
            desc = "AMPK pathway activated. Cellular cleanup initiated. Insulin levels at baseline.";
            color = "var(--neon-blue)";
            bgColor = "rgba(56, 189, 248, 0.1)";
        } else if (hours >= 12) {
            milestone = "Ketosis Threshold";
            desc = "Fat oxidation begins. Liver glycogen depleted. Metabolic shift starting.";
            color = "var(--neon-blue)";
            bgColor = "rgba(56, 189, 248, 0.05)";
        }
        
        if (milestoneEl) milestoneEl.textContent = milestone;
        if (milestoneEl) milestoneEl.style.color = color;
        if (descEl) descEl.textContent = desc;
        if (boxEl) {
            boxEl.style.borderLeftColor = color;
            boxEl.style.backgroundColor = bgColor;
        }
    }

    if (fastRange) {
        fastRange.addEventListener('input', updateAutophagy);
        updateAutophagy();
    }

    // 1. Biohacking Codex Search
    const codexSearch = document.getElementById('codex-search');
    if (codexSearch) {
        codexSearch.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            const resultBox = document.getElementById('codex-results');
            if (query.length < 2) {
                resultBox.innerHTML = '<em>Search for a term to initialize protocol data.</em>';
                return;
            }

            // Resilience check for codexData
            if (typeof codexData === 'undefined') {
                resultBox.innerHTML = '<em>Error: Codex intelligence not loaded.</em>';
                return;
            }

            const found = Object.keys(codexData).find(key => key.includes(query));
            if (found) {
                resultBox.innerHTML = `<strong>${found.toUpperCase()}:</strong> ${codexData[found]}`;
            } else {
                resultBox.innerHTML = '<em>Term not found in current database.</em>';
            }
        });
    }

    // 2. Neural Frequency Architect
    let brownNoiseNode = null;
    let binauralNodes = null;
    let baseFreq = 200;

    const freqValDisplay = document.getElementById('freq-val');
    const freqType = document.getElementById('freq-type');
    const freqDesc = document.getElementById('freq-desc');
    let currentFreq = 40;

    window.setBrainwave = function(type, freq) {
        currentFreq = freq;
        if (freqValDisplay) freqValDisplay.textContent = freq;
        
        // Update Buttons
        document.querySelectorAll('.preset-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.textContent.toLowerCase() === type) {
                btn.classList.add('active');
            }
        });

        const stateInfo = {
            'delta': { name: "Delta State", desc: "Deep sleep, physical restoration, and restorative healing." },
            'theta': { name: "Theta State", desc: "Deep relaxation, meditation, creativity, and subconscious access." },
            'alpha': { name: "Alpha State", desc: "Relaxed alertness, stress relief, calm focus, and learning." },
            'beta': { name: "Beta State", desc: "Active thinking, problem-solving, analytical tasks, and alertness." },
            'gamma': { name: "Gamma State", desc: "Peak focus, high-level cognition, memory recall, and insight." }
        };

        if (freqType) freqType.textContent = stateInfo[type].name;
        if (freqDesc) freqDesc.textContent = stateInfo[type].desc;

        if (binauralNodes && window.audioCtx) {
            binauralNodes.oscR.frequency.setTargetAtTime(baseFreq + freq, window.audioCtx.currentTime, 0.1);
        }
    };

    window.toggleBrownNoise = function() {
        if (!window.audioCtx) window.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const btn = document.getElementById('brown-toggle');

        if (brownNoiseNode) {
            brownNoiseNode.stop();
            brownNoiseNode = null;
            btn.classList.remove('active');
        } else {
            const bufferSize = 2 * window.audioCtx.sampleRate;
            const noiseBuffer = window.audioCtx.createBuffer(1, bufferSize, window.audioCtx.sampleRate);
            const output = noiseBuffer.getChannelData(0);
            let lastOut = 0.0;
            for (let i = 0; i < bufferSize; i++) {
                const white = Math.random() * 2 - 1;
                output[i] = (lastOut + (0.02 * white)) / 1.02;
                lastOut = output[i];
                output[i] *= 3.5;
            }
            brownNoiseNode = window.audioCtx.createBufferSource();
            brownNoiseNode.buffer = noiseBuffer;
            brownNoiseNode.loop = true;
            
            const gainNode = window.audioCtx.createGain();
            gainNode.gain.setValueAtTime(0.3, window.audioCtx.currentTime);
            
            brownNoiseNode.connect(gainNode).connect(window.audioCtx.destination);
            brownNoiseNode.start();
            btn.classList.add('active');
        }
    };

    window.toggleBinauralBeats = function() {
        if (!window.audioCtx) window.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const btn = document.getElementById('binaural-toggle');

        if (binauralNodes) {
            if (binauralNodes.oscL) binauralNodes.oscL.stop();
            if (binauralNodes.oscR) binauralNodes.oscR.stop();
            binauralNodes = null;
            if (btn) btn.classList.remove('active');
        } else {
            const freq = currentFreq;
            const oscL = window.audioCtx.createOscillator();
            oscL.frequency.setValueAtTime(baseFreq, window.audioCtx.currentTime);
            const pannerL = window.audioCtx.createStereoPanner();
            pannerL.pan.setValueAtTime(-1, window.audioCtx.currentTime);
            
            const oscR = window.audioCtx.createOscillator();
            oscR.frequency.setValueAtTime(baseFreq + freq, window.audioCtx.currentTime);
            const pannerR = window.audioCtx.createStereoPanner();
            pannerR.pan.setValueAtTime(1, window.audioCtx.currentTime);
            
            const gain = window.audioCtx.createGain();
            gain.gain.setValueAtTime(0.1, window.audioCtx.currentTime);

            oscL.connect(pannerL).connect(gain);
            oscR.connect(pannerR).connect(gain);
            gain.connect(window.audioCtx.destination);

            oscL.start();
            oscR.start();
            binauralNodes = { oscL, oscR, gain };
            if (btn) btn.classList.add('active');
        }
    };

    // 3. Protocol Timer
    let timerInterval;
    window.startTimer = function(seconds) {
        clearInterval(timerInterval);
        let timeLeft = seconds;
        const display = document.getElementById('timer-display');
        
        timerInterval = setInterval(() => {
            const mins = Math.floor(timeLeft / 60);
            const secs = timeLeft % 60;
            display.textContent = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
            
            if (timeLeft <= 0) {
                clearInterval(timerInterval);
                display.textContent = "PROTOCOL COMPLETE";
            }
            timeLeft--;
        }, 1000);
    };

    // 4. Sleep Calculator
    const wakeInput = document.getElementById('wake-time');
    const suggestContainer = document.getElementById('suggested-times');

    function calculateSleepTimes() {
        if (!wakeInput || !suggestContainer) return;
        const wakeTime = wakeInput.value;
        const [hours, minutes] = wakeTime.split(':').map(Number);
        const wakeDate = new Date();
        wakeDate.setHours(hours, minutes, 0);

        suggestContainer.innerHTML = '';
        [6, 5, 4].forEach(cycles => {
            const sleepDate = new Date(wakeDate.getTime() - (cycles * 90 * 60 * 1000) - (15 * 60 * 1000));
            const timeStr = sleepDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });

            const card = document.createElement('div');
            card.className = 'time-card';
            card.textContent = timeStr;
            suggestContainer.appendChild(card);
        });
    }

    if (wakeInput) {
        wakeInput.addEventListener('change', calculateSleepTimes);
        calculateSleepTimes();
    }

    // 5. Checklist Logic
    const checks = document.querySelectorAll('.protocol-check');
    checks.forEach(check => {
        const id = check.getAttribute('data-id');
        const saved = localStorage.getItem('protocol_' + id);
        if (saved === 'true') {
            check.checked = true;
            check.parentElement.classList.add('completed');
        }

        check.addEventListener('change', (e) => {
            const isChecked = e.target.checked;
            localStorage.setItem('protocol_' + id, isChecked);
            if (isChecked) {
                check.parentElement.classList.add('completed');
            } else {
                check.parentElement.classList.remove('completed');
            }
        });
    });

    // 6. Accordion
    document.querySelectorAll('.accordion-header').forEach(header => {
        header.addEventListener('click', () => {
            const item = header.parentElement;
            item.classList.toggle('active');
        });
    });

    // 7. Biometric Chart Animation
    function animateChart() {
        const bars = document.querySelectorAll('.chart-bar');
        const heights = ['30%', '45%', '80%', '60%', '90%', '40%', '75%'];
        bars.forEach((bar, i) => {
            setTimeout(() => {
                bar.style.height = heights[i];
            }, i * 100);
        });
    }

    // 8. Neuro-Stack Builder Quiz
    const quizQuestions = [
        {
            q: "What is your primary optimization target?",
            options: [
                { text: "Cognitive Flux (Focus & Memory)", value: "focus" },
                { text: "System Recovery (Sleep & Mood)", value: "sleep" },
                { text: "Bio-Output (Energy & Performance)", value: "energy" }
            ]
        },
        {
            q: "Current experience level with nootropics?",
            options: [
                { text: "Baseline (Beginner)", value: "base" },
                { text: "Augmented (Intermediate)", value: "aug" },
                { text: "Elite (Advanced)", value: "elite" }
            ]
        },
        {
            q: "Preferred intake method?",
            options: [
                { text: "Standard (Capsules/Powder)", value: "std" },
                { text: "Optimized (Sublingual/Fast-Acting)", value: "opt" }
            ]
        }
    ];

    let currentQuizStep = 0;
    let quizAnswers = [];

    window.startQuiz = function() {
        const intro = document.getElementById('quiz-intro');
        const questions = document.getElementById('quiz-questions');
        if (intro) intro.style.display = 'none';
        if (questions) {
            questions.style.display = 'block';
            showQuizQuestion();
        }
    };

    function showQuizQuestion() {
        const q = quizQuestions[currentQuizStep];
        const textEl = document.getElementById('question-text');
        const container = document.getElementById('options-container');
        
        if (textEl) textEl.textContent = q.q;
        if (container) {
            container.innerHTML = '';
            q.options.forEach(opt => {
                const btn = document.createElement('button');
                btn.className = 'buy-btn';
                btn.style.textAlign = 'left';
                btn.style.padding = '15px';
                btn.textContent = opt.text;
                btn.onclick = () => selectQuizOption(opt.value);
                container.appendChild(btn);
            });
        }
    }

    function selectQuizOption(val) {
        quizAnswers.push(val);
        currentQuizStep++;
        if (currentQuizStep < quizQuestions.length) {
            showQuizQuestion();
        } else {
            showQuizResults();
        }
    }

    function showQuizResults() {
        const questions = document.getElementById('quiz-questions');
        const resultsDiv = document.getElementById('quiz-results');
        if (questions) questions.style.display = 'none';
        if (resultsDiv) {
            resultsDiv.classList.add('active');
            const output = document.getElementById('recommendation-output');
            const goal = quizAnswers[0];
            const level = quizAnswers[1];
            const method = quizAnswers[2];
            
            let rec = "";
            let stackName = "";
            let components = "";
            
            if (goal === 'focus') {
                stackName = "The Architect Stack";
                components = "Alpha GPC + Huperzine-A + Citicoline";
                rec = "This combination optimizes acetylcholine levels for sustained deep work and neural plasticity.";
                if (level === 'elite') rec += " Pro-tip: Cycle with Agmatine for neuro-protection.";
                if (method === 'opt') rec += " Consider sublingual administration for immediate cholinergic response.";
            } else if (goal === 'sleep') {
                stackName = "The Circadian Reset";
                components = "Magnesium + 5-HTP";
                rec = "Designed to down-regulate the nervous system and optimize REM latency.";
                if (level === 'elite') rec += " Ideal for recovering from high-intensity cognitive flux.";
                if (method === 'opt') rec += " Use high-absorption magnesium glycinate for better CNS penetration.";
            } else {
                stackName = "The Performance Engine";
                components = "Agmatine Sulfate + Citicoline";
                rec = "Enhances blood flow and cognitive drive for high-output physical and mental sessions.";
                if (level === 'base') rec += " Start with lower dosages to assess systemic tolerance.";
                if (method === 'opt') rec += " Liquid suspension recommended for faster pre-workout activation.";
            }
            
            if (output) {
                output.innerHTML = `
                    <p><strong>${stackName}:</strong> ${components}</p>
                    <p style="color: var(--text-dim); font-size: 0.9rem;">${rec}</p>
                `;
            }
        }
    }

    window.resetQuiz = function() {
        currentQuizStep = 0;
        quizAnswers = [];
        const results = document.getElementById('quiz-results');
        const intro = document.getElementById('quiz-intro');
        if (results) results.classList.remove('active');
        if (intro) intro.style.display = 'block';
    };


    // Reading Time Estimator
    const content = document.querySelector('article');
    const readTimeDisplay = document.getElementById('reading-time');
    if (content && readTimeDisplay) {
        const text = content.innerText;
        const wpm = 225;
        const words = text.trim().split(/\s+/).length;
        const time = Math.ceil(words / wpm);
        readTimeDisplay.innerText = time;
    }

    // Theme Toggle
    const themeToggle = document.getElementById('theme-toggle');
    const body = document.body;
    const logo = document.querySelector('.logo-wrap img');

    // Check for saved theme
    const currentTheme = localStorage.getItem('theme');
    if (currentTheme === 'light') {
        body.classList.add('light-mode');
        if (themeToggle) themeToggle.textContent = '🌙 DARK MODE';
        if (logo) {
            // Check if logo src is relative to articles
            const isArticle = window.location.pathname.includes('/articles/');
            logo.src = isArticle ? '../topper-inverted.webp' : 'topper-inverted.webp';
        }
    }

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            body.classList.toggle('light-mode');

            let theme = 'dark';
            if (body.classList.contains('light-mode')) {
                theme = 'light';
                themeToggle.textContent = '🌙 DARK MODE';
                if (logo) {
                    const isArticle = window.location.pathname.includes('/articles/');
                    logo.src = isArticle ? '../topper-inverted.webp' : 'topper-inverted.webp';
                }
            } else {
                themeToggle.textContent = '☀️ LIGHT MODE';
                if (logo) {
                    const isArticle = window.location.pathname.includes('/articles/');
                    logo.src = isArticle ? '../topper.webp' : 'topper.webp';
                }
            }
            localStorage.setItem('theme', theme);
        });
    }

    // Custom Cursor Logic
    if (window.innerWidth >= 1024) {
        const cursor = document.createElement('div');
        cursor.className = 'custom-cursor';
        document.body.appendChild(cursor);

        const trailCount = 8;
        const trails = [];
        for (let i = 0; i < trailCount; i++) {
            const trail = document.createElement('div');
            trail.className = 'cursor-trail';
            document.body.appendChild(trail);
            trails.push({
                el: trail,
                x: 0,
                y: 0
            });
        }

        let mouseX = 0;
        let mouseY = 0;

        window.addEventListener('mousemove', (e) => {
            mouseX = e.clientX;
            mouseY = e.clientY;

            cursor.style.left = mouseX + 'px';
            cursor.style.top = mouseY + 'px';
        });

        function animateTrails() {
            let x = mouseX;
            let y = mouseY;

            trails.forEach((trail, index) => {
                const nextTrail = trails[index + 1] || { x: mouseX, y: mouseY };

                trail.x += (x - trail.x) * 0.3;
                trail.y += (y - trail.y) * 0.3;

                trail.el.style.left = trail.x + 'px';
                trail.el.style.top = trail.y + 'px';
                trail.el.style.opacity = 1 - (index / trailCount);
                trail.el.style.transform = `translate(-50%, -50%) scale(${1 - index / trailCount})`;

                x = trail.x;
                y = trail.y;
            });

            requestAnimationFrame(animateTrails);
        }
        animateTrails();

        // Cursor scaling on links
        const interactiveElements = document.querySelectorAll('a, button, .accordion-header, input');
        interactiveElements.forEach(el => {
            el.addEventListener('mouseenter', () => {
                cursor.style.width = '40px';
                cursor.style.height = '40px';
                cursor.style.backgroundColor = 'rgba(56, 189, 248, 0.3)';
            });
            el.addEventListener('mouseleave', () => {
                cursor.style.width = '20px';
                cursor.style.height = '20px';
                cursor.style.backgroundColor = 'var(--neon-blue)';
            });
        });
    }
});

// --- Syndicate Chat Widget Logic ---
document.addEventListener('DOMContentLoaded', () => {
    const body = document.body;

    // 1. Inject Chat HTML
    const chatHTML = `
        <div id="syndicate-chat-toggle" title="Initialize Syndicate Intelligence">
            <svg width="30" height="30" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"></path></svg>
        </div>
        <div id="chat-window">
            <div class="chat-header">
                <h4>SYNDICATE_INTEL</h4>
                <button id="close-chat" style="background:none; border:none; color:var(--text-dim); cursor:pointer;">&times;</button>
            </div>
            <div class="agent-selector">
                <span class="agent-chip active" data-agent="Ghost">Ghost</span>
                <span class="agent-chip" data-agent="Pulse">Pulse</span>
                <span class="agent-chip" data-agent="Spark">Spark</span>
            </div>
            <div class="chat-messages" id="chat-messages">
                <div class="message bot">System initialized. Agent Ghost online. How can the Syndicate assist your optimization today?</div>
            </div>
            <div class="chat-input-area">
                <input type="text" id="chat-input" placeholder="Enter transmission..." autocomplete="off">
                <button class="chat-send-btn" id="chat-send">
                    <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7"></path></svg>
                </button>
            </div>
        </div>
    `;
    body.insertAdjacentHTML('beforeend', chatHTML);

    const toggle = document.getElementById('syndicate-chat-toggle');
    const chatWindow = document.getElementById('chat-window');
    const closeBtn = document.getElementById('close-chat');
    const sendBtn = document.getElementById('chat-send');
    const input = document.getElementById('chat-input');
    const messagesContainer = document.getElementById('chat-messages');
    const chips = document.querySelectorAll('.agent-chip');

    let currentAgent = "Ghost";

    const agentPersonas = {
        "Ghost": "Security & Compliance Specialist. Focuses on privacy and system hardening.",
        "Pulse": "Performance Tuner. Expert in biometric optimization and XPU acceleration.",
        "Spark": "UI/UX Architect. Specializes in high-vibe interface design."
    };

    // Toggle Chat
    toggle.addEventListener('click', () => chatWindow.classList.toggle('active'));
    closeBtn.addEventListener('click', () => chatWindow.classList.remove('active'));

    // Agent Selection
    chips.forEach(chip => {
        chip.addEventListener('click', () => {
            chips.forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            currentAgent = chip.dataset.agent;
            addMessage(`Switching to Agent ${currentAgent}. ${agentPersonas[currentAgent]}`, 'bot');
        });
    });

    // Thinking Indicator
    function setThinking(isThinking) {
        const existing = document.getElementById('syndicate-thinking');
        if (isThinking && !existing) {
            const indicator = document.createElement('div');
            indicator.id = 'syndicate-thinking';
            indicator.className = 'message bot thinking';
            indicator.innerHTML = `<span class="dot"></span><span class="dot"></span><span class="dot"></span>`;
            messagesContainer.appendChild(indicator);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        } else if (!isThinking && existing) {
            existing.remove();
        }
    }

    // Send Message
    async function handleSend() {
        const text = input.value.trim();
        if (!text) return;

        addMessage(text, 'user');
        input.value = '';
        setThinking(true);

        // Integrated with Local Bot via Cloudflare Tunnel
        try {
            const response = await fetch('https://ai.hopes-and-dreams.ca/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: text
                })
            });

            if (!response.ok) throw new Error('Network response was not ok');

            const data = await response.json();
            setThinking(false);

            const botReply = data.reply || data.response || (typeof data === 'string' ? data : getBotResponse(text));
            addMessage(botReply, 'bot');
        } catch (error) {
            console.error('Syndicate Backend Error:', error);
            setThinking(false);
            // Fallback to local intelligence if backend is offline
            setTimeout(() => {
                const response = getBotResponse(text);
                addMessage(`[LOCAL_MODE] ${response}`, 'bot');
            }, 600);
        }
    }

    sendBtn.addEventListener('click', handleSend);
    input.addEventListener('keypress', (e) => { if (e.key === 'Enter') handleSend(); });

    function addMessage(text, side) {
        const msg = document.createElement('div');
        msg.className = `message ${side}`;
        msg.textContent = text;
        messagesContainer.appendChild(msg);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function getBotResponse(input) {
        const lowerInput = input.toLowerCase();

        // 1. Check Biohacking Codex (Resilience check)
        if (typeof codexData !== 'undefined') {
            for (const [key, value] of Object.entries(codexData)) {
                if (lowerInput.includes(key)) {
                    return `[${currentAgent}] Intelligence retrieved: ${value}`;
                }
            }
        }

        // 2. Intent-based responses
        if (lowerInput.includes("who are you") || lowerInput.includes("syndicate")) {
            return `[${currentAgent}] We are the Syndicate. A private research and development collective focused on neuro-optimization and biological sovereignty.`;
        }

        if (lowerInput.includes("hello") || lowerInput.includes("hi")) {
            return `[${currentAgent}] Transmission received. Ready for protocol analysis.`;
        }

        if (lowerInput.includes("facebook") || lowerInput.includes("fb")) {
            return `[${currentAgent}] Our official community intelligence is hosted on Facebook. Use the link in the footer to access the full research archive.`;
        }

        // 3. Fallback
        return `[${currentAgent}] Query logged. My current intelligence parameters are limited to known protocols. Try asking about 'Alpha GPC', 'HRV', or 'The Syndicate'.`;
    }
});

/**
 * BRIDGE FOR FACEBOOK BOT LOGIC
 * To integrate the external Hopes-and-Dreams-Facebook-bot:
 * 1. Host the bot's logic as a serverless function or API.
 * 2. Replace the 'getBotResponse' function or the logic in 'handleSend'
 *    with a fetch() call to your API endpoint.
 *
 * Example:
 * async function getExternalBotResponse(text) {
 *    const response = await fetch('YOUR_API_ENDPOINT', {
 *        method: 'POST',
 *        body: JSON.stringify({ message: text, agent: currentAgent })
 *    });
 *    const data = await response.json();
 *    return data.reply;
 * }
 */
