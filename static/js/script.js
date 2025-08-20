const chatMessages = document.getElementById("chat-messages");
const chatInput = document.getElementById("chat-input");
const chatButton = document.getElementById("chat-button");

async function sendMessage() {
    const userMessage = chatInput.value;
    if (!userMessage) return;

    // Display user message
    const userDiv = document.createElement("div");
    userDiv.className = "message user";
    userDiv.textContent = userMessage;
    chatMessages.appendChild(userDiv);
    chatInput.value = "";

    // Send the query to the backend
    const response = await fetch("/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: userMessage }),
    });

    const data = await response.json();

    // Display assistant response
    const assistantDiv = document.createElement("div");
    assistantDiv.className = "message assistant";
    assistantDiv.textContent = data.response_message;
    chatMessages.appendChild(assistantDiv);

    chatMessages.scrollTop = chatMessages.scrollHeight;
}

chatButton.addEventListener("click", sendMessage);
chatInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendMessage();
});
