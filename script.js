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
    const firstArticleP = document.querySelector('.article-container p, .intel-burst p');
    if (firstArticleP) {
        firstArticleP.classList.add('decryption-text');
        setTimeout(() => {
            firstArticleP.classList.add('decrypted');
        }, 500);
    }
});

// --- Article Navigation Scroller Logic ---
document.addEventListener('DOMContentLoaded', () => {
    const navPlaceholder = document.getElementById('article-navigation');
    if (!navPlaceholder) return;
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
            let navHTML = '<h2 class="section-title">Syndicate Transmissions</h2><div class="nav-scroller-container"><div class="nav-scroller" id="nav-scroller">';
            archiveItems.forEach((item, index) => {
                const title = item.querySelector('.title').textContent;
                const date = item.querySelector('.date').textContent;
                const href = item.getAttribute('href');
                const isActive = index === currentIndex;
                const isPrev = index === currentIndex + 1;
                const isNext = index === currentIndex - 1;
                let cardClass = 'nav-card';
                if (isActive) cardClass += ' active';
                if (isPrev) cardClass += ' prev-card';
                if (isNext) cardClass += ' next-card';
                navHTML += `<a href="../${href}" class="${cardClass}" data-index="${index}"><div><div class="nav-meta">${date}</div><h4>${title}</h4></div></a>`;
            });
            navHTML += '</div></div>';
            navPlaceholder.innerHTML = navHTML;
            const scroller = document.getElementById('nav-scroller');
            const activeCard = scroller.querySelector('.nav-card.active');
            if (activeCard) {
                setTimeout(() => {
                    const scrollLeft = activeCard.offsetLeft - (scroller.offsetWidth / 2) + (activeCard.offsetWidth / 2);
                    scroller.scrollTo({ left: scrollLeft, behavior: 'smooth' });
                }, 500);
            }
            let isDown = false, startX, scrollLeft;
            scroller.addEventListener('mousedown', (e) => { isDown = true; scroller.classList.add('grabbing'); startX = e.pageX - scroller.offsetLeft; scrollLeft = scroller.scrollLeft; });
            scroller.addEventListener('mouseleave', () => { isDown = false; scroller.classList.remove('grabbing'); });
            scroller.addEventListener('mouseup', () => { isDown = false; scroller.classList.remove('grabbing'); });
            scroller.addEventListener('mousemove', (e) => { if (!isDown) return; e.preventDefault(); const x = e.pageX - scroller.offsetLeft; const walk = (x - startX) * 2; scroller.scrollLeft = scrollLeft - walk; });
        } catch (error) { console.error('Syndicate Navigation Error:', error); }
    }
    initializeArticleNav();
});

// --- NEURO-LAUNCHPAD LOGIC ---
document.addEventListener('DOMContentLoaded', () => {
    const hero = document.getElementById('hero-launchpad');
    if (!hero) return;

    gsap.registerPlugin(Flip, TextPlugin);

    const brainSvg = document.getElementById('brain-hero-svg');
    const hotspots = document.querySelectorAll('.hotspot');
    const labelL = document.getElementById('label-left');
    const labelR = document.getElementById('label-right');
    const connSvg = document.getElementById('hero-connections');
    const mainInterface = document.getElementById('main-interface');

    hotspots.forEach(hotspot => {
        hotspot.addEventListener('mouseenter', (e) => {
            const moduleName = hotspot.getAttribute('data-module');
            const color = hotspot.getAttribute('fill');
            const rect = hotspot.getBoundingClientRect();
            const targetLabel = rect.left < window.innerWidth / 2 ? labelL : labelR;

            targetLabel.style.opacity = 1;
            targetLabel.style.borderColor = color;
            targetLabel.style.color = color;
            targetLabel.style.top = (rect.top + rect.height/2) + 'px';
            targetLabel.style.left = (rect.left < window.innerWidth / 2) ? (rect.left - 300) + 'px' : (rect.right + 100) + 'px';

            // Text Scramble Fallback
            targetLabel.innerText = moduleName;

            // Path Draw
            const lRect = targetLabel.getBoundingClientRect();
            const startX = (rect.left < window.innerWidth / 2) ? lRect.right : lRect.left;
            const startY = lRect.top + lRect.height / 2;
            const endX = rect.left + rect.width / 2;
            const endY = rect.top + rect.height / 2;

            connSvg.innerHTML = `<path class="connection-line" d="M${startX},${startY} L${endX},${endY}" style="stroke:${color};" />`;
            gsap.fromTo(".connection-line", { strokeDashoffset: 1000 }, { strokeDashoffset: 0, duration: 0.5 });
            gsap.to(brainSvg, { filter: `drop-shadow(0 0 30px ${color})`, duration: 0.3 });
        });

        hotspot.addEventListener('mouseleave', () => {
            labelL.style.opacity = 0; labelR.style.opacity = 0;
            connSvg.innerHTML = '';
            gsap.to(brainSvg, { filter: 'drop-shadow(0 0 20px rgba(56, 189, 248, 0.2))', duration: 0.3 });
        });

        hotspot.addEventListener('click', () => {
            brainSvg.style.animation = 'none';
            const state = Flip.getState(brainSvg);
            document.getElementById('header-logo-proxy').appendChild(brainSvg);
            mainInterface.style.display = 'block';

            Flip.from(state, {
                duration: 1.5,
                ease: "power2.inOut",
                scale: true,
                onComplete: () => {
                    hero.style.display = 'none';
                    gsap.to(brainSvg, { filter: 'grayscale(1) contrast(1.2) opacity(0.8)', duration: 1 });
                }
            });
            gsap.to(mainInterface, { opacity: 1, duration: 1, delay: 0.5 });
            gsap.to(hero, { opacity: 0, duration: 1, delay: 0.5 });
        });
    });
});
