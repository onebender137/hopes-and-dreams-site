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
    // Robustly target the first paragraph of an article container
    const firstArticleP = document.querySelector('.article-container p, .intel-burst p');
    if (firstArticleP) {
        firstArticleP.classList.add('decryption-text');
        // Staggered reveal
        setTimeout(() => {
            firstArticleP.classList.add('decrypted');
        }, 500);
    }

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
                components = ["alpha-gpc", "citicoline", "l-theanine", "bacopa"];
                dosage = "Alpha GPC: 300mg, Citicoline: 250mg, L-Theanine: 200mg, Bacopa: 300mg.";
                details = "Designed for sustained neural plasticity and linguistic fluidity. The cholinergic foundation paired with L-Theanine ensures sharp focus, while Bacopa supports long-term memory consolidation.";
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
                components = ["agmatine", "alpha-gpc", "nalt", "creatine"];
                dosage = "Agmatine: 500mg, Alpha GPC: 150mg, N-Acetyl L-Tyrosine: 350mg, Creatine: 5g.";
                details = "Focused on dopamine synthesis and cellular energy. NALT provides the precursor for drive, while Creatine ensures ATP availability for high-output neural sessions.";
            } else if (goal === 'dream') {
                stackName = "The Oneironaut Stack";
                components = ["huperzine", "alpha-gpc", "citicoline", "uridine"];
                dosage = "Huperzine-A: 200mcg, Alpha GPC: 300mg, Citicoline: 250mg, Uridine: 250mg.";
                details = "Maximizes acetylcholine concentration during the REM-dominant hours. Uridine supports the synaptic plasticity required for vivid dream recall.";
            } else if (goal === 'resilience') {
                stackName = "The Zen Master";
                components = ["ashwagandha", "rhodiola", "l-theanine", "magnesium"];
                dosage = "Ashwagandha (KSM-66): 600mg, Rhodiola: 300mg, L-Theanine: 200mg, Magnesium: 200mg.";
                details = "The ultimate shield against burnout. Rhodiola provides acute anti-fatigue effects, while Ashwagandha and Magnesium manage systemic stress loads.";
            } else if (goal === 'maintenance') {
                stackName = "The Neuro-Vanguard";
                components = ["lions-mane", "omega-3", "citicoline", "uridine", "creatine"];
                dosage = "Lion's Mane: 1000mg, Omega-3: 2000mg, Citicoline: 250mg, Uridine: 250mg, Creatine: 3g.";
                details = "The ultimate foundation for long-term brain health. This stack focuses on neuro-genesis (Lion's Mane), membrane integrity (Omega-3/Citicoline/Uridine), and metabolic support (Creatine).";
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
            <div class="agent-selector">
                <span class="agent-chip active" data-agent="Ghost">Ghost</span>
                <span class="agent-chip" data-agent="Pulse">Pulse</span>
                <span class="agent-chip" data-agent="Spark">Spark</span>
            </div>
            <div class="chat-messages" id="chat-messages">
                <div class="message bot">System initialized. Agent Ghost online. How can the Syndicate assist your optimization today?</div>
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

// Syndicate Matrix Gutter Logic (Lightweight)
document.addEventListener('DOMContentLoaded', () => {
    if (window.innerWidth <= 1024) return; // Abort on mobile

    const createGutter = (side) => {
        const gutter = document.createElement('div');
        gutter.className = `data-gutter ${side}`;
        document.body.appendChild(gutter);
        return gutter;
    };

    const leftGutter = createGutter('left');
    const rightGutter = createGutter('right');

    // Matrix character set (Katakana + Latin + Numerals)
    const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%^&*";

    // Moderate interval for ~50% density
    setInterval(() => {
        const text = chars.charAt(Math.floor(Math.random() * chars.length)) +
                     chars.charAt(Math.floor(Math.random() * chars.length)) +
                     chars.charAt(Math.floor(Math.random() * chars.length));

        const el = document.createElement('div');
        el.innerText = text;
        el.style.opacity = Math.random() * 0.4 + 0.05;
        el.style.marginBottom = "6px";

        const target = Math.random() > 0.5 ? leftGutter : rightGutter;
        target.prepend(el);

        // Keep DOM clean
        if (target.children.length > 35) {
            target.removeChild(target.lastChild);
        }
    }, 600);
});

// --- Article Navigation Scroller Logic ---
document.addEventListener('DOMContentLoaded', () => {
    const navPlaceholder = document.getElementById('article-navigation');
    if (!navPlaceholder) return;

    // Determine if we are in an article page
    const isArticle = window.location.pathname.includes('/articles/');
    if (!isArticle) return;

    const transmissionsUrl = '../transmissions.html';

    async function initializeArticleNav() {
        try {
            const response = await fetch(transmissionsUrl);
            const html = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const archiveItems = Array.from(doc.querySelectorAll('.archive-item'));

            if (archiveItems.length === 0) return;

            const currentPath = window.location.pathname.split('/').pop();
            let currentIndex = archiveItems.findIndex(item => item.getAttribute('href').includes(currentPath));

            // Generate the scroller HTML
            let navHTML = `
                <h2 class="section-title">Syndicate Transmissions</h2>
                <div class="nav-scroller-container">
                    <div class="nav-scroller" id="nav-scroller">
            `;

            archiveItems.forEach((item, index) => {
                const title = item.querySelector('.title').textContent;
                const date = item.querySelector('.date').textContent;
                const href = item.getAttribute('href');
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
gsap.registerPlugin(Flip, TextPlugin);

document.addEventListener('DOMContentLoaded', () => {
    const hero = document.getElementById('hero-launchpad');
    const mainInterface = document.getElementById('main-interface');
    const brainImage = document.getElementById('hero-brain-image');
    const heroTitle = document.getElementById('hero-main-title');
    const destination = document.getElementById('header-logo-proxy');
    const connLine = document.getElementById('hero-connection-line');
    const hotspots = document.querySelectorAll('.hotspot');
    const labels = document.querySelectorAll('.hero-section-label');
    const isLive = localStorage.getItem('syndicate_live') === 'true';

    if (!hero || !mainInterface || !brainImage) return;

    // --- Throb Animation ---
    // Disabled - replaced by stronger CSS hormetic-throb keyframes in style.css
    // (See #hero-brain-image rule for box-shadow pulse + scale)

    // --- Persistent State Check ---
    if (isLive) {
        hero.style.display = 'none';
        mainInterface.style.display = 'block';
        mainInterface.style.opacity = '1';
        document.body.classList.add('logo-header-state');
        if (destination) {
            destination.appendChild(brainImage);
            brainImage.style.cursor = 'pointer';
            brainImage.onclick = () => {
                localStorage.removeItem('syndicate_live');
                window.location.href = 'index.html';
            };
        }
        return;
    }

    // --- Hover Logic ---
    hotspots.forEach(hotspot => {
        const section = hotspot.dataset.section;
        const labelId = `label-${section.replace(/\s+/g, '-')}`;
        const label = document.getElementById(labelId);

        hotspot.addEventListener('mouseenter', () => {
            if (label) {
                gsap.to(label, { opacity: 1, duration: 0.3 });

                // Draw line
                const hRect = hotspot.getBoundingClientRect();
                const lRect = label.getBoundingClientRect();

                const x1 = hRect.left + hRect.width / 2;
                const y1 = hRect.top + hRect.height / 2;
                const x2 = lRect.left + lRect.width / 2;
                const y2 = lRect.top + lRect.height / 2;

                connLine.setAttribute('x1', x1);
                connLine.setAttribute('y1', y1);
                connLine.setAttribute('x2', x2);
                connLine.setAttribute('y2', y2);
                gsap.to(connLine, { opacity: 0.8, duration: 0.2 });
            }
        });

        hotspot.addEventListener('mouseleave', () => {
            if (label) {
                gsap.to(label, { opacity: 0, duration: 0.3 });
                gsap.to(connLine, { opacity: 0, duration: 0.2 });
            }
        });

        // --- Transition Logic (Step A, B, C) ---
        hotspot.addEventListener('click', () => startTransition());
    });

    // Make image also trigger transition
    brainImage.addEventListener('click', () => startTransition());

    function startTransition() {
        if (localStorage.getItem('syndicate_live') === 'true') return;
        localStorage.setItem('syndicate_live', 'true');

        const tl = gsap.timeline();

        // Step A: Title fade and slide down
        tl.to(heroTitle, {
            y: 50,
            opacity: 0,
            duration: 0.6,
            ease: "power2.in"
        });

        // Step B: Brain Flip to Header
        tl.add(() => {
            const state = Flip.getState(brainImage);
            destination.appendChild(brainImage);

            const flipTween = Flip.from(state, {
                duration: 1.2,
                scale: true,
                ease: "power3.inOut",
                onComplete: () => {
                    document.body.classList.add('logo-header-state');
                    brainImage.style.cursor = 'pointer';
                    brainImage.onclick = () => {
                        localStorage.removeItem('syndicate_live');
                        window.location.href = 'index.html';
                    };
                }
            });
            // We can't easily return a tween inside a timeline callback to make it blocking
            // so we'll use a delayed call for Step C or similar, but better is to just add it.
        });

        // Step C: Fade in architecture (Wait for Step B to finish roughly)
        tl.to(mainInterface, {
            display: 'block',
            opacity: 1,
            duration: 1,
            ease: "power2.out"
        }, "+=1.2"); // Positive offset to ensure Step B (duration 1.2) finishes

        tl.to(hero, {
            opacity: 0,
            duration: 1,
            onComplete: () => {
                hero.style.display = 'none';
            }
        }, "-=1");
    }
});
