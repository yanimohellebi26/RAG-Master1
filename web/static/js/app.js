/* ================================================================= */
/* RAG Master 1 -- Main JavaScript Application                       */
/* ================================================================= */

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

const state = {
    messages: [],
    isStreaming: false,
    lastContext: "",
    lastSources: [],
    lastQuestion: "",
    lastResponse: "",
    chartInstances: [],
};

// ---------------------------------------------------------------------------
// DOM refs
// ---------------------------------------------------------------------------

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const sidebar = $("#sidebar");
const chatArea = $("#chatArea");
const messagesEl = $("#messages");
const welcome = $("#welcome");
const chatInput = $("#chatInput");
const sendBtn = $("#sendBtn");
const copilotBar = $("#copilotBar");
const copilotResults = $("#copilotResults");
const copilotResultsBody = $("#copilotResultsBody");
const nbSourcesSlider = $("#nbSources");
const nbSourcesValue = $("#nbSourcesValue");

// ---------------------------------------------------------------------------
// Marked.js config
// ---------------------------------------------------------------------------

marked.setOptions({
    highlight: (code, lang) => {
        if (lang && hljs.getLanguage(lang)) {
            return hljs.highlight(code, { language: lang }).value;
        }
        return hljs.highlightAuto(code).value;
    },
    breaks: true,
    gfm: true,
});

// ---------------------------------------------------------------------------
// Theme toggle
// ---------------------------------------------------------------------------

function initTheme() {
    const saved = localStorage.getItem("theme") || "dark";
    document.documentElement.setAttribute("data-theme", saved);
}

function toggleTheme() {
    const current = document.documentElement.getAttribute("data-theme");
    const next = current === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
}

initTheme();
$("#toggleTheme").addEventListener("click", toggleTheme);

// ---------------------------------------------------------------------------
// Sidebar toggle
// ---------------------------------------------------------------------------

$("#sidebarOpen").addEventListener("click", () => sidebar.classList.remove("collapsed"));
$("#sidebarClose").addEventListener("click", () => sidebar.classList.add("collapsed"));

// Auto-collapse on mobile
if (window.innerWidth < 768) {
    sidebar.classList.add("collapsed");
}

// ---------------------------------------------------------------------------
// Range slider
// ---------------------------------------------------------------------------

nbSourcesSlider.addEventListener("input", () => {
    nbSourcesValue.textContent = nbSourcesSlider.value;
});

// ---------------------------------------------------------------------------
// Auto-resize textarea
// ---------------------------------------------------------------------------

chatInput.addEventListener("input", () => {
    chatInput.style.height = "auto";
    chatInput.style.height = Math.min(chatInput.scrollHeight, 150) + "px";
});

chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// ---------------------------------------------------------------------------
// Clear chat
// ---------------------------------------------------------------------------

$("#clearChat").addEventListener("click", async () => {
    state.messages = [];
    state.lastContext = "";
    state.lastSources = [];
    state.lastQuestion = "";
    state.lastResponse = "";
    messagesEl.innerHTML = "";
    welcome.style.display = "flex";
    copilotBar.style.display = "none";
    copilotResults.style.display = "none";

    try {
        await fetch("/api/clear", { method: "POST" });
    } catch (e) {
        console.error("Failed to clear server-side history:", e);
    }
});

// ---------------------------------------------------------------------------
// Get settings
// ---------------------------------------------------------------------------

function getSettings() {
    const subjects = [];
    $$(".subject-filter:checked").forEach((cb) => subjects.push(cb.value));

    return {
        subjects,
        nb_sources: parseInt(nbSourcesSlider.value, 10),
        enable_rewrite: $("#enableRewrite").checked,
        enable_hybrid: $("#enableHybrid").checked,
        enable_rerank: $("#enableRerank").checked,
        enable_compress: $("#enableCompress").checked,
    };
}

// ---------------------------------------------------------------------------
// Send suggestion
// ---------------------------------------------------------------------------

