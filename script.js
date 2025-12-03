document.addEventListener("DOMContentLoaded", () => {
    const chatContainer = document.getElementById("chat-container");
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");

    userInput.focus();

    function appendMessage(text, isUser, emotion = null) {
        const msgDiv = document.createElement("div");
        msgDiv.className = `message ${isUser ? "user-message" : "bot-message"}`;

        const bubble = document.createElement("div");
        bubble.className = "bubble";

        bubble.textContent = text;

        // Add emotion tag for bot messages
        if (!isUser && emotion && emotion !== "neutral") {
            const tag = document.createElement("span");
            tag.className = "emotion-tag";
            tag.textContent = emotion;
            bubble.appendChild(tag);
        }

        msgDiv.appendChild(bubble);
        chatContainer.appendChild(msgDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    async function sendMessage() {
        const text = userInput.value.trim();
        if (!text) return;

        appendMessage(text, true);
        userInput.value = "";

        try {
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: text })
            });

            const data = await response.json();

            if (data.crisis === true) {
                appendMessage("⚠ Crisis detected:\n" + data.response, false);
                return;
            }

            appendMessage(data.response, false, data.emotion);
        } catch (err) {
            appendMessage(
                "I'm having trouble connecting right now. Can we try again?",
                false
            );
        }
    }

    sendBtn.addEventListener("click", sendMessage);
    userInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") sendMessage();
    });
});
