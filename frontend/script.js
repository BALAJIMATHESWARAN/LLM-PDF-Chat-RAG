async function uploadFiles() {
    const files = document.getElementById("fileInput").files;
    if (files.length === 0) {
        alert("Select files first");
        return;
    }

    const formData = new FormData();
    const fileList = document.getElementById("fileList");
    fileList.innerHTML = "";

    for (let i = 0; i < files.length; i++) {
        formData.append("files", files[i]);

        // Show file name in sidebar
        const div = document.createElement("div");
        div.className = "file-item";
        div.innerText = files[i].name;
        fileList.appendChild(div);
    }

    document.getElementById("uploadStatus").innerText =
        "Uploading files...";

    await fetch("http://localhost:5000/upload", {
        method: "POST",
        body: formData
    });

    document.getElementById("uploadStatus").innerText =
        "Files uploaded successfully ✅";
}


function formatText(text) {
    return text.replace(/\n/g, "<br>");
}

async function askQuestion() {
    const input = document.getElementById("question");
    const q = input.value.trim();

    if (!q) return;

    const chat = document.getElementById("chatBox");

    // Show user message
    chat.innerHTML += `
        <div class="message">
            <span class="user">You:</span><br>${q}
        </div>
    `;

    // ✅ CLEAR INPUT AFTER SENDING
    input.value = "";

    // Show loading
    const loading = document.createElement("div");
    loading.className = "message bot";
    loading.innerText = "AI is thinking...";
    chat.appendChild(loading);

    const res = await fetch("http://localhost:5000/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q })
    });

    const data = await res.json();

    // Remove loading text
    loading.remove();

    // Show AI response
    chat.innerHTML += `
        <div class="message bot">
            <b>AI:</b><br>${data.answer.replace(/\n/g, "<br>")}
        </div>
    `;

    chat.scrollTop = chat.scrollHeight;
}

document.getElementById("question").addEventListener("keydown", function (e) {
    if (e.key === "Enter") {
        askQuestion();
    }
});
