const API_URL = "http://127.0.0.1:8000/api/tasks/";
const DEFAULT_STATE = {
    search: "",
    status: "",
    priority: "",
    ordering: "-created_at",
    page: "1",
    page_size: "5"
};

const VALID_STATUS = new Set(["", "pending", "completed"]);
const VALID_PRIORITY = new Set(["", "low", "medium", "high"]);
const VALID_ORDERING = new Set([
    "-created_at",
    "created_at",
    "-updated_at",
    "updated_at",
    "-priority",
    "priority",
    "-status",
    "status"
]);

const elements = {
    apiBaseLabel: document.getElementById("apiBaseLabel"),
    filtersForm: document.getElementById("filtersForm"),
    createTaskForm: document.getElementById("createTaskForm"),
    search: document.getElementById("search"),
    status: document.getElementById("statusFilter"),
    priority: document.getElementById("priorityFilter"),
    ordering: document.getElementById("ordering"),
    pageSize: document.getElementById("pageSize"),
    pageNumber: document.getElementById("pageNumber"),
    createTitle: document.getElementById("createTitle"),
    createDescription: document.getElementById("createDescription"),
    createPriority: document.getElementById("createPriority"),
    createStatus: document.getElementById("createStatus"),
    createStatusLine: document.getElementById("createStatusLine"),
    activeQueryChips: document.getElementById("activeQueryChips"),
    browserUrlPreview: document.getElementById("browserUrlPreview"),
    requestUrlPreview: document.getElementById("requestUrlPreview"),
    openApiLink: document.getElementById("openApiLink"),
    totalCount: document.getElementById("totalCount"),
    pageSummary: document.getElementById("pageSummary"),
    pageSizeSummary: document.getElementById("pageSizeSummary"),
    rowsShown: document.getElementById("rowsShown"),
    rangeSummary: document.getElementById("rangeSummary"),
    taskTableBody: document.getElementById("taskTableBody"),
    emptyState: document.getElementById("emptyState"),
    responsePreview: document.getElementById("responsePreview"),
    prevPageButton: document.getElementById("prevPageButton"),
    nextPageButton: document.getElementById("nextPageButton"),
    refreshButton: document.getElementById("refreshButton"),
    resetFiltersButton: document.getElementById("resetFiltersButton"),
    resetAllButton: document.getElementById("resetAllButton"),
    toast: document.getElementById("toast")
};

elements.apiBaseLabel.textContent = API_URL;

let currentState = { ...DEFAULT_STATE };
let lastPayload = { count: 0, next: null, previous: null, results: [] };
let toastTimer = null;

function clampInteger(value, min, max, fallback) {
    const parsed = Number.parseInt(value, 10);
    if (!Number.isFinite(parsed)) {
        return Number.parseInt(fallback, 10);
    }
    return Math.min(max, Math.max(min, parsed));
}

function sanitizeState(raw) {
    return {
        search: (raw.search || "").trim(),
        status: VALID_STATUS.has(raw.status) ? raw.status : DEFAULT_STATE.status,
        priority: VALID_PRIORITY.has(raw.priority) ? raw.priority : DEFAULT_STATE.priority,
        ordering: VALID_ORDERING.has(raw.ordering) ? raw.ordering : DEFAULT_STATE.ordering,
        page: String(clampInteger(raw.page, 1, 9999, DEFAULT_STATE.page)),
        page_size: String(clampInteger(raw.page_size, 1, 10, DEFAULT_STATE.page_size))
    };
}

function readStateFromUrl() {
    const params = new URLSearchParams(window.location.search);
    return sanitizeState({
        search: params.get("search") || "",
        status: params.get("status") || "",
        priority: params.get("priority") || "",
        ordering: params.get("ordering") || DEFAULT_STATE.ordering,
        page: params.get("page") || DEFAULT_STATE.page,
        page_size: params.get("page_size") || DEFAULT_STATE.page_size
    });
}

function buildSearchParams(state) {
    const params = new URLSearchParams();
    params.set("page", state.page);
    params.set("page_size", state.page_size);
    params.set("ordering", state.ordering);
    if (state.search) params.set("search", state.search);
    if (state.status) params.set("status", state.status);
    if (state.priority) params.set("priority", state.priority);
    return params;
}

function writeStateToUrl(state, mode) {
    if (mode === "skip") return;
    const url = new URL(window.location.href);
    url.search = buildSearchParams(state).toString();
    window.history[mode === "replace" ? "replaceState" : "pushState"](state, "", url.toString());
}

function syncControls(state) {
    elements.search.value = state.search;
    elements.status.value = state.status;
    elements.priority.value = state.priority;
    elements.ordering.value = state.ordering;
    elements.pageSize.value = state.page_size;
    elements.pageNumber.value = state.page;
}

