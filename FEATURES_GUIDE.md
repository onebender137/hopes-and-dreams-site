# Hopes and Dreams: Interactive Features Guide

Welcome to the technical guide for the new interactive features on Hopes and Dreams. This document explains how the features work and how you can update them.

---

## Architecture Note
All interactive logic is consolidated in `script.js` for better maintainability and performance. Local styling is handled in `style.css` under the `/* --- WIDGETS & INTERACTIVE FEATURES --- */` section.

---

## 1. Biohacking Codex (Glossary)
The Codex is a searchable technical glossary located in the Intel Hub.

### How it works:
- It uses a lookup table called `codexData` in `script.js`.
- When a user types in the search bar, the script looks for a matching key and displays the definition.

### How to add new articles/terms:
1. Open `script.js`.
2. Find the `codexData` object.
3. Add a new key-value pair. The key should be **lowercase**.

---

## 2. Neuro-Stack Builder (Quiz)
A multi-step recommender system on the Procurement page.

### How it works:
- It tracks user selections for Goal, Experience, and Intake Method.
- The `showQuizResults` function in `script.js` processes these answers to build a personalized recommendation.

### How to update results:
- Modify the `quizQuestions` array to change the questions or options.
- Update the `showQuizResults` logic in `script.js` to change how recommendations are formulated.

---

## 3. Deep Work Soundscapes
Generates audio locally using the Web Audio API.

### How it works:
- **Brown Noise:** Generates deep, low-frequency random noise via a buffer algorithm.
- **Binaural Beats (40Hz):** Creates a "Gamma" frequency by playing 200Hz in the left ear and 240Hz in the right ear for true stereo separation.
- Controlled via `toggleSound(type)` in `script.js`.

---

## 4. Protocol Timer
A countdown timer for biohacking routines (Cold Plunges, Meditation).

### How it works:
- Managed by `startTimer(seconds)` in `script.js`.
- Updates the DOM every second and provides a "PROTOCOL COMPLETE" notification.

---

## 5. Reading Time Estimator
Displays the "Intel Depth" at the top of articles.

### How it works:
- Scans the `<article>` tag and calculates reading time based on a 225 WPM average.
- Automatically initializes for any page containing an `<article>` tag.

---

## 6. Biometric Visualizer
A visual representation of HRV (Heart Rate Variability).

### How it works:
- Uses a CSS-based bar chart with a staggered entrance animation.
- Triggered by the `IntersectionObserver` in `script.js` when the chart scrolls into view.

---

## General Maintenance
- **Styles:** All feature styling is in `style.css`.
- **Logic:** All interactive logic is in `script.js`.
- **Theme:** All features are fully compatible with the Dark/Light mode toggle.

Happy Biohacking! 🧠✨
