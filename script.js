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

    // 1. Biohacking Codex
    const codexData = {
        'ache': 'Acetylcholinesterase: An enzyme that breaks down acetylcholine. Inhibiting this (e.g. with Huperzine-A) increases neuro-connectivity.',
        'bdnf': 'Brain-Derived Neurotrophic Factor: A protein that supports the survival of existing neurons and encourages the growth of new ones.',
        'choline': 'A precursor to acetylcholine, essential for memory, mood, and muscle control.',
        'gaba': 'Gamma-Aminobutyric Acid: The primary inhibitory neurotransmitter in the CNS, crucial for reducing neuronal excitability and promoting relaxation.',
        'glycine': 'An amino acid that acts as a neurotransmitter, improving sleep quality and lowering core body temperature.',
        'hrv': 'Heart Rate Variability: The variation in time between heartbeats. A higher HRV typically indicates better recovery and nervous system balance.',
        'l-theanine': 'An amino acid found in tea that promotes relaxation without drowsiness, often stacked with caffeine for "calm focus".',
        'nootropic': 'Compounds that enhance cognitive function, particularly executive functions, memory, creativity, or motivation.',
        'rem': 'Rapid Eye Movement: The sleep stage associated with vivid dreaming and memory consolidation.',
        'yuschak': 'The gold-standard protocol for lucidity involving specific supplement timing during the WBTB window.'
    };

    const codexSearch = document.getElementById('codex-search');
    if (codexSearch) {
        codexSearch.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            const resultBox = document.getElementById('codex-results');
            if (query.length < 2) {
                resultBox.innerHTML = '<em>Search for a term to initialize protocol data.</em>';
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

    const freqSlider = document.getElementById('freq-slider');
    const freqValDisplay = document.getElementById('freq-val');
    const freqType = document.getElementById('freq-type');
    const freqDesc = document.getElementById('freq-desc');

    function updateFreqDisplay(val) {
        if (freqValDisplay) freqValDisplay.textContent = val;

        let type = "";
        let desc = "";

        if (val < 4) {
            type = "Delta State";
            desc = "Deep sleep, physical restoration, and restorative healing.";
        } else if (val < 8) {
            type = "Theta State";
            desc = "Deep relaxation, meditation, creativity, and subconscious access.";
        } else if (val < 14) {
            type = "Alpha State";
            desc = "Relaxed alertness, stress relief, calm focus, and learning.";
        } else if (val < 30) {
            type = "Beta State";
            desc = "Active thinking, problem-solving, analytical tasks, and alertness.";
        } else {
            type = "Gamma State";
            desc = "Peak focus, high-level cognition, memory recall, and insight.";
        }

        if (freqType) freqType.textContent = type;
        if (freqDesc) freqDesc.textContent = desc;

        if (binauralNodes && window.audioCtx) {
            const freq = parseFloat(val);
            binauralNodes.oscR.frequency.setTargetAtTime(baseFreq + freq, window.audioCtx.currentTime, 0.1);
        }
    }

    if (freqSlider) {
        freqSlider.addEventListener('input', (e) => updateFreqDisplay(e.target.value));
    }

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
            const freq = freqSlider ? parseFloat(freqSlider.value) : 40;
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
            logo.src = isArticle ? '../topper-inverted.png' : 'topper-inverted.png';
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
                    logo.src = isArticle ? '../topper-inverted.png' : 'topper-inverted.png';
                }
            } else {
                themeToggle.textContent = '☀️ LIGHT MODE';
                if (logo) {
                    const isArticle = window.location.pathname.includes('/articles/');
                    logo.src = isArticle ? '../topper.png' : 'topper.png';
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