function collectStateFromForm() {
    return sanitizeState({
        search: elements.search.value,
        status: elements.status.value,
        priority: elements.priority.value,
        ordering: elements.ordering.value,
        page: elements.pageNumber.value,
        page_size: elements.pageSize.value
    });
}

function showToast(message) {
    clearTimeout(toastTimer);
    elements.toast.textContent = message;
    elements.toast.classList.add("visible");
    toastTimer = setTimeout(() => {
        elements.toast.classList.remove("visible");
    }, 2600);
}

function setCreateStatus(message, isError) {
    elements.createStatusLine.textContent = message;
    elements.createStatusLine.style.color = isError ? "var(--danger)" : "var(--muted)";
}

function updateQueryChips(state) {
    const params = buildSearchParams(state);
    elements.activeQueryChips.innerHTML = "";
    params.forEach((value, key) => {
        const chip = document.createElement("span");
        chip.className = "chip";
        chip.textContent = `${key}=${value}`;
        elements.activeQueryChips.appendChild(chip);
    });
}

function createCell(text) {
    const cell = document.createElement("td");
    cell.textContent = text;
    return cell;
}

function createBadge(value) {
    const badge = document.createElement("span");
    badge.className = `badge ${value}`;
    badge.textContent = value;
    return badge;
}

function formatDate(value) {
    if (!value) return "-";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString();
}

function renderTasks(tasks) {
    elements.taskTableBody.innerHTML = "";
    elements.emptyState.classList.toggle("visible", tasks.length === 0);
    if (!tasks.length) return;

    tasks.forEach((task) => {
        const row = document.createElement("tr");

        const titleCell = document.createElement("td");
        titleCell.className = "title-cell";
        const title = document.createElement("div");
        title.className = "task-title";
        title.textContent = task.title;
        const description = document.createElement("div");
        description.className = "task-desc";
        description.textContent = task.description || "No description";
        titleCell.append(title, description);

        const statusCell = document.createElement("td");
        statusCell.appendChild(createBadge(task.status));

        const priorityCell = document.createElement("td");
        priorityCell.appendChild(createBadge(task.priority));

        const actionsCell = document.createElement("td");
        const actionWrap = document.createElement("div");
        actionWrap.className = "actions";

        const completeButton = document.createElement("button");
        completeButton.type = "button";
        completeButton.className = "secondary";
        completeButton.textContent = task.status === "completed" ? "Completed" : "Mark Complete";
        completeButton.disabled = task.status === "completed";
        completeButton.addEventListener("click", () => patchTask(task.id, { status: "completed" }));

        const deleteButton = document.createElement("button");
        deleteButton.type = "button";
        deleteButton.className = "danger";
        deleteButton.textContent = "Delete";
        deleteButton.addEventListener("click", () => deleteTask(task.id));

        actionWrap.append(completeButton, deleteButton);
        actionsCell.appendChild(actionWrap);

        row.append(
            titleCell,
            statusCell,
            priorityCell,
            createCell(formatDate(task.created_at)),
            createCell(formatDate(task.updated_at)),
            actionsCell
        );
        elements.taskTableBody.appendChild(row);
    });
}

function updateSummary(payload, state) {
    const tasks = Array.isArray(payload.results) ? payload.results : [];
    const total = typeof payload.count === "number" ? payload.count : tasks.length;
    const page = Number.parseInt(state.page, 10);
    const pageSize = Number.parseInt(state.page_size, 10);
    const totalPages = Math.max(1, Math.ceil(total / pageSize));
    const start = tasks.length ? (page - 1) * pageSize + 1 : 0;
    const end = tasks.length ? start + tasks.length - 1 : 0;

    elements.totalCount.textContent = String(total);
    elements.pageSummary.textContent = `${page} / ${totalPages}`;
    elements.pageSizeSummary.textContent = String(pageSize);
    elements.rowsShown.textContent = String(tasks.length);
    elements.rangeSummary.textContent = tasks.length ? `Showing ${start}-${end} of ${total}` : "Showing 0 results";
    elements.prevPageButton.disabled = !payload.previous;
    elements.nextPageButton.disabled = !payload.next;
}

function updateRequestPreview(state) {
    const query = buildSearchParams(state).toString();
    const browserUrl = `${window.location.origin}${window.location.pathname}?${query}`;
    const requestUrl = `${API_URL}?${query}`;
    elements.browserUrlPreview.textContent = browserUrl;
    elements.requestUrlPreview.textContent = requestUrl;
    elements.openApiLink.href = requestUrl;
}

