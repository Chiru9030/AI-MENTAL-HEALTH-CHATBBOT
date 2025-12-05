// static/js/script.js
document.addEventListener("DOMContentLoaded", () => {
    // Elements
    const chatContainer = document.getElementById("chat-container");
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");
    const micBtn = document.getElementById("mic-btn");
    const typingIndicator = document.getElementById("typing-indicator");
    const emotionIndicator = document.getElementById("emotion-indicator");
    const bgOverlay = document.getElementById("bg-overlay");
    const memoryList = document.getElementById("memory-list");
    const quotesDataEl = document.getElementById("quotes-data");
    const breathBtn = document.getElementById("breath-btn");
    const journalBtn = document.getElementById("journal-btn");
    const sleepBtn = document.getElementById("sleep-btn");
    const checkinBtn = document.getElementById("checkin-btn");
    const voiceToggle = document.getElementById("voice-toggle");
    const memClear = document.getElementById("mem-clear");
    const crisisWarning = document.getElementById("crisis-warning");

    // State
    let voiceEnabled = true;
    let recognition = null;
    let isListening = false;
    let memory = [];

    // Show a random daily quote
    try {
        const quotes = JSON.parse(document.getElementById("quotes-data").textContent || "[]");
        if (quotes && quotes.length) {
            const q = quotes[Math.floor(Math.random() * quotes.length)];
            document.getElementById("daily-quote").textContent = `"${q.text}"`;
            document.getElementById("quote-author").textContent = q.author ? `— ${q.author}` : "";
        }
    } catch (e) { }

    // Helpers
    function scrollToBottom() {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    function appendMessage(text, isUser = false) {
        const wrapper = document.createElement("div");
        wrapper.className = `message ${isUser ? "user-message" : "bot-message"}`;
        const bubble = document.createElement("div");
        bubble.className = "bubble";
        bubble.textContent = text;
        wrapper.appendChild(bubble);
        chatContainer.appendChild(wrapper);
        scrollToBottom();
        return bubble;
    }

    async function revealTextSlow(targetText, bubble) {
        bubble.textContent = "";
        for (let i = 0; i < targetText.length; i++) {
            bubble.textContent += targetText[i];
            if (i % 4 === 0) await new Promise(r => setTimeout(r, 18));
        }
        scrollToBottom();
    }

    function showTyping() { typingIndicator.hidden = false; }
    function hideTyping() { typingIndicator.hidden = true; }

    // Emotion mapping
    const emojiMap = { sad: "😢", anxious: "😟", angry: "😠", positive: "😊", neutral: "😐" };
    function setEmotion(e) { emotionIndicator.textContent = emojiMap[e] || emojiMap["neutral"]; }

    // Background themes
    const themes = [
        "linear-gradient(120deg,#89f7fe,#66a6ff)",
        "linear-gradient(120deg,#a18cd1,#fbc2eb)",
        "linear-gradient(120deg,#667eea,#764ba2)",
        "linear-gradient(120deg,#fbc2eb,#a6c1ee)"
    ];
    let t = 0;
    function cycleBg() {
        bgOverlay.style.background = themes[t % themes.length];
        t++;
    }
    setInterval(cycleBg, 9000);

    // TTS: try server-side /api/tts first
    async function speakText(text) {
        if (!voiceEnabled) return;
        try {
            const res = await fetch("/api/tts", {
                method: "POST", headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text })
            });
            if (!res.ok) throw new Error("TTS endpoint failed");
            const json = await res.json();
            if (json.audio) {
                const audio = new Audio("data:audio/mp3;base64," + json.audio);
                await audio.play();
                return;
            }
            // fallback flag -> use browser
            if (json.fallback) {
                speakBrowser(text);
                return;
            }
        } catch (e) {
            // fallback to browser TTS
            speakBrowser(text);
        }
    }

    function speakBrowser(text) {
        if (!("speechSynthesis" in window)) return;
        const ut = new SpeechSynthesisUtterance(text);
        ut.rate = 1.0; ut.pitch = 1.0;
        // pick an English voice if available
        const voices = speechSynthesis.getVoices();
        if (voices && voices.length) {
            ut.voice = voices.find(v => /Google.*English|English.*(US|GB)|en-US|en_GB/i.test(v.lang + " " + v.name)) || voices[0];
        }
        speechSynthesis.cancel();
        speechSynthesis.speak(ut);
    }

    // Send to server, handle response
    async function sendToServer(text) {
        try {
            showTyping();
            const resp = await fetch("/api/chat", {
                method: "POST", headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: text })
            });
            hideTyping();
            if (!resp.ok) {
                appendMessage("Serena is having trouble right now. Try again later.");
                return;
            }
            const data = await resp.json();
            const botText = data.response || "I'm here.";
            const emotion = data.emotion || "neutral";
            setEmotion(emotion);
            // Save local memory preview
            memory.unshift({ ts: Date.now(), user: text, bot: botText, emo: emotion });
            if (memory.length > 12) memory.pop();
            renderMemory();
            // Render response slowly while speaking
            const wrapper = document.createElement("div");
            wrapper.className = "message bot-message";
            const bubble = document.createElement("div");
            bubble.className = "bubble";
            wrapper.appendChild(bubble);
            chatContainer.appendChild(wrapper);
            scrollToBottom();
            // Speak while revealing
            if (voiceEnabled) speakText(botText);
            await revealTextSlow(botText, bubble);
            scrollToBottom();
            // Show crisis warning if needed
            if (data.crisis) {
                crisisWarning.hidden = false;
                setTimeout(() => crisisWarning.hidden = true, 14000);
            }
        } catch (e) {
            hideTyping();
            appendMessage("You seem to be offline. Serena will try to help locally.");
            speakBrowser("You seem to be offline. I will try to support you locally.");
        }
    }

    // Render memory preview
    function renderMemory() {
        memoryList.innerHTML = "";
        memory.slice(0, 6).forEach(m => {
            const li = document.createElement("li");
            const d = new Date(m.ts);
            li.textContent = `${d.toLocaleDateString()} ${d.toLocaleTimeString()}: ${m.user.slice(0, 36)} → ${m.emo}`;
            memoryList.appendChild(li);
        });
    }

    // Fetch history on load
    (async () => {
        try {
            const r = await fetch("/api/history");
            if (r.ok) {
                const j = await r.json();
                if (j.history && j.history.length) {
                    memory = j.history.slice(-6).reverse().map(h => ({ ts: Date.now(), user: h.user_msg || "", bot: h.bot_msg || "", emo: "neutral" }));
                    renderMemory();
                }
            }
        } catch (e) { }
    })();

    // Speech recognition (Web Speech API)
    function initRecognition() {
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SR) { micBtn.disabled = true; return; }
        recognition = new SR();
        recognition.lang = "en-US";
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;
        recognition.onstart = () => { isListening = true; micBtn.classList.add("listening"); }
        recognition.onend = () => { isListening = false; micBtn.classList.remove("listening"); }
        recognition.onerror = (e) => { isListening = false; micBtn.classList.remove("listening"); }
        recognition.onresult = (evt) => {
            const text = evt.results[0][0].transcript;
            userInput.value = text;
            sendUserMessage();
        }
    }
    initRecognition();

    // Send flows
    async function sendUserMessage() {
        const t = userInput.value.trim();
        if (!t) return;
        appendMessage(t, true);
        userInput.value = "";
        await sendToServer(t);
    }

    sendBtn.addEventListener("click", sendUserMessage);
    userInput.addEventListener("keypress", (e) => { if (e.key === "Enter") sendUserMessage() });

    // Mic button: toggle on click
    micBtn.addEventListener("click", () => {
        if (!recognition) return;
        if (isListening) {
            recognition.stop();
        } else {
            recognition.start();
        }
    });

    // Voice toggle
    voiceToggle.addEventListener("click", () => {
        voiceEnabled = !voiceEnabled;
        voiceToggle.style.opacity = voiceEnabled ? 1 : 0.5;
    });

    // Clear memory (local + server)
    memClear.addEventListener("click", async () => {
        if (!confirm("Clear local and server memory?")) return;
        memory = [];
        renderMemory();
        try { await fetch("/api/clear_memory", { method: "POST" }); } catch (e) { }
    });

    // Feature flows
    breathBtn.addEventListener("click", () => {
        appendMessage("Let's do a short 4-7-8 breathing exercise.", false);
        speakBrowser("Let's do a short 4-7-8 breathing exercise together.");
        (async () => {
            const steps = ["Breathe in... 4", "Hold... 7", "Exhale... 8"];
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
        const prompt = "Let's write a short journal entry: what's on your mind?";
        appendMessage(prompt, false);
        speakBrowser(prompt);
    });

    sleepBtn.addEventListener("click", () => {
        const text = "Close your eyes and imagine a warm place. I will guide you for a soft rest.";
        appendMessage(text, false);
        speakText(text);
    });

    checkinBtn.addEventListener("click", () => {
        const text = "Hi — how are you feeling right now on a scale of 1 to 10?";
        appendMessage(text, false);
        speakBrowser(text);
    });

}); // DOMContentLoaded
