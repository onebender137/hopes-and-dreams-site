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

    // --- Video Splash Intro Skip Logic ---
    const skipBtn = document.getElementById('skip-video-btn');
    if (skipBtn) {
        skipBtn.addEventListener('click', () => {
            const splash = document.getElementById('splash-screen');
            if (splash) {
                splash.style.transition = 'opacity 0.5s ease';
                splash.style.opacity = '0';
                setTimeout(() => {
                    splash.remove();
                    // Set the session token so it remembers they skipped it
                    sessionStorage.setItem('hopesSplashSeen', "true");
                }, 500);
            }
        });
    }

    const observerOptions = {
        threshold: 0,
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

    // --- Typewriter Effect for Timestamps ---
    document.querySelectorAll('.timestamp-live[data-timestamp]').forEach(el => {
        const text = el.getAttribute('data-timestamp');
        if (!text) return;

        el.innerHTML = '<span class="typing-text"></span><span class="cursor"></span>';
        const typingText = el.querySelector('.typing-text');
        let i = 0;
        const typingSpeed = 40;

        function typeWriter() {
            if (i < text.length) {
                typingText.textContent += text.charAt(i);
                i++;
                setTimeout(typeWriter, typingSpeed);
            }
        }
        setTimeout(typeWriter, 500);
    });

    // --- Decryption (Boot-Up) Sequence ---
    // Target all structural elements within the article content for the decryption effect
    const articleElements = document.querySelectorAll('.article-container p, .article-container h2, .article-container li, .intel-burst p, .intel-burst h2, .intel-burst li');
    articleElements.forEach((el, index) => {
        el.classList.add('decryption-text');
        // Staggered reveal based on index
        setTimeout(() => {
            el.classList.add('decrypted');
        }, 500 + (index * 150)); // Delay each element slightly for a better visual sequence
    });

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
        [caffMg, caffHours, caffBedtime].forEach(el => el.addEventListener('input', () => {
            updateCaffeine();
            calculateReadinessScore();
        }));
        updateCaffeine();
    }

    // 0.1 Autophagy Milestone Tracker
    const fastRange = document.getElementById('fast-range');
    const fastDisplay = document.getElementById('fast-display');

    // 0.2 Neural Readiness Logic
    function calculateReadinessScore() {
        const progress = document.getElementById('readiness-progress');
        const valueDisplay = document.getElementById('readiness-value');
        const adviceEl = document.getElementById('readiness-advice');
        if (!progress || !valueDisplay) return;

        let score = 0;
        const factors = {
            caffeine: 25,
            fasting: 25,
            sleep: 25,
            protocols: 25
        };

        // 1. Caffeine Factor (Residual)
        const caffMgEl = document.getElementById('caff-mg');
        const caffHoursEl = document.getElementById('caff-hours');
        const caffBedtimeEl = document.getElementById('caff-bedtime');

        const initial = caffMgEl ? parseFloat(caffMgEl.value) : 0;
        const elapsed = caffHoursEl ? parseFloat(caffHoursEl.value) : 0;
        const tillBed = caffBedtimeEl ? parseFloat(caffBedtimeEl.value) : 10;
        const halfLife = 5.7;
        const residual = initial * Math.pow(0.5, (elapsed + tillBed) / halfLife);

        // Lower residual = better readiness
        let caffScore = 100;
        if (residual > 50) caffScore = 0;
        else if (residual > 0) caffScore = 100 - (residual * 2);
        factors.caffeine = (caffScore / 100) * 25;

        // 2. Fasting Factor
        const fastRangeEl = document.getElementById('fast-range');
        const fastHours = fastRangeEl ? parseInt(fastRangeEl.value) : 0;
        let fastScore = (fastHours / 48) * 100;
        if (fastScore > 100) fastScore = 100;
        factors.fasting = (fastScore / 100) * 25;

        // 3. Sleep Factor
        const wakeInput = document.getElementById('wake-time');
        factors.sleep = wakeInput && wakeInput.value ? 25 : 0;

        // 4. Protocols Factor (Checklist)
        const checks = document.querySelectorAll('.protocol-check');
        const checked = document.querySelectorAll('.protocol-check:checked');
        let protocolScore = checks.length > 0 ? (checked.length / checks.length) * 100 : 0;
        factors.protocols = (protocolScore / 100) * 25;

        score = Math.round(factors.caffeine + factors.fasting + factors.sleep + factors.protocols);

        // Update UI
        progress.setAttribute('stroke-dasharray', `${score}, 100`);
        valueDisplay.textContent = score + "%";

        // Update bars
        const caffBar = document.querySelector('#factor-caffeine .factor-fill');
        const fastBar = document.querySelector('#factor-fasting .factor-fill');
        const sleepBar = document.querySelector('#factor-sleep .factor-fill');
        const protocolBar = document.querySelector('#factor-protocols .factor-fill');

        if (caffBar) caffBar.style.width = (factors.caffeine * 4) + "%";
        if (fastBar) fastBar.style.width = (factors.fasting * 4) + "%";
        if (sleepBar) sleepBar.style.width = (factors.sleep * 4) + "%";
        if (protocolBar) protocolBar.style.width = (factors.protocols * 4) + "%";

        // Update Advice
        let advice = "System online. Initialize protocols to calculate performance readiness.";
        if (score >= 90) advice = "EXTREME READINESS. All neural systems optimized. Deploy high-value cognitive tasks.";
        else if (score >= 70) advice = "OPTIMAL STATE. Neuro-chemical balance achieved. Proceed with building.";
        else if (score >= 50) advice = "NOMINAL OPERATING CAPACITY. Moderate biological noise detected.";
        else advice = "SYSTEM CRITICAL. Prioritize recovery and metabolic clearing protocols.";

        if (adviceEl) adviceEl.textContent = `"${advice}"`;
    }

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
        fastRange.addEventListener('input', () => {
            updateAutophagy();
            calculateReadinessScore();
        });
        updateAutophagy();
    }

    // 0.3 Interactive Neural Map Logic
    const brainRegions = document.querySelectorAll('.brain-region');
    const neuralInfoBox = document.getElementById('neural-info-box');
    const neuralStatus = document.getElementById('neural-status');

    const regionProtocols = {
        'prefrontal cortex': 'Focus Stack (Alpha GPC + Uridine)',
        'thalamus': 'Sleep Architecture (Magnesium + 5-HTP)',
        'vagus nerve': 'Resilience Protocol (Ashwagandha + Rhodiola)',
        'hippocampus': 'Memory Stack (Lion\'s Mane + Bacopa)',
        'amygdala': 'Zen Protocol (L-Theanine + Magnesium)',
        'pineal gland': 'Circadian Reset (Magnesium Bisglycinate)',
        'cerebellum': 'Flow State Engine (Creatine + NALT)'
    };

    brainRegions.forEach(region => {
        const handleRegionSelection = () => {
            const targetRegion = region.getAttribute('data-region');

            // Toggle active class
            brainRegions.forEach(r => r.classList.remove('active'));
            region.classList.add('active');

            if (neuralStatus) {
                neuralStatus.textContent = `DEEP ANALYSIS: ${targetRegion.toUpperCase()}`;
                neuralStatus.style.color = 'var(--neon-blue)';
            }

            if (typeof codexData !== 'undefined' && neuralInfoBox) {
                const info = codexData[targetRegion];
                const protocol = regionProtocols[targetRegion];

                if (info) {
                    neuralInfoBox.innerHTML = `
                        <p style="color: var(--neon-gold); font-weight: 900; margin-bottom: 10px; text-transform: uppercase;">${targetRegion}</p>
                        <p style="font-size: 0.9rem; margin-bottom: 15px;">${info}</p>
                        <div style="background: rgba(56, 189, 248, 0.1); padding: 10px; border-radius: 8px; border-left: 3px solid var(--neon-blue);">
                            <p style="font-size: 0.75rem; color: var(--neon-blue); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; font-weight: 700;">Targeted Protocol:</p>
                            <p style="font-size: 0.85rem; font-weight: 700;">${protocol || 'Consult Syndicate Shop'}</p>
                            <a href="shop.html" style="font-size: 0.7rem; color: var(--neon-gold); text-decoration: none; display: inline-block; margin-top: 5px; text-transform: uppercase; font-weight: 900;">Access Procurement &rarr;</a>
                        </div>
                    `;
                    neuralInfoBox.classList.add('active');
                    // Scroll to info for visibility on mobile
                    neuralInfoBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }
            }
        };

        region.addEventListener('click', handleRegionSelection);
        region.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                handleRegionSelection();
            }
        });

        region.addEventListener('mouseenter', () => {
            const targetRegion = region.getAttribute('data-region');
            if (neuralStatus) {
                neuralStatus.textContent = `INITIALIZING [${targetRegion.toUpperCase()}]...`;
                neuralStatus.style.color = 'var(--neon-gold)';
            }
        });

        region.addEventListener('mouseleave', () => {
            if (neuralStatus && !document.querySelector('.brain-region.active')) {
                neuralStatus.textContent = 'Interface Ready';
                neuralStatus.style.color = 'var(--neon-gold)';
            } else if (neuralStatus) {
                const activeRegion = document.querySelector('.brain-region.active');
                if (activeRegion) {
                    neuralStatus.textContent = `DEEP ANALYSIS: ${activeRegion.getAttribute('data-region').toUpperCase()}`;
                    neuralStatus.style.color = 'var(--neon-blue)';
                }
            }
        });
    });

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
        wakeInput.addEventListener('change', () => {
            calculateSleepTimes();
            calculateReadinessScore();
        });
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
            calculateReadinessScore();
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
                { text: "Cognitive Flux (Deep Work & Memory)", value: "focus" },
                { text: "System Recovery (Sleep & Mood)", value: "sleep" },
                { text: "Bio-Output (Energy & Performance)", value: "energy" },
                { text: "Subconscious Exploration (Lucid Dreaming)", value: "dream" },
                { text: "Neural Resilience (Stress Management)", value: "resilience" },
                { text: "Long-Term Maintenance (Brain Health)", value: "maintenance" }
            ]
        },
        {
            q: "How would you describe your current stress levels?",
            options: [
                { text: "Baseline (Stable)", value: "low" },
                { text: "Elevated (High Pressure)", value: "high" },
                { text: "Critical (Burnout Risk)", value: "critical" }
            ]
        },
        {
            q: "Experience level with neuro-augmentations?",
            options: [
                { text: "Baseline (Beginner)", value: "base" },
                { text: "Augmented (Intermediate)", value: "aug" },
                { text: "Elite (Advanced)", value: "elite" }
            ]
        },
        {
            q: "Primary delivery method preference?",
            options: [
                { text: "Standard (Capsules/Powder)", value: "std" },
                { text: "Rapid-Onset (Liquid/Sublingual)", value: "fast" }
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
            const stress = quizAnswers[1];
            const level = quizAnswers[2];
            const method = quizAnswers[3];

            let stackName = "";
            let components = [];
            let details = "";
            let dosage = "";

            // Logic for Stack Recommendation
            if (goal === 'focus') {
                stackName = "The Architect Protocol";
                components = ["alpha-gpc", "citicoline", "l-theanine", "bacopa", "mag-threonate"];
                dosage = "Alpha GPC: 300mg, Citicoline: 250mg, L-Theanine: 200mg, Bacopa: 300mg, Mag-Threonate: 144mg (as elemental).";
                details = "Designed for sustained neural plasticity and linguistic fluidity. The cholinergic foundation paired with L-Theanine ensures sharp focus, while Bacopa and Magnesium L-Threonate support synapse density and memory consolidation.";
                if (level === 'elite') {
                    components.push("nicotine");
                    dosage += " Nicotine: 2mg patch (optional for high-stakes windows).";
                }
            } else if (goal === 'sleep') {
                stackName = "The Circadian Reset";
                components = ["magnesium", "5-htp", "l-theanine", "phosphatidylserine"];
                dosage = "Magnesium Bisglycinate: 400mg, 5-HTP: 100mg, L-Theanine: 200mg, Phosphatidylserine: 100mg.";
                details = "Optimizes the transition into deep sleep. Phosphatidylserine helps lower nocturnal cortisol, while L-Theanine increases alpha-wave activity for restorative rest.";
            } else if (goal === 'energy') {
                stackName = "The Kinetic Engine";
                components = ["agmatine", "alpha-gpc", "nalt", "creatine", "pqq", "coq10"];
                dosage = "Agmatine: 500mg, Alpha GPC: 150mg, NALT: 350mg, Creatine: 5g, PQQ: 20mg, CoQ10: 100mg.";
                details = "Focused on dopamine synthesis and mitochondrial energy. NALT and Agmatine optimize drive, while the PQQ/CoQ10 synergy ensures peak cellular ATP output.";
            } else if (goal === 'dream') {
                stackName = "The Oneironaut Stack";
                components = ["huperzine", "alpha-gpc", "citicoline", "uridine"];
                dosage = "Huperzine-A: 200mcg, Alpha GPC: 300mg, Citicoline: 250mg, Uridine: 250mg.";
                details = "Maximizes acetylcholine concentration during the REM-dominant hours. Uridine supports the synaptic plasticity required for vivid dream recall.";
            } else if (goal === 'resilience') {
                stackName = "The Zen Master";
                components = ["ashwagandha", "rhodiola", "l-theanine", "magnesium", "kratom"];
                dosage = "Ashwagandha: 600mg, Rhodiola: 300mg, L-Theanine: 200mg, Magnesium: 200mg, Kratom: As directed.";
                details = "The ultimate shield against burnout. Rhodiola provides acute anti-fatigue effects, while Ashwagandha, Magnesium, and Kratom manage systemic stress and resilience.";
            } else if (goal === 'maintenance') {
                stackName = "The Neuro-Vanguard";
                components = ["lions-mane", "omega-3", "citicoline", "uridine", "creatine", "nac", "pqq", "d3-k2", "nattokinase", "turkey-tail"];
                dosage = "Lion's Mane: 1000mg, Omega-3: 2000mg, Citicoline: 250mg, Uridine: 250mg, Creatine: 3g, NAC: 600mg, PQQ: 20mg, D3+K2: 5000IU, Nattokinase: 2000FU, Turkey Tail: 500mg.";
                details = "The ultimate foundation for long-term biological sovereignty. Combines neuro-genesis (Lion's Mane) and mitochondrial support (PQQ) with systemic antioxidant (NAC), cardiovascular (Nattokinase), and immune (Turkey Tail) optimization.";
            }

            if (output) {
                output.innerHTML = `
                    <p style="color: var(--neon-gold); font-size: 1.2rem; font-weight: 900; text-transform: uppercase;">${stackName}</p>
                    <p style="margin-bottom: 15px;"><strong>Stack Components:</strong> ${components.join(', ')}</p>
                    <div style="background: rgba(255,255,255,0.03); padding: 15px; border-radius: 10px; margin-bottom: 15px; text-align: left;">
                        <p style="font-size: 0.85rem; color: var(--neon-blue); margin-bottom: 5px;"><strong>RECOMMENDED DOSAGE:</strong></p>
                        <p style="font-size: 0.9rem; margin-bottom: 10px;">${dosage}</p>
                        <p style="font-size: 0.85rem; color: var(--neon-blue); margin-bottom: 5px;"><strong>PROTOCOL DETAILS:</strong></p>
                        <p style="font-size: 0.9rem; color: var(--text-dim); line-height: 1.4;">${details}</p>
                    </div>
                    <p style="font-size: 0.8rem; font-style: italic; color: var(--neon-gold);">Note: Recommended products in the procurement list have been highlighted below.</p>
                `;
            }

            // Highlight Cards
            highlightShopCards(components);
            if (window.buildRxReadout) window.buildRxReadout(stackName, components, dosage, details);
        }
    }

    function highlightShopCards(productIds) {
        // Clear previous highlights
        document.querySelectorAll('.item-card').forEach(card => card.classList.remove('highlight-card'));

        // Add new highlights
        productIds.forEach(id => {
            const card = document.querySelector(`.item-card[data-product="${id}"]`);
            if (card) {
                card.classList.add('highlight-card');
                // Optional: Scroll to the grid after a short delay
                // card.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        });
    }

    window.resetQuiz = function() {
        currentQuizStep = 0;
        quizAnswers = [];
        const results = document.getElementById('quiz-results');
        const intro = document.getElementById('quiz-intro');
        if (results) results.classList.remove('active');
        if (intro) intro.style.display = 'block';
        document.querySelectorAll('.item-card').forEach(card => card.classList.remove('highlight-card'));
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
    const themeToggleLander = document.getElementById('theme-toggle-lander');
    const body = document.body;
    // === SYNDICATE_KB: local knowledge, loaded once ===
    if(!window.SYNDICATE_KB){
        fetch('/chat-knowledge.json').then(function(r){return r.ok?r.json():null;})
            .then(function(kb){window.SYNDICATE_KB=kb;}).catch(function(){});
    }

    const logo = document.querySelector('.logo-wrap img');

    // Check for saved theme
    const currentTheme = localStorage.getItem('theme');
    if (currentTheme === 'light') {
        body.classList.add('light-mode');
        if (themeToggle) themeToggle.textContent = '🌙 DARK MODE';
        if (themeToggleLander) themeToggleLander.textContent = '🌙 DARK MODE';
        if (logo) {
            // Check if logo src is relative to articles
            const isArticle = window.location.pathname.includes('/articles/');
            logo.src = isArticle ? '../topper-inverted.png' : 'topper-inverted.png';
        }
        const heroBrain = document.getElementById('hero-brain-image');
        if (heroBrain) heroBrain.src = 'topper-inverted.png';
        // Swap the SVG <image> href too (this is the actually-visible brain on the landing)
        const svgBrain = document.querySelector('#hero-brain-svg image');
        if (svgBrain) svgBrain.setAttribute('href', 'topper-inverted.png');
    }

    // Lander pill fires same logic as main toggle
    if (themeToggleLander) {
        themeToggleLander.addEventListener('click', () => themeToggle && themeToggle.click());
    }
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            body.classList.toggle('light-mode');

            let theme = 'dark';
            if (body.classList.contains('light-mode')) {
                theme = 'light';
                themeToggle.textContent = '🌙 DARK MODE';
                if (themeToggleLander) themeToggleLander.textContent = '🌙 DARK MODE';
                if (logo) {
                    const isArticle = window.location.pathname.includes('/articles/');
                    logo.src = isArticle ? '../topper-inverted.png' : 'topper-inverted.png';
                }
                const heroBrainLight = document.getElementById('hero-brain-image');
                if (heroBrainLight) heroBrainLight.src = 'topper-inverted.png';
                const svgBrainLight = document.querySelector('#hero-brain-svg image');
                if (svgBrainLight) svgBrainLight.setAttribute('href', 'topper-inverted.png');
            } else {
                themeToggle.textContent = '☀️ LIGHT MODE';
                if (themeToggleLander) themeToggleLander.textContent = '☀️ LIGHT MODE';
                if (logo) {
                    const isArticle = window.location.pathname.includes('/articles/');
                    logo.src = isArticle ? '../topper.png' : 'topper.png';
                }
                const heroBrainDark = document.getElementById('hero-brain-image');
                if (heroBrainDark) heroBrainDark.src = 'topper.png';
                const svgBrainDark = document.querySelector('#hero-brain-svg image');
                if (svgBrainDark) svgBrainDark.setAttribute('href', 'topper.png');
            }
            localStorage.setItem('theme', theme);
        });
    }

    // --- Sticky Readiness Command Shrink Logic ---
    const readinessCommand = document.getElementById('readiness-command');
    if (readinessCommand) {
        // Use a placeholder to prevent layout shift when widget goes fixed
        const placeholder = document.createElement('div');
        placeholder.style.display = 'none';
        placeholder.style.height = readinessCommand.offsetHeight + 'px';
        placeholder.style.margin = getComputedStyle(readinessCommand).margin;
        readinessCommand.parentNode.insertBefore(placeholder, readinessCommand);

        // Capture original position relative to the document
        const getAbsoluteOffset = () => {
            const rect = readinessCommand.classList.contains('compact')
                ? placeholder.getBoundingClientRect()
                : readinessCommand.getBoundingClientRect();
            return rect.top + window.pageYOffset;
        };

        let originalOffset = getAbsoluteOffset();

        // Recalculate offset on resize in case layout shifts
        window.addEventListener('resize', () => {
            if (!readinessCommand.classList.contains('compact')) {
                originalOffset = getAbsoluteOffset();
                placeholder.style.height = readinessCommand.offsetHeight + 'px';
            }
        });

        window.addEventListener('scroll', () => {
            const currentScroll = window.pageYOffset || document.documentElement.scrollTop;

            // Trigger compact mode once the viewport reaches the widget's original position
            if (currentScroll > originalOffset) {
                if (!readinessCommand.classList.contains('compact')) {
                    placeholder.style.height = readinessCommand.offsetHeight + 'px';
                    placeholder.style.display = 'block';
                    readinessCommand.classList.add('compact');
                }
            } else {
                if (readinessCommand.classList.contains('compact')) {
                    readinessCommand.classList.remove('compact');
                    placeholder.style.display = 'none';
                }
            }
        });

        // Click to return to original position
        readinessCommand.addEventListener('click', (e) => {
            if (readinessCommand.classList.contains('compact')) {
                window.scrollTo({
                    top: originalOffset - 20,
                    behavior: 'smooth'
                });
            }
        });
    }

    // Initial Score Calculation
    if (typeof calculateReadinessScore === 'function') {
        calculateReadinessScore();
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
        <button id="syndicate-chat-toggle" title="Initialize Syndicate Intelligence" aria-label="Open Syndicate Chat">
            <svg width="30" height="30" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"></path></svg>
        </button>
        <div id="chat-window">
            <div class="chat-header">
                <h4>SYNDICATE_INTEL</h4>
                <button id="close-chat" style="background:none; border:none; color:var(--text-dim); cursor:pointer;">&times;</button>
            </div>
            <div class="agent-selector" style="display:none;">
                <span class="agent-chip active" data-agent="Ghost">Ghost</span>
                <span class="agent-chip" data-agent="Pulse">Pulse</span>
                <span class="agent-chip" data-agent="Spark">Spark</span>
            </div>
            <div class="chat-messages" id="chat-messages">
                <div class="message bot">You're in the Syndicate. Ask me about a supplement, a tool, or where to find something on the site — I'll point you the right way. // Do your own research, don't be a statistic.</div>
            </div>
            <div class="chat-input-area">
                <button class="chat-send-btn" id="chat-mic" title="Voice Input (Requires Chrome/Brave permissions)">
                    <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"></path></svg>
                </button>
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
    const micBtn = document.getElementById('chat-mic');
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
    let thinkingTimeout;
    function setThinking(isThinking) {
        const existing = document.getElementById('syndicate-thinking');
        const statusMsg = document.getElementById('syndicate-status');

        if (isThinking && !existing) {
            const indicator = document.createElement('div');
            indicator.id = 'syndicate-thinking';
            indicator.className = 'message bot thinking';
            indicator.innerHTML = `<span class="dot"></span><span class="dot"></span><span class="dot"></span>`;
            messagesContainer.appendChild(indicator);

            // UX for slow MSI Claw inference
            thinkingTimeout = setTimeout(() => {
                const status = document.createElement('div');
                status.id = 'syndicate-status';
                status.style.fontSize = '0.7rem';
                status.style.color = 'var(--neon-gold)';
                status.style.opacity = '0.6';
                status.style.marginTop = '-10px';
                status.style.marginLeft = '15px';
                status.textContent = "Indexing neural chunks via MSI Claw...";
                messagesContainer.appendChild(status);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }, 4000);

            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        } else if (!isThinking) {
            if (existing) existing.remove();
            if (statusMsg) statusMsg.remove();
            clearTimeout(thinkingTimeout);
        }
    }

    // Send Message
    async function handleSend() {
        const text = input.value.trim();
        if (!text) return;

        addMessage(text, 'user');
        input.value = '';
        setThinking(true);
        setTimeout(function(){ setThinking(false); addMessage(getBotResponse(text), 'bot'); }, 450 + Math.random()*350);
    }

    sendBtn.addEventListener('click', handleSend);
    input.addEventListener('keypress', (e) => { if (e.key === 'Enter') handleSend(); });

    // Voice Input Logic
    if (micBtn && ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;

        recognition.onstart = () => {
            micBtn.style.color = 'var(--neon-blue)';
            micBtn.classList.add('pulse');
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            input.value = transcript;
            handleSend();
        };

        recognition.onend = () => {
            micBtn.style.color = 'var(--neon-gold)';
            micBtn.classList.remove('pulse');
        };

        micBtn.addEventListener('click', () => {
            recognition.start();
        });
    } else if (micBtn) {
        micBtn.style.display = 'none';
    }

    function addMessage(text, side) {
        const msg = document.createElement('div');
        msg.className = `message ${side}`;
        // bot content is our own trusted knowledge file -> render HTML (clickable links);
        // user content stays as plain text so nothing they type can inject markup.
        if (side === 'bot') { msg.innerHTML = text; }
        else { msg.textContent = text; }
        messagesContainer.appendChild(msg);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function getBotResponse(input){
        if(!window.SYNDICATE_KB||!window.SYNDICATE_KB.entries){return "Still booting my knowledge core \u2014 give me a second and ask again.";}
        var q=(input||'').toLowerCase().replace(/[^a-z0-9\s]/g,' ');
        var words=q.split(/\s+/).filter(Boolean);
        var best=null,bestScore=0;
        for(var i=0;i<window.SYNDICATE_KB.entries.length;i++){
            var e=window.SYNDICATE_KB.entries[i]; var score=0;
            for(var j=0;j<e.keywords.length;j++){
                var k=(e.keywords[j]||'').toLowerCase().replace(/[^a-z0-9\s]/g,' '); if(!k)continue;
                if(q.indexOf(k)>=0)score+=(k.indexOf(' ')>=0?3:2);
                else if(words.some(function(w){return w.length>3&&k.split(' ').indexOf(w)>=0;}))score+=1;
            }
            if(score>bestScore){bestScore=score;best=e;}
        }
        if(best&&bestScore>=2){
            var reply=best.answer;
            if(best.cta_href){reply+='<br><br><a href="'+best.cta_href+'" class="chat-cta">\u25B6 '+(best.cta_label||'Learn more')+'</a>';}
            return reply;
        }
        return window.SYNDICATE_KB.fallback||"Not sure on that one \u2014 try the Intel Hub search, or ask about a supplement, the Optimization Hub, or the Cipher.";
    }
});

// Syndicate Matrix Gutter Logic (High-Performance Canvas Edition)
document.addEventListener('DOMContentLoaded', () => {
    if (window.innerWidth <= 1024) return; // Abort on mobile

    const createGutterCanvas = (side) => {
        const canvas = document.createElement('canvas');
        canvas.className = `data-gutter ${side}`;
        canvas.style.position = 'fixed';
        canvas.style.top = '0';
        canvas.style[side] = '0'; // Flush with the edge to avoid "blinds" gap
        canvas.style.width = '80px'; // Narrower to avoid cutting off elements
        canvas.style.height = '100vh';
        canvas.style.zIndex = '1';
        canvas.style.pointerEvents = 'none';
        canvas.style.background = 'var(--bg-main)';
        canvas.style.transition = 'background-color var(--transition-speed)';
        document.body.appendChild(canvas);
        return canvas;
    };

    const leftCanvas = createGutterCanvas('left');
    const rightCanvas = createGutterCanvas('right');
    const canvases = [leftCanvas, rightCanvas];
    const contexts = canvases.map(c => c.getContext('2d'));

    const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%^&*ｦｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ";
    const fontSize = 14; // Slightly smaller font for narrower gutters
    let columns;
    let drops;
    let matrixBgColor = "rgba(10, 15, 43, 0.15)";

    function updateMatrixBgColor() {
        // Read the CSS variable directly from body to get the target value instantly
        const bodyStyle = getComputedStyle(document.body);
        let bgColor = bodyStyle.getPropertyValue('--bg-main').trim();

        // Robust color parsing: create a dummy element to resolve hex/var to rgb
        const temp = document.createElement('div');
        temp.style.color = bgColor;
        document.body.appendChild(temp);
        const resolvedColor = getComputedStyle(temp).color;
        document.body.removeChild(temp);

        // Extract R, G, B values from "rgb(r, g, b)" or "rgba(r, g, b, a)"
        const match = resolvedColor.match(/\d+/g);
        if (match && match.length >= 3) {
            // Use 0.15 alpha for trail effect, but ensures RGB matches the theme exactly
            matrixBgColor = `rgba(${match[0]}, ${match[1]}, ${match[2]}, 0.15)`;
        }
    }

    function init() {
        canvases.forEach(canvas => {
            canvas.width = 80; // Match CSS width
            canvas.height = window.innerHeight;
        });
        columns = Math.floor(80 / fontSize);
        drops = Array(columns).fill(1);
        updateMatrixBgColor();
    }

    // Update background color when theme changes
    const themeToggleEl = document.getElementById('theme-toggle');
    if (themeToggleEl) {
        themeToggleEl.addEventListener('click', () => {
            // The class toggle happens immediately, update color in the next tick
            setTimeout(updateMatrixBgColor, 0);
        });
    }

    function draw() {
        contexts.forEach((ctx, i) => {
            const isLightMode = document.body.classList.contains('light-mode');

            ctx.fillStyle = matrixBgColor;
            ctx.fillRect(0, 0, canvases[i].width, canvases[i].height);

            // Matrix Text Styling
            ctx.fillStyle = isLightMode ? "#0284c7" : "#38bdf8"; 
            ctx.font = `${fontSize}px monospace`;
            ctx.shadowBlur = 8;
            ctx.shadowColor = isLightMode ? "rgba(2, 132, 199, 0.5)" : "rgba(56, 189, 248, 0.5)";

            for (let j = 0; j < drops.length; j++) {
                const text = chars.charAt(Math.floor(Math.random() * chars.length));
                const x = j * fontSize;
                const y = drops[j] * fontSize;

                ctx.fillText(text, x, y);

                // Reset drop to top randomly after it crosses screen
                if (y > canvases[i].height && Math.random() > 0.975) {
                    drops[j] = 0;
                }
                drops[j]++;
            }
        });
    }

    init();
    window.addEventListener('resize', init);
    // Slowed down from 33ms to 65ms for a more readable, relaxed pace
    setInterval(draw, 65);
}); // <--- THIS is the bracket that went missing!

// --- Article Navigation Scroller Logic ---
document.addEventListener('DOMContentLoaded', () => {
    const navPlaceholder = document.getElementById('article-navigation');
    if (!navPlaceholder) return;

    // Determine if we are in an article page
    const isArticle = window.location.pathname.includes('/articles/');
    if (!isArticle) return;

    const transmissionsUrl = '../transmissions.json';

    async function initializeArticleNav() {
        console.log("Initializing Syndicate Transmission Scroller (JSON Optimized)...");
        try {
            const response = await fetch(transmissionsUrl);
            if (!response.ok) {
                console.error(`Failed to fetch transmissions: ${response.status}`);
                return;
            }
            const archiveItems = await response.json();

            console.log(`Found ${archiveItems.length} items in optimized archive.`);
            if (archiveItems.length === 0) return;

            const currentPath = window.location.pathname.split('/').pop();
            let currentIndex = archiveItems.findIndex(item => item.href.includes(currentPath));
            console.log(`Current article index: ${currentIndex}`);

            // Generate the scroller HTML
            let navHTML = `
                <h2 class="section-title">Syndicate Transmissions</h2>
                <div class="nav-scroller-container">
                    <div class="nav-scroller" id="nav-scroller">
            `;

            archiveItems.forEach((item, index) => {
                const title = item.title;
                const date = item.date;
                const href = item.href;
                const isActive = index === currentIndex;
                const isPrev = index === currentIndex + 1; // Reverse chronological order
                const isNext = index === currentIndex - 1;

                let cardClass = 'nav-card';
                if (isActive) cardClass += ' active';
                if (isPrev) cardClass += ' prev-card';
                if (isNext) cardClass += ' next-card';

                navHTML += `
                    <a href="../${href}" class="${cardClass}" data-index="${index}">
                        <div>
                            <div class="nav-meta">${date}</div>
                            <h4>${title}</h4>
                        </div>
                    </a>
                `;
            });

            navHTML += `
                    </div>
                </div>
            `;

            navPlaceholder.innerHTML = navHTML;

            // Scroll the active card into center view
            const scroller = document.getElementById('nav-scroller');
            const activeCard = scroller.querySelector('.nav-card.active');
            if (activeCard) {
                setTimeout(() => {
                    const scrollLeft = activeCard.offsetLeft - (scroller.offsetWidth / 2) + (activeCard.offsetWidth / 2);
                    scroller.scrollTo({ left: scrollLeft, behavior: 'smooth' });
                }, 500);
            }

            // Click and Drag scrolling
            let isDown = false;
            let startX;
            let scrollLeft;

            scroller.addEventListener('mousedown', (e) => {
                isDown = true;
                scroller.classList.add('grabbing');
                startX = e.pageX - scroller.offsetLeft;
                scrollLeft = scroller.scrollLeft;
            });

            scroller.addEventListener('mouseleave', () => {
                isDown = false;
                scroller.classList.remove('grabbing');
            });

            scroller.addEventListener('mouseup', () => {
                isDown = false;
                scroller.classList.remove('grabbing');
            });

            scroller.addEventListener('mousemove', (e) => {
                if (!isDown) return;
                e.preventDefault();
                const x = e.pageX - scroller.offsetLeft;
                const walk = (x - startX) * 2; // scroll-fast factor
                scroller.scrollLeft = scrollLeft - walk;
            });

        } catch (error) {
            console.error('Syndicate Navigation Error:', error);
        }
    }

    initializeArticleNav();
});

// --- NEURO-LAUNCHPAD LOGIC ---
if (typeof gsap !== 'undefined') {
    gsap.registerPlugin(Flip, TextPlugin);
}

document.addEventListener('DOMContentLoaded', () => {
    const hero = document.getElementById('hero-launchpad');
    const mainInterface = document.getElementById('main-interface');
    const brainImage = document.getElementById('hero-brain-image'); // hidden, used as flip proxy for header destination
    const brainSvgWrap = document.getElementById('brain-svg-wrap'); // visible SVG container — what we actually animate
    const heroTitle = document.getElementById('hero-main-title');
    const heroInstruction = document.getElementById('hero-instruction');
    const destination = document.getElementById('header-logo-proxy');
    const isLive = localStorage.getItem('syndicate_live') === 'true';

    if (!hero || !mainInterface) return;

    // --- Persistent State Check ---
    if (isLive) {
        hero.style.display = 'none';
        mainInterface.style.display = 'block';
        mainInterface.style.opacity = '1';
        document.body.classList.add('logo-header-state');
        if (destination && brainImage) {
            destination.appendChild(brainImage);
            brainImage.style.display = 'block';
            brainImage.style.cursor = 'pointer';
        }
        return;
    }

    // --- SVG Hotspot Hover + Click Logic ---
    const hotspotGroups = document.querySelectorAll('.hotspot-group');
    hotspotGroups.forEach(group => {
        const section = group.dataset.section;
        const hexString = group.dataset.hex;
        const page = group.dataset.page;
        const labelId = 'label-group-' + section.replace(/\s+/g, '-');
        const labelGroup = document.getElementById(labelId);
        const glowCircle = group.querySelector('.hotspot-glow');
        const nodeDot = group.querySelector('.node-dot');
        if (!labelGroup) return;
        const connLine = labelGroup.querySelector('.conn-line');
        const hexText = labelGroup.querySelector('.hex-text');
        const decodedText = labelGroup.querySelector('.decoded-text');
        let hoverTl = null;
        let scrambleInterval = null;
        let glitchInterval = null;

        group.addEventListener('mouseenter', () => {
            if (hoverTl) hoverTl.kill();
            if (scrambleInterval) clearInterval(scrambleInterval);
            if (glitchInterval) clearInterval(glitchInterval);

            hoverTl = gsap.timeline();
            hoverTl.to(nodeDot, { opacity: 1, duration: 0.12 });
            hoverTl.to(glowCircle, { opacity: 0.5, duration: 0.3, ease: 'power2.out' }, '<0.05');
            hoverTl.to(connLine, { opacity: 0.6, duration: 0.25 }, '<0.08');
            hoverTl.to(labelGroup, { opacity: 1, duration: 0.18 }, '<0.08');

            // Glitchy hex scramble
            // SLOW + DRAMATIC hex scramble decode — you should clearly see chars cycling
            const chars = '0123456789ABCDEF!@#$%&*<>{}[]/?\\|';
            let count = 0;
            scrambleInterval = setInterval(() => {
                let s = '';
                for (let i = 0; i < hexString.length; i++) {
                    if (hexString[i] === ' ') s += ' ';
                    // Each char locks in after the scrambler reaches it
                    // Slowed locking rate (i * 4 instead of i * 1.5) = much more visible cycling
                    else if (count > i * 4) s += hexString[i];
                    else s += chars[Math.floor(Math.random() * chars.length)];
                }
                hexText.textContent = s;
                // Stronger opacity flicker — drops to 30% on 25% of frames
                hexText.style.opacity = Math.random() > 0.25 ? '1' : '0.3';
                count++;
                if (count > hexString.length * 5) {
                    clearInterval(scrambleInterval);
                    scrambleInterval = null;
                    hexText.textContent = hexString;
                    hexText.style.opacity = '1';
                    // AGGRESSIVE post-settle re-corruption — fires often, multiple chars at once
                    glitchInterval = setInterval(() => {
                        if (Math.random() > 0.3) {  // 70% chance every cycle (was 40%)
                            let glitched = hexString.split('');
                            // Corrupt 1-3 characters at random
                            const numCorrupt = 1 + Math.floor(Math.random() * 3);
                            for (let n = 0; n < numCorrupt; n++) {
                                let pos = Math.floor(Math.random() * glitched.length);
                                if (glitched[pos] !== ' ') {
                                    glitched[pos] = chars[Math.floor(Math.random() * chars.length)];
                                }
                            }
                            hexText.textContent = glitched.join('');
                            hexText.style.opacity = '0.6';
                            setTimeout(() => {
                                hexText.textContent = hexString;
                                hexText.style.opacity = '1';
                            }, 80 + Math.random() * 120);
                        }
                    }, 200 + Math.random() * 400); // Tighter cycle (was 400-1000ms, now 200-600ms)
                }
            }, 65); // SLOWER scramble interval (was 22ms, now 65ms) — actually visible decoding

            hoverTl.to(decodedText, { opacity: 1, duration: 0.4, ease: 'power2.out' }, '+=1.5');
        });

        group.addEventListener('mouseleave', () => {
            if (hoverTl) hoverTl.kill();
            if (scrambleInterval) { clearInterval(scrambleInterval); scrambleInterval = null; }
            if (glitchInterval) { clearInterval(glitchInterval); glitchInterval = null; }
            hexText.style.opacity = '1';
            gsap.to([nodeDot, glowCircle, connLine, labelGroup], { opacity: 0, duration: 0.2 });
            gsap.to(decodedText, { opacity: 0, duration: 0.1 });
        });

        // Click → run transition then navigate
        group.addEventListener('click', () => {
            const navMap = {
                'Procurement': 'shop.html',
                'Optimization': 'optimization.html',
                'Intel Hub': 'intel.html',
                'About': 'about.html',
                'Privacy': 'privacy.html'
            };
            const targetPage = navMap[section] || page;
            startTransition(targetPage);
        });
    });

    // Mobile fallback nav already navigates via <a> hrefs — but mark as live on click
    document.querySelectorAll('.mobile-nav-item').forEach(link => {
        link.addEventListener('click', () => {
            localStorage.setItem('syndicate_live', 'true');
        });
    });

    function startTransition(navigateTo) {
        // Returning visitor: skip animation, just navigate
        if (localStorage.getItem('syndicate_live') === 'true') {
            if (navigateTo) window.location.href = navigateTo;
            return;
        }
        localStorage.setItem('syndicate_live', 'true');

        // Fast hop with target page
        if (navigateTo) {
            if (typeof gsap !== 'undefined' && brainSvgWrap) {
                const tl = gsap.timeline();
                tl.to(heroTitle, { y: 50, opacity: 0, duration: 0.4, ease: "power2.in" });
                tl.to(heroInstruction, { opacity: 0, duration: 0.3 }, "<");
                tl.to(brainSvgWrap, { scale: 0.5, opacity: 0.8, duration: 0.5, ease: "power2.in" }, "<");
                setTimeout(() => { window.location.href = navigateTo; }, 600);
            } else {
                window.location.href = navigateTo;
            }
            return;
        }

        // Full launchpad → command center transition (no target page, brain stays as header logo)
        if (typeof gsap !== 'undefined' && brainSvgWrap && destination) {
            const tl = gsap.timeline();

            tl.to(heroTitle, { y: 50, opacity: 0, duration: 0.6, ease: "power2.in" });
            tl.to(heroInstruction, { opacity: 0, duration: 0.4 }, "<");

            tl.add(() => {
                // Show the hidden img and Flip it into the header
                brainImage.style.display = 'block';
                const state = Flip.getState(brainImage);
                destination.appendChild(brainImage);
                Flip.from(state, {
                    duration: 1.2,
                    scale: true,
                    ease: "power3.inOut",
                    onComplete: () => {
                        document.body.classList.add('logo-header-state');
                        brainImage.style.cursor = 'pointer';
                    }
                });
                // Fade the SVG container while the img Flips into place
                gsap.to(brainSvgWrap, { opacity: 0, duration: 0.6 });
            });

            tl.to(mainInterface, {
                display: 'block',
                opacity: 1,
                duration: 1,
                ease: "power2.out"
            }, "+=1.2");

            tl.to(hero, {
                opacity: 0,
                duration: 1,
                onComplete: () => {
                    hero.style.display = 'none';
                }
            }, "-=1");
        } else {
            // Fallback if GSAP missing
            hero.style.display = 'none';
            mainInterface.style.display = 'block';
            mainInterface.style.opacity = '1';
            document.body.classList.add('logo-header-state');
            if (destination && brainImage) {
                destination.appendChild(brainImage);
                brainImage.style.display = 'block';
            }
        }
    }
});

/* === DSDA MOBILE NAV DRAWER === */
(function () {
  function init() {
    if (document.getElementById('dsda-nav-toggle')) return;
    var nav = document.querySelector('header nav') || document.querySelector('body > nav');
    if (!nav) return;
    var btn = document.createElement('button');
    btn.id = 'dsda-nav-toggle';
    btn.setAttribute('aria-label', 'Toggle menu');
    btn.innerHTML = '<span></span><span></span><span></span>';
    document.body.appendChild(btn);
    btn.addEventListener('click', function () {
      document.body.classList.toggle('dsda-nav-open');
    });
    nav.addEventListener('click', function (e) {
      if (e.target.tagName === 'A') document.body.classList.remove('dsda-nav-open');
    });
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else { init(); }
})();

