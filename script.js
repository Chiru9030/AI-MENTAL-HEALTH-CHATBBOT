// script.js - Serena frontend logic
pdfjsLib = window.pdfjsLib || {}; // prevent pdf.js errors if present in other project files
document.addEventListener("DOMContentLoaded", () => {
    // Elements
    const chatContainer = document.getElementById("chat-container");
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");
    const micBtn = document.getElementById("mic-btn");
    const typingIndicator = document.getElementById("typing-indicator");
    const emotionIndicator = document.getElementById("emotion-indicator");
    const bgOverlay = document.getElementById("bg-overlay");
    const quotesDataEl = document.getElementById("quotes-data");
    const memoryList = document.getElementById("memory-list");
    const crisisWarning = document.getElementById("crisis-warning");

    // Feature buttons
    const breathBtn = document.getElementById("breath-btn");
    const journalBtn = document.getElementById("journal-btn");
    const sleepBtn = document.getElementById("sleep-btn");
    const checkinBtn = document.getElementById("checkin-btn");
    const voiceToggle = document.getElementById("voice-toggle");
    const memClear = document.getElementById("mem-clear");

    // State
    let voiceEnabled = true;
    let recognition = null;
    let isListening = false;
    let serverSupportsTTS = true; // will be checked on first TTS call
    let memory = [];

    // Load quotes and show one
    try {
        const quotes = JSON.parse(quotesDataEl.textContent || "[]");
        if (Array.isArray(quotes) && quotes.length) {
            const q = quotes[Math.floor(Math.random() * quotes.length)];
            document.getElementById("daily-quote").textContent = `"${q.text}"`;
            document.getElementById("quote-author").textContent = q.author ? `— ${q.author}` : "";
        }
    } catch (e) {
        // ignore
    }

    // Helpers: append messages
    function appendMessage(text, isUser = false) {
        const wrapper = document.createElement("div");
        wrapper.className = `message ${isUser ? "user-message" : "bot-message"}`;

        const bubble = document.createElement("div");
        bubble.className = "bubble";
        bubble.textContent = text;

        wrapper.appendChild(bubble);
        chatContainer.appendChild(wrapper);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // Slow reveal text (also used when TTS plays)
    async function revealText(targetText, containerBubble) {
        containerBubble.textContent = "";
        for (let i = 0; i < targetText.length; i++) {
            containerBubble.textContent += targetText[i];
            if (i % 6 === 0) await new Promise(r => setTimeout(r, 18)); // speed control
        }
    }

    // Typing indicator
    function showTyping() {
        typingIndicator.hidden = false;
    }
    function hideTyping() {
        typingIndicator.hidden = true;
    }

    // Emotion mapping
    const emotionEmoji = {
        sad: "😢",
        anxious: "😟",
        angry: "😠",
        neutral: "😐",
        positive: "😊"
    };
    function setEmotion(e) {
        emotionIndicator.textContent = emotionEmoji[e] || emotionEmoji["neutral"];
    }

    // Play audio blob returned by server
    async function playAudioBlob(blob) {
        const audioUrl = URL.createObjectURL(blob);
        const audio = new Audio(audioUrl);
        audio.play();
        audio.onended = () => URL.revokeObjectURL(audioUrl);
    }

    // TTS: try server endpoint first, fallback to browser speechSynthesis
    async function speakText(text) {
        if (!voiceEnabled) return;
        // Try server TTS
        try {
            const resp = await fetch("/api/tts", {
                method: "POST",
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });
            if (!resp.ok) throw new Error("TTS server error");
            // Check for JSON fallback
            const contentType = resp.headers.get("content-type") || "";
            if (contentType.includes("application/json")) {
                const j = await resp.json();
                if (j && j.fallback) {
                    // fallback to browser
                    speakBrowser(text);
                    return;
                }
            } else {
                // assume audio blob
                const blob = await resp.blob();
                await playAudioBlob(blob);
                return;
            }
        } catch (e) {
            // server TTS failed -> use browser TTS
            speakBrowser(text);
        }
    }

    // Browser speechSynthesis fallback
    function speakBrowser(text) {
        if (!("speechSynthesis" in window)) return;
        const utter = new SpeechSynthesisUtterance(text);
        utter.rate = 1;
        utter.pitch = 1;
        // choose voice optionally
        const voices = speechSynthesis.getVoices();
        if (voices && voices.length) {
            // pick a pleasant voice (fallback)
            utter.voice = voices.find(v => /en-US|en_GB|English/i.test(v.lang)) || voices[0];
        }
        speechSynthesis.cancel();
        speechSynthesis.speak(utter);
    }

    // Send to chat endpoint (existing) and display response gradually + speak
    async function sendToServer(text) {
        try {
            showTyping();
            const resp = await fetch("/api/chat", {
                method: "POST",
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });
            hideTyping();
            if (!resp.ok) {
                appendMessage("Sorry, I couldn't reach Serena. Try again.", false);
                return;
            }
            const data = await resp.json();
            const analysis = data.response || "";
            const emotion = data.emotion || "neutral";
            setEmotion(emotion);

            // store memory locally (basic)
            memory.unshift({ ts: Date.now(), user: text, bot: analysis, emo: emotion });
            if (memory.length > 10) memory.pop();
            renderMemory();

            // show slow reveal and speak
            const wrapper = document.createElement("div");
            wrapper.className = "message bot-message";
            const bubble = document.createElement("div");
            bubble.className = "bubble";
            wrapper.appendChild(bubble);
            chatContainer.appendChild(wrapper);
            chatContainer.scrollTop = chatContainer.scrollHeight;

            // speak in background while revealing
            if (voiceEnabled) speakText(analysis);
            await revealText(analysis, bubble);
            chatContainer.scrollTop = chatContainer.scrollHeight;

            // crisis UI
            if (data.crisis === true) {
                crisisWarning.hidden = false;
                setTimeout(() => crisisWarning.hidden = true, 15000);
            }
        } catch (err) {
            hideTyping();
            appendMessage("We're offline or the server had an error. Serena will still try to support you locally.", false);
            // offline fallback simple reply
            const fallback = "I hear you. Tell me more about what's on your mind.";
            appendMessage(fallback, false);
            speakBrowser(fallback);
        }
    }

    // render memory preview
    function renderMemory() {
        memoryList.innerHTML = "";
        memory.slice(0, 6).forEach(m => {
            const li = document.createElement("li");
            const d = new Date(m.ts);
            li.textContent = `${d.toLocaleDateString()} ${d.toLocaleTimeString()}: ${m.user.slice(0, 28)} → ${m.emo}`;
            memoryList.appendChild(li);
        });
    }

    // Background transitions
    const themes = [
        "linear-gradient(135deg,#667eea 0%,#764ba2 100%)",
        "linear-gradient(135deg,#a18cd1 0%,#fbc2eb 100%)",
        "linear-gradient(135deg,#89f7fe 0%,#66a6ff 100%)",
        "linear-gradient(135deg,#fdfbfb 0%,#ebedee 100%)"
    ];
    let themeIndex = 0;
    function cycleBackground() {
        bgOverlay.style.background = themes[themeIndex % themes.length];
        bgOverlay.style.opacity = 0.12 + (themeIndex % 2) * 0.04;
        themeIndex++;
    }
    setInterval(cycleBackground, 8000); // slow transition

    // Speech recognition (Web Speech API)
    function initSpeechRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            micBtn.disabled = true;
            return;
        }
        recognition = new SpeechRecognition();
        recognition.lang = "en-US";
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;

        recognition.onstart = () => {
            isListening = true;
            micBtn.classList.add("listening");
        };
        recognition.onend = () => {
            isListening = false;
            micBtn.classList.remove("listening");
        };
        recognition.onresult = (evt) => {
            const text = evt.results[0][0].transcript;
            userInput.value = text;
            sendUserMessage();
        };
        recognition.onerror = (e) => {
            isListening = false;
            micBtn.classList.remove("listening");
            console.warn("STT error", e);
        };
    }
    initSpeechRecognition();

    // Send message flows
    async function sendUserMessage() {
        const text = userInput.value.trim();
        if (!text) return;
        appendMessage(text, true);
        userInput.value = "";
        await sendToServer(text);
    }

    // UI bindings
    sendBtn.addEventListener("click", sendUserMessage);
    userInput.addEventListener("keypress", (e) => { if (e.key === "Enter") sendUserMessage(); });

    // Mic button: press to talk (on mobile tap toggles)
    let micPressTimer = null;
    micBtn.addEventListener("mousedown", () => {
        if (!recognition) return;
        try { recognition.start(); } catch (e) { }
    });
    micBtn.addEventListener("mouseup", () => {
        if (!recognition) return;
        try { recognition.stop(); } catch (e) { }
    });
    // mobile: toggle on click
    micBtn.addEventListener("click", () => {
        if (!recognition) return;
        if (isListening) { recognition.stop(); } else { recognition.start(); }
    });

    // Voice toggle
    voiceToggle.addEventListener("click", () => {
        voiceEnabled = !voiceEnabled;
        voiceToggle.classList.toggle("off", !voiceEnabled);
        voiceToggle.title = voiceEnabled ? "Voice ON" : "Voice OFF";
    });

    // Memory clear
    memClear.addEventListener("click", () => {
        if (!confirm("Clear local memory?")) return;
        memory = [];
        renderMemory();
        fetch('/api/clear_memory', { method: 'POST' }).catch(() => { });
    });

    // Feature buttons (simple guided behaviors)
    breathBtn.addEventListener("click", () => {
        // Simple breathing modal-like experience
        const steps = ["Breathe in 4", "Hold 7", "Exhale 8"];
        appendMessage("Let's do a short 4-7-8 breath with me.", false);
        speakBrowser("Let's do a short breathing exercise together.");
        (async () => {
            for (let i = 0; i < 3; i++) {
                appendMessage(steps[0], false);
                await new Promise(r => setTimeout(r, 4000));
                appendMessage(steps[1], false);
                await new Promise(r => setTimeout(r, 7000));
                appendMessage(steps[2], false);
                await new Promise(r => setTimeout(r, 8000));
            }
        })();
    });

    journalBtn.addEventListener("click", () => {
        const prompt = "Let's write a short journal entry. What's on your mind today?";
        appendMessage(prompt, false);
        speakBrowser(prompt);
    });

    sleepBtn.addEventListener("click", () => {
        const sleepText = "Relax. Close your eyes. Imagine a soft warm place. I will tell you a calming story.";
        appendMessage(sleepText, false);
        speakText(sleepText);
    });

    checkinBtn.addEventListener("click", () => {
        const c = "Hi — how are you feeling right now, on a scale of 1 to 10?";
        appendMessage(c, false);
        speakBrowser(c);
    });

    // On load: fetch small state / memory from server
    (async () => {
        try {
            const r = await fetch('/api/history');
            if (r.ok) {
                const d = await r.json();
                // d.history is array of interactions, show last few
                if (d.history && d.history.length) {
                    memory = d.history.slice(-6).reverse().map(h => ({ ts: Date.now(), user: h.user_msg || "", bot: h.bot_msg || "", emo: "neutral" }));
                    renderMemory();
                }
            }
        } catch (e) { }
    })();

}); // DOMContentLoaded