function setLoading(isLoading) {
    elements.refreshButton.classList.toggle("loading", isLoading);
}

async function readResponseBody(response) {
    const type = response.headers.get("content-type") || "";
    return type.includes("application/json") ? response.json() : response.text();
}

function formatError(body) {
    if (!body) return "Unknown error";
    return typeof body === "string" ? body : JSON.stringify(body);
}

async function requestJson(url, options) {
    const response = await fetch(url, options);
    const body = await readResponseBody(response);
    if (!response.ok) {
        throw new Error(formatError(body));
    }
    return body;
}

async function loadTasks(state, historyMode) {
    currentState = sanitizeState(state);
    syncControls(currentState);
    writeStateToUrl(currentState, historyMode);
    updateQueryChips(currentState);
    updateRequestPreview(currentState);
    setLoading(true);

    const requestUrl = `${API_URL}?${buildSearchParams(currentState).toString()}`;

    try {
        const payload = await requestJson(requestUrl, {
            headers: { Accept: "application/json" }
        });

        lastPayload = payload;
        renderTasks(payload.results || []);
        updateSummary(payload, currentState);
        elements.responsePreview.textContent = JSON.stringify(payload, null, 2);
    } catch (error) {
        lastPayload = { count: 0, next: null, previous: null, results: [] };
        renderTasks([]);
        updateSummary(lastPayload, currentState);
        elements.responsePreview.textContent = JSON.stringify({
            error: error.message,
            help: "Start Django on http://127.0.0.1:8000 and keep /api/tasks/ reachable."
        }, null, 2);
        showToast(`Request failed: ${error.message}`);
    } finally {
        setLoading(false);
    }
}

async function createTask(event) {
    event.preventDefault();
    setCreateStatus("Saving task...", false);

    try {
        await requestJson(API_URL, {
            method: "POST",
            headers: {
                Accept: "application/json",
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                title: elements.createTitle.value.trim(),
                description: elements.createDescription.value.trim(),
                priority: elements.createPriority.value,
                status: elements.createStatus.value
            })
        });

        elements.createTaskForm.reset();
        elements.createPriority.value = "medium";
        elements.createStatus.value = "pending";
        setCreateStatus("Task created successfully.", false);
        showToast("Task created successfully.");
        await loadTasks({ ...currentState, page: "1" }, "replace");
    } catch (error) {
        setCreateStatus(`Create failed: ${error.message}`, true);
        showToast(`Create failed: ${error.message}`);
    }
}

async function patchTask(taskId, payload) {
    try {
        await requestJson(`${API_URL}${taskId}/`, {
            method: "PATCH",
            headers: {
                Accept: "application/json",
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });
        showToast(`Task ${taskId} updated.`);
        await loadTasks(currentState, "replace");
    } catch (error) {
        showToast(`Update failed: ${error.message}`);
    }
}

async function deleteTask(taskId) {
    try {
        const response = await fetch(`${API_URL}${taskId}/`, {
            method: "DELETE",
            headers: { Accept: "application/json" }
        });

        if (!response.ok && response.status !== 204) {
            const body = await readResponseBody(response);
            throw new Error(formatError(body));
        }

        showToast(`Task ${taskId} deleted.`);
        await loadTasks(currentState, "replace");
    } catch (error) {
        showToast(`Delete failed: ${error.message}`);
    }
}

elements.filtersForm.addEventListener("submit", (event) => {
    event.preventDefault();
    loadTasks(collectStateFromForm(), "push");
});

elements.createTaskForm.addEventListener("submit", createTask);

elements.prevPageButton.addEventListener("click", () => {
    if (!lastPayload.previous) return;
    loadTasks({ ...currentState, page: String(Math.max(1, Number.parseInt(currentState.page, 10) - 1)) }, "push");
});

elements.nextPageButton.addEventListener("click", () => {
    if (!lastPayload.next) return;
    loadTasks({ ...currentState, page: String(Number.parseInt(currentState.page, 10) + 1) }, "push");
});

elements.refreshButton.addEventListener("click", () => {
    loadTasks(currentState, "replace");
});

elements.resetFiltersButton.addEventListener("click", () => {
    loadTasks({ ...DEFAULT_STATE }, "push");
});

elements.resetAllButton.addEventListener("click", () => {
    elements.createTaskForm.reset();
    elements.createPriority.value = "medium";
    elements.createStatus.value = "pending";
    setCreateStatus("", false);
    loadTasks({ ...DEFAULT_STATE }, "push");
});

window.addEventListener("popstate", () => {
    loadTasks(readStateFromUrl(), "skip");
});

loadTasks(readStateFromUrl(), "replace");
