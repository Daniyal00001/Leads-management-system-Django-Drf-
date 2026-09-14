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

const CSRF_TOKEN = getCookie('csrftoken');

// Shared fetch wrapper.....every AJAX call in this project use this
function apiPost(url, body, isFormData = false) {
    const headers = { 'X-CSRFToken': CSRF_TOKEN };
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