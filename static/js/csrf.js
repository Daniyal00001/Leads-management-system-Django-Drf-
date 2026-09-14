// Reads Django's csrftoken cookie so we can send it on every AJAX POST.
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function getCsrfToken() {
    let token = getCookie('csrftoken');
    if (!token) {
        const input = document.querySelector('[name=csrfmiddlewaretoken]');
        if (input) token = input.value;
    }
    return token || '';
}

// Shared fetch wrapper.....every AJAX call in this project use this
function apiPost(url, body, isFormData = false) {
    const headers = { 'X-CSRFToken': getCsrfToken() };
    if (!isFormData) headers['Content-Type'] = 'application/json';

    return fetch(url, {
        method: 'POST',
        headers,
        body: isFormData ? body : JSON.stringify(body),
    }).then(async (res) => {
        const data = await res.json();
        if (!res.ok) throw { status: res.status, data };
        return data;
    });
}


function apiGet(url) {
    return fetch(url).then(async (res) => {
        const data = await res.json();
        if (!res.ok) throw { status: res.status, data };
        return data;
    });
}

function formatApiError(err) {
    if (!err || !err.data) return "Something went wrong.";
    const data = err.data;
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail)) return data.detail.join(" ");
    try {
        return Object.entries(data)
            .map(([key, value]) => {
                const text = Array.isArray(value) ? value.join(", ") : value;
                return `${key}: ${text}`;
            })
            .join(" ");
    } catch (e) {
        return "Something went wrong.";
    }
}

function initComments(modelName, objectId) {
    const list = document.getElementById("comments-list");
    const form = document.getElementById("comment-form");
    if (!list || !form) return;

    function loadComments() {
        apiGet(`/api/comments/?model_name=${modelName}&object_id=${objectId}`)
            .then((data) => {
                const results = data.results || data;
                if (!results.length) {
                    list.innerHTML = '<div class="empty-state"><p class="empty-title">No comments yet</p><p class="empty-text">Start the thread for this record.</p></div>';
                    return;
                }
                list.innerHTML = results.map((comment) => `
                    <div class="comment">
                        <strong>${comment.user.email}</strong>
                        <span class="muted"> — ${new Date(comment.created_at).toLocaleString()}</span>
                        <p>${comment.body}</p>
                        ${(comment.attachments || []).map((attachment) => `
                            <img src="${attachment.image}" class="comment-img" alt="">
                        `).join("")}
                    </div>
                `).join("");
            })
            .catch(() => {
                list.innerHTML = '<p class="muted">Could not load comments.</p>';
            });
    }

    form.addEventListener("submit", function (event) {
        event.preventDefault();
        const body = document.getElementById("comment-body").value;
        const files = document.getElementById("comment-images").files;
        const formData = new FormData();
        formData.append("model_name", modelName);
        formData.append("object_id", objectId);
        formData.append("body", body);
        for (const file of files) formData.append("images", file);

        apiPost("/api/comments/create/", formData, true)
            .then(() => {
                form.reset();
                loadComments();
            })
            .catch((err) => alert(formatApiError(err)));
    });

    loadComments();
}