// --- Shared Functionality ---

document.addEventListener('DOMContentLoaded', () => {
    // 1. Page Fade-In Effect
    document.body.classList.add('page-fade');

    // 2. Custom Neon Glow Cursor
    const cursorDot = document.createElement('div');
    const cursorOutline = document.createElement('div');
    cursorDot.className = 'cursor-dot';
    cursorOutline.className = 'cursor-outline';
    document.body.appendChild(cursorDot);
    document.body.appendChild(cursorOutline);

    window.addEventListener('mousemove', (e) => {
        const posX = e.clientX;
        const posY = e.clientY;

        cursorDot.style.left = `${posX}px`;
        cursorDot.style.top = `${posY}px`;

        // Smooth outline trailing
        cursorOutline.animate({
            left: `${posX}px`,
            top: `${posY}px`
        }, { duration: 500, fill: "forwards" });
    });

    // 3. Scroll Reveal Logic
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('revealed');
            }
        });
    }, observerOptions);

    document.querySelectorAll('[data-reveal]').forEach(el => observer.observe(el));

    // 4. Reading Progress Bar (for intel.html)
    const progressBar = document.getElementById('reading-progress');
    if (progressBar) {
        window.addEventListener('scroll', () => {
            const winScroll = document.body.scrollTop || document.documentElement.scrollTop;
            const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
            const scrolled = (winScroll / height) * 100;
            progressBar.style.width = scrolled + "%";
        });
    }

    // 5. Hero Particle Background (for index.html)
    const canvas = document.getElementById('particle-canvas');
    if (canvas) {
        initParticles(canvas);
    }

    // 6. Dynamic Quote Rotator (for index.html)
    const quoteContainer = document.getElementById('quote-container');
    if (quoteContainer) {
        initQuoteRotator(quoteContainer);
    }

    // 7. Category Filtering (for shop.html)
    const filterBtns = document.querySelectorAll('.filter-btn');
    if (filterBtns.length > 0) {
        initFilters(filterBtns);
    }
});

// Particle System
function initParticles(canvas) {
    const ctx = canvas.getContext('2d');
    let particles = [];
    const particleCount = 60;

    function resize() {
        canvas.width = canvas.offsetWidth;
        canvas.height = canvas.offsetHeight;
    }

    window.addEventListener('resize', resize);
    resize();

    class Particle {
        constructor() {
            this.reset();
        }
        reset() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.vx = (Math.random() - 0.5) * 0.5;
            this.vy = (Math.random() - 0.5) * 0.5;
            this.size = Math.random() * 2;
            this.alpha = Math.random() * 0.5 + 0.2;
        }
        update() {
            this.x += this.vx;
            this.y += this.vy;
            if (this.x < 0 || this.x > canvas.width || this.y < 0 || this.y > canvas.height) {
                this.reset();
            }
        }
        draw() {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(56, 189, 248, ${this.alpha})`;
            ctx.fill();
        }
    }

    for (let i = 0; i < particleCount; i++) {
        particles.push(new Particle());
    }

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        particles.forEach(p => {
            p.update();
            p.draw();
        });
        requestAnimationFrame(animate);
    }
    animate();
}

// Quote Rotator
function initQuoteRotator(container) {
    const quotes = [
        "\"We aren't just dreaming of a better life; we’re building the infrastructure to make it inevitable.\"",
        "\"Cognitive sovereignty is the ultimate frontier of human freedom.\"",
        "\"The biological hardware must be upgraded to support the digital ambition.\"",
        "\"Focus is a currency. Spend it where it yields the highest return.\"",
        "\"The best way to predict the future is to architect it.\""
    ];
    let current = 0;
    const textEl = container.querySelector('.quote-text');

    setInterval(() => {
        textEl.classList.add('fade-out');
        setTimeout(() => {
            current = (current + 1) % quotes.length;
            textEl.textContent = quotes[current];
            textEl.classList.remove('fade-out');
        }, 500);
    }, 6000);
}

// Category Filters
function initFilters(btns) {
    const cards = document.querySelectorAll('.item-card');
    btns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Update buttons
            btns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const filter = btn.getAttribute('data-filter');

            cards.forEach(card => {
                const category = card.getAttribute('data-category');
                if (filter === 'all' || category === filter) {
                    card.classList.remove('hidden');
                } else {
                    card.classList.add('hidden');
                }
            });
        });
    });
}