function sendSuggestion(el) {
    chatInput.value = el.textContent;
    sendMessage();
}

// ---------------------------------------------------------------------------
// Send message
// ---------------------------------------------------------------------------

async function sendMessage() {
    const question = chatInput.value.trim();
    if (!question || state.isStreaming) return;

    state.isStreaming = true;
    sendBtn.disabled = true;
    state.lastQuestion = question;

    // Hide welcome
    welcome.style.display = "none";

    // Add user message
    addMessage("user", question);
    chatInput.value = "";
    chatInput.style.height = "auto";

    // Add assistant placeholder
    const assistantEl = addMessage("assistant", "", true);
    const bodyEl = assistantEl.querySelector(".assistant-body");
    const sourcesContainer = assistantEl.querySelector(".sources-container");
    const pipelineInfo = assistantEl.querySelector(".pipeline-info");

    // Scroll
    scrollToBottom();

    const settings = getSettings();

    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question, ...settings }),
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let fullResponse = "";
        let sources = [];
        let pipelineData = {};

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop(); // keep incomplete line

            for (const line of lines) {
                if (!line.startsWith("data: ")) continue;
                const jsonStr = line.slice(6);
                if (!jsonStr) continue;

                try {
                    const parsed = JSON.parse(jsonStr);

                    if (parsed.type === "meta") {
                        sources = parsed.sources || [];
                        state.lastSources = sources;
                        state.lastContext = parsed.context || "";
                        pipelineData = parsed;
                        renderSources(sourcesContainer, sources);
                        renderPipeline(pipelineInfo, pipelineData);
                    } else if (parsed.type === "token") {
                        fullResponse += parsed.content;
                        bodyEl.innerHTML = marked.parse(fullResponse);
                        highlightNewCode(bodyEl);
                        scrollToBottom();
                    } else if (parsed.type === "done") {
                        pipelineData.total_time = parsed.total_time;
                        renderPipeline(pipelineInfo, pipelineData);
                    }
                } catch (e) {
                    // skip malformed JSON
                }
            }
        }

        state.lastResponse = fullResponse;

        // Show copilot bar
        copilotBar.style.display = "flex";

    } catch (error) {
        bodyEl.innerHTML = `<p style="color:var(--danger)">Erreur : ${error.message}</p>`;
    } finally {
        state.isStreaming = false;
        sendBtn.disabled = false;
        chatInput.focus();
    }
}

// ---------------------------------------------------------------------------
// Add message to DOM
// ---------------------------------------------------------------------------

function addMessage(role, content, isPlaceholder = false) {
    const el = document.createElement("div");
    el.className = "message";

    const avatarClass = role === "user" ? "user" : "assistant";
    const avatarText = role === "user" ? "Vous" : "AI";
    const name = role === "user" ? "Vous" : "Assistant RAG";

    let bodyContent = "";
    if (role === "user") {
        bodyContent = `<div class="message-body user-body">${escapeHtml(content)}</div>`;
    } else {
        if (isPlaceholder) {
            bodyContent = `
                <div class="message-body assistant-body">
                    <div class="typing-indicator"><span></span><span></span><span></span></div>
                </div>
                <div class="sources-container"></div>
                <div class="pipeline-info"></div>
            `;
        } else {
            bodyContent = `<div class="message-body assistant-body">${marked.parse(content)}</div>`;
        }
    }

    el.innerHTML = `
        <div class="message-header">
            <div class="message-avatar ${avatarClass}">${avatarText}</div>
            <div class="message-name">${name}</div>
        </div>
        ${bodyContent}
    `;

    messagesEl.appendChild(el);

    state.messages.push({ role, content });

    return el;
}

// ---------------------------------------------------------------------------
// Render sources
// ---------------------------------------------------------------------------

