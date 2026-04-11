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
2. Find the `codexData` object (near the top).
3. Add a new key-value pair inside the curly braces `{ }`. 
   - The **key** (the word you search for) must be lowercase and inside quotes.
   - The **value** (the definition) must be inside quotes and followed by a comma.

**Example Code:**
```javascript
const codexData = {
    'ache': 'Acetylcholinesterase explanation...',
    'newterm': 'Your definition here...', // <--- Add like this!
};
```

### Current Terms in Database:
- **ache**: Acetylcholinesterase enzyme info.
- **bdnf**: Brain-Derived Neurotrophic Factor.
- **choline**: Acetylcholine precursor.
- **gaba**: Inhibitory neurotransmitter for relaxation.
- **glycine**: Amino acid for sleep quality.
- **hrv**: Heart Rate Variability.
- **l-theanine**: Relaxation without drowsiness.
- **nootropic**: Cognitive enhancers.
- **rem**: Rapid Eye Movement sleep stage.
- **yuschak**: Lucid dreaming protocol.

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

## 3. DEEP WORK SOUNDSCAPES (Neural Frequency Architect)
An advanced audio generation system for brainwave entrainment, labeled "DEEP WORK SOUNDSCAPES" on the Intel Hub for clarity.

### How it works:
- **Brown Noise Layer:** Generates deep, low-frequency random noise via a buffer algorithm to mask external distractions.
- **Dynamic Binaural Beats:** Uses two independent oscillators (L/R) to create a perceived third tone.
- **Brainwave Presets:** Users can select from five optimized frequencies (Delta, Theta, Alpha, Beta, Gamma) via a preset grid.
- **Real-time State Mapping:** Selecting a preset updates the `currentFreq` and triggers the `setBrainwave` function, which provides dynamic feedback on the optimization target.

### Maintenance:
- The base frequency (default 200Hz) can be adjusted in `script.js` by changing the `baseFreq` variable.
- Brainwave state descriptions and specific frequency targets can be updated within the `setBrainwave` function in `script.js`.

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
