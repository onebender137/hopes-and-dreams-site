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
            }
        });
    }, observerOptions);

    document.querySelectorAll('[data-reveal]').forEach(el => observer.observe(el));

    // Theme Toggle
    const themeToggle = document.getElementById('theme-toggle');
    const body = document.body;
    const logo = document.querySelector('.logo-wrap img');

    // Check for saved theme
    const currentTheme = localStorage.getItem('theme');
    if (currentTheme === 'light') {
        body.classList.add('light-mode');
        if (themeToggle) themeToggle.innerHTML = '🌙 DARK MODE';
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
                themeToggle.innerHTML = '🌙 DARK MODE';
                if (logo) {
                    const isArticle = window.location.pathname.includes('/articles/');
                    logo.src = isArticle ? '../topper-inverted.png' : 'topper-inverted.png';
                }
            } else {
                themeToggle.innerHTML = '☀️ LIGHT MODE';
                if (logo) {
                    const isArticle = window.location.pathname.includes('/articles/');
                    logo.src = isArticle ? '../topper.png' : 'topper.png';
                }
            }
            localStorage.setItem('theme', theme);
        });
    }
});