function renderSources(container, sources) {
    if (!sources || sources.length === 0) {
        container.innerHTML = "";
        return;
    }

    const toggleId = `sources_${Date.now()}`;
    let html = `
        <button class="sources-toggle" onclick="toggleSources(this, '${toggleId}')">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
            Sources RAG (${sources.length} documents)
        </button>
        <div class="sources-list" id="${toggleId}">
    `;

    for (const src of sources) {
        html += `
            <div class="source-card">
                <span class="source-tag">${escapeHtml(src.matiere)}</span>
                <span class="source-info"><strong>${escapeHtml(src.doc_type)}</strong> — ${escapeHtml(src.filename)}</span>
            </div>
        `;
    }

    html += `</div>`;
    container.innerHTML = html;
}

function toggleSources(btn, listId) {
    const list = document.getElementById(listId);
    btn.classList.toggle("open");
    list.classList.toggle("open");
}

// ---------------------------------------------------------------------------
// Render pipeline info
// ---------------------------------------------------------------------------

function renderPipeline(container, data) {
    if (!data) return;

    let html = `<div class="pipeline-bar">`;
    if (data.retrieval_time != null) {
        html += `<span class="pipeline-metric">Retrieval: <strong>${data.retrieval_time}s</strong></span>`;
    }
    if (data.total_time != null) {
        html += `<span class="pipeline-metric">Total: <strong>${data.total_time}s</strong></span>`;
    }
    if (data.num_docs != null) {
        html += `<span class="pipeline-metric">Documents: <strong>${data.num_docs}</strong></span>`;
    }
    if (data.steps && data.steps.length) {
        html += `<span class="pipeline-steps">${data.steps.join(" → ")}</span>`;
    }
    if (data.rewritten_query && data.rewritten_query !== state.lastQuestion) {
        html += `<br><span class="pipeline-metric" style="margin-top:4px">Requete enrichie: <em>${escapeHtml(data.rewritten_query.substring(0, 120))}</em></span>`;
    }
    html += `</div>`;
    container.innerHTML = html;
}

// ---------------------------------------------------------------------------
// Copilot tools
// ---------------------------------------------------------------------------

async function generateCopilot(toolType) {
    const content = `Question de l'etudiant : ${state.lastQuestion}\n\nReponse du cours :\n${state.lastResponse}`;
    const model = document.getElementById("copilotModel")?.value || "gpt-4o";

    copilotResults.style.display = "flex";
    copilotResultsBody.innerHTML = `
        <div style="text-align:center;padding:40px">
            <div class="spinner"></div>
            <p style="margin-top:12px;color:var(--text-secondary)">Generation en cours...</p>
        </div>
    `;

    try {
        const response = await fetch("/api/copilot", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                tool_type: toolType,
                content: content,
                model: model,
                sources: state.lastSources,
            }),
        });

        const result = await response.json();

        if (result.error) {
            copilotResultsBody.innerHTML = `
                <div style="padding:20px;color:var(--danger)">
                    <p><strong>Erreur :</strong> ${escapeHtml(result.error)}</p>
                    ${result.raw ? `<pre style="margin-top:8px;font-size:0.75rem;overflow:auto;max-height:200px">${escapeHtml(result.raw)}</pre>` : ""}
                </div>
            `;
        } else {
            renderCopilotResult(toolType, result);
        }
    } catch (error) {
        copilotResultsBody.innerHTML = `
            <div style="padding:20px;color:var(--danger)">
                <p><strong>Erreur :</strong> ${escapeHtml(error.message)}</p>
            </div>
        `;
    }
}

function closeCopilotResults() {
    copilotResults.style.display = "none";
}

function renderCopilotResult(toolType, data) {
    const renderers = {
        quiz: renderQuiz,
        table: renderTable,
        chart: renderChart,
        concepts: renderConcepts,
        flashcards: renderFlashcards,
        mindmap: renderMindmap,
    };

    const renderer = renderers[toolType];
    if (renderer) {
        copilotResultsBody.innerHTML = "";
        renderer(data, copilotResultsBody);
    } else {
        copilotResultsBody.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
    }
}

// Quiz
function renderQuiz(data, container) {
    let html = `<h3 class="tool-title">${escapeHtml(data.title || "Quiz")}</h3>`;
    html += `<div class="quiz-container">`;

    for (let i = 0; i < (data.questions || []).length; i++) {
        const q = data.questions[i];
        const qId = `quiz_${Date.now()}_${i}`;
        html += `<div class="quiz-question" id="${qId}">`;
        html += `<h4>Q${i + 1}. ${escapeHtml(q.question)}</h4>`;
        html += `<div class="quiz-options">`;

        for (let j = 0; j < (q.options || []).length; j++) {
            html += `<div class="quiz-option" onclick="checkAnswer('${qId}', ${j}, ${q.correct || 0})">${escapeHtml(q.options[j])}</div>`;
        }

        html += `</div>`;
        html += `<div class="quiz-explanation" id="${qId}_exp">${escapeHtml(q.explanation || "")}</div>`;
        html += `</div>`;
    }

    html += `</div>`;
    container.innerHTML = html;
}

function checkAnswer(qId, selected, correct) {
    const qEl = document.getElementById(qId);
    const options = qEl.querySelectorAll(".quiz-option");
    const explanation = document.getElementById(qId + "_exp");

    options.forEach((opt, idx) => {
        opt.classList.add("disabled");
        if (idx === correct) opt.classList.add("correct");
        if (idx === selected && idx !== correct) opt.classList.add("wrong");
    });

    explanation.classList.add("visible");
}

// Table
function renderTable(data, container) {
    let html = `<h3 class="tool-title">${escapeHtml(data.title || "Tableau")}</h3>`;
    if (data.headers && data.rows) {
        html += `<table class="data-table"><thead><tr>`;
        data.headers.forEach((h) => (html += `<th>${escapeHtml(h)}</th>`));
        html += `</tr></thead><tbody>`;
        data.rows.forEach((row) => {
            html += `<tr>`;
            row.forEach((cell) => (html += `<td>${escapeHtml(String(cell))}</td>`));
            html += `</tr>`;
        });
        html += `</tbody></table>`;
    }
    container.innerHTML = html;
}

// Chart
function renderChart(data, container) {
    // Destroy existing charts
    state.chartInstances.forEach((c) => c.destroy());
    state.chartInstances = [];

    let html = `<h3 class="tool-title">${escapeHtml(data.title || "Graphique")}</h3>`;
    html += `<div class="chart-container"><canvas id="copilotChart"></canvas></div>`;
    container.innerHTML = html;

    const ctx = document.getElementById("copilotChart").getContext("2d");
    const chartType = data.chart_type === "line" ? "line" : data.chart_type === "area" ? "line" : "bar";

    const isDark = document.documentElement.getAttribute("data-theme") === "dark";
    const gridColor = isDark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.08)";
    const textColor = isDark ? "#a0a0b8" : "#5a5a7a";

    const chart = new Chart(ctx, {
        type: chartType,
        data: {
            labels: data.labels || [],
            datasets: [
                {
                    label: data.title || "Valeurs",
                    data: data.values || [],
                    backgroundColor: data.chart_type === "area"
                        ? "rgba(102, 126, 234, 0.2)"
                        : "rgba(102, 126, 234, 0.7)",
                    borderColor: "#667eea",
                    borderWidth: 2,
                    borderRadius: 6,
                    fill: data.chart_type === "area",
                    tension: 0.3,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
            },
            scales: {
                x: { ticks: { color: textColor }, grid: { color: gridColor } },
                y: { ticks: { color: textColor }, grid: { color: gridColor } },
            },
        },
    });

    state.chartInstances.push(chart);
}

// Concepts
function renderConcepts(data, container) {
    let html = `<h3 class="tool-title">${escapeHtml(data.title || "Concepts cles")}</h3>`;
    for (const c of data.concepts || []) {
        const imp = c.importance || "moyenne";
        html += `<div class="concept-card ${imp}">
            <h4>${escapeHtml(c.name)}</h4>
            <p>${escapeHtml(c.definition)}</p>
        </div>`;
    }
    container.innerHTML = html;
}

// Flashcards
function renderFlashcards(data, container) {
    let html = `<h3 class="tool-title">${escapeHtml(data.title || "Flashcards")}</h3>`;
    for (let i = 0; i < (data.cards || []).length; i++) {
        const card = data.cards[i];
        const cardId = `fc_${Date.now()}_${i}`;
        html += `<div class="flashcard" id="${cardId}">
            <div class="flashcard-front" onclick="toggleFlashcard('${cardId}')">
                ${escapeHtml(card.front)}
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>
            </div>
            <div class="flashcard-back">${escapeHtml(card.back)}</div>
        </div>`;
    }
    container.innerHTML = html;
}

function toggleFlashcard(id) {
    document.getElementById(id).classList.toggle("open");
}

// Mindmap
function renderMindmap(data, container) {
    let html = `<h3 class="tool-title">${escapeHtml(data.title || "Mind Map")}</h3>`;
    if (data.central) {
        html += `<div class="mindmap-central">${escapeHtml(data.central)}</div>`;
    }
    for (const branch of data.branches || []) {
        html += `<div class="mindmap-branch"><h4>${escapeHtml(branch.name)}</h4><ul>`;
        for (const child of branch.children || []) {
            html += `<li>${escapeHtml(child)}</li>`;
        }
        html += `</ul></div>`;
    }
    container.innerHTML = html;
}

// ---------------------------------------------------------------------------
// Evaluation
// ---------------------------------------------------------------------------

function openEvalModal() {
    $("#evalModal").style.display = "flex";
}

function closeEvalModal() {
    $("#evalModal").style.display = "none";
}

$("#openEvalModal").addEventListener("click", openEvalModal);

async function runEvaluation() {
    const btn = $("#runEvalBtn");
    btn.disabled = true;

    const progress = $("#evalProgress");
    const progressFill = $("#evalProgressFill");
    const progressText = $("#evalProgressText");
    const resultsEl = $("#evalResults");

    progress.style.display = "block";
    resultsEl.style.display = "none";
    progressFill.style.width = "0%";
    progressText.textContent = "Evaluation en cours... Cela peut prendre quelques minutes.";

    // Simulate progress
    let pct = 0;
    const progressInterval = setInterval(() => {
        pct = Math.min(pct + Math.random() * 8, 90);
        progressFill.style.width = pct + "%";
    }, 2000);

    try {
        const response = await fetch("/api/eval/run", { method: "POST" });
        const data = await response.json();

        clearInterval(progressInterval);
        progressFill.style.width = "100%";
        progressText.textContent = "Evaluation terminee !";

        setTimeout(() => {
            progress.style.display = "none";
            displayEvalResults(data);
        }, 1000);
    } catch (error) {
        clearInterval(progressInterval);
        progressText.textContent = `Erreur : ${error.message}`;
        progressFill.style.width = "0%";
    } finally {
        btn.disabled = false;
    }
}

async function loadLatestEval() {
    const resultsEl = $("#evalResults");

    try {
        const response = await fetch("/api/eval/latest");
        if (!response.ok) {
            resultsEl.innerHTML = `<p style="color:var(--text-secondary)">Aucune evaluation disponible.</p>`;
            resultsEl.style.display = "block";
            return;
        }
        const data = await response.json();
        displayEvalResults(data);
    } catch (error) {
        resultsEl.innerHTML = `<p style="color:var(--danger)">Erreur : ${error.message}</p>`;
        resultsEl.style.display = "block";
    }
}

function displayEvalResults(data) {
    const el = $("#evalResults");
    el.style.display = "block";

    const metrics = [
        { label: "Score global", value: formatPercent(data.overall_score) },
        { label: "Fidelite", value: formatPercent(data.avg_faithfulness) },
        { label: "Pertinence", value: formatPercent(data.avg_relevance) },
        { label: "Completude", value: formatPercent(data.avg_completeness) },
        { label: "Sim. semantique", value: formatPercent(data.avg_semantic_similarity) },
        { label: "Mots-cles", value: formatPercent(data.avg_keyword_coverage) },
        { label: "Match matiere", value: formatPercent(data.avg_subject_match) },
        { label: "Latence moy.", value: `${(data.avg_latency || 0).toFixed(1)}s` },
    ];

    let html = `<div class="eval-metrics">`;
    for (const m of metrics) {
        html += `<div class="eval-metric-card">
            <div class="metric-value">${m.value}</div>
            <div class="metric-label">${m.label}</div>
        </div>`;
    }
    html += `</div>`;

    // Per-question details
    if (data.results && data.results.length) {
        html += `<h3 style="margin:20px 0 12px;font-size:1rem">Detail par question</h3>`;
        for (let i = 0; i < data.results.length; i++) {
            const r = data.results[i];
            const faith = r.answer?.faithfulness_score || 0;
            const relev = r.answer?.relevance_score || 0;
            const compl = r.answer?.completeness_score || 0;
            const avg = (faith + relev + compl) / 3;

            let icon, scoreClass;
            if (avg >= 0.7) { icon = "✅"; scoreClass = "score-good"; }
            else if (avg >= 0.4) { icon = "⚠️"; scoreClass = "score-ok"; }
            else { icon = "❌"; scoreClass = "score-bad"; }

            const detailId = `eval_d_${i}`;
            html += `<div class="eval-detail" id="${detailId}">
                <div class="eval-detail-header" onclick="document.getElementById('${detailId}').classList.toggle('open')">
                    <span>${icon} Q${i + 1}. ${escapeHtml((r.question || "").substring(0, 60))}...</span>
                    <span class="eval-detail-score ${scoreClass}">${formatPercent(avg)}</span>
                </div>
                <div class="eval-detail-body">
                    <div class="eval-metrics" style="margin:0 0 12px">
                        <div class="eval-metric-card"><div class="metric-value">${formatPercent(faith)}</div><div class="metric-label">Fidelite</div></div>
                        <div class="eval-metric-card"><div class="metric-value">${formatPercent(relev)}</div><div class="metric-label">Pertinence</div></div>
                        <div class="eval-metric-card"><div class="metric-value">${formatPercent(compl)}</div><div class="metric-label">Completude</div></div>
                        <div class="eval-metric-card"><div class="metric-value">${(r.latency_seconds || 0).toFixed(1)}s</div><div class="metric-label">Latence</div></div>
                    </div>
                    <p style="font-size:0.82rem;color:var(--text-tertiary);margin-bottom:4px"><strong>Reponse attendue :</strong></p>
                    <p style="font-size:0.82rem;color:var(--info);padding:8px;background:var(--info-bg);border-radius:6px;margin-bottom:8px">${escapeHtml(r.expected_answer || "")}</p>
                    <p style="font-size:0.82rem;color:var(--text-tertiary);margin-bottom:4px"><strong>Reponse generee :</strong></p>
                    <p style="font-size:0.82rem;color:var(--success);padding:8px;background:var(--success-bg);border-radius:6px">${escapeHtml((r.generated_answer || "").substring(0, 400))}</p>
                </div>
            </div>`;
        }
    }

    el.innerHTML = html;
}

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------

function escapeHtml(text) {
    const map = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" };
    return String(text || "").replace(/[&<>"']/g, (m) => map[m]);
}

function formatPercent(val) {
    return `${Math.round((val || 0) * 100)}%`;
}

function scrollToBottom() {
    chatArea.scrollTop = chatArea.scrollHeight;
}

function highlightNewCode(el) {
    el.querySelectorAll("pre code:not(.hljs)").forEach((block) => {
        hljs.highlightElement(block);
    });
}
