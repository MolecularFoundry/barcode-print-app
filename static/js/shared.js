// ========== API Helpers ==========

async function api(url, method = 'GET', body = null) {
    const opts = {
        method,
        headers: { 'Content-Type': 'application/json' },
    };
    if (body) opts.body = JSON.stringify(body);
    const fullUrl = (typeof BASE_URL !== 'undefined' ? BASE_URL : '') + url;
    const res = await fetch(fullUrl, opts);
    const data = await res.json();
    if (!res.ok) {
        const err = new Error(data.error || `Request failed (${res.status})`);
        err.status = res.status;
        err.data = data;
        throw err;
    }
    return data;
}

// ========== Alert System ==========

function showAlert(type, message) {
    const container = document.getElementById('alert-container');
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;
    container.appendChild(alert);
    setTimeout(() => alert.remove(), 5000);
}

// ========== Modal ==========

function showModal(title, bodyHTML, onConfirm, confirmLabel = 'Confirm') {
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-body').innerHTML = bodyHTML;
    document.getElementById('modal-overlay').classList.remove('hidden');

    const confirmBtn = document.getElementById('modal-confirm');
    // Remove old listeners by cloning
    const newBtn = confirmBtn.cloneNode(true);
    newBtn.textContent = confirmLabel;
    confirmBtn.parentNode.replaceChild(newBtn, confirmBtn);
    newBtn.addEventListener('click', () => {
        closeModal();
        onConfirm();
    });
}

function closeModal() {
    document.getElementById('modal-overlay').classList.add('hidden');
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str == null ? '' : String(str);
    return div.innerHTML;
}

// ========== User ==========

async function loadUserState() {
    const user = await api('/api/user');
    document.getElementById('username').value = user.user_name;

    const projectSelect = document.getElementById('project');
    projectSelect.innerHTML = '';
    for (const p of user.projects) {
        const opt = document.createElement('option');
        opt.value = p;
        opt.textContent = p;
        if (p === user.selected_project) opt.selected = true;
        projectSelect.appendChild(opt);
    }

    document.getElementById('nav-user-info').textContent = user.user_name;
}

async function setProject() {
    const project = document.getElementById('project').value;
    await api('/api/user/project', 'POST', { project });
}

// ========== Tabs ==========

function switchTab(tabId) {
    document.querySelectorAll('.tab-panel').forEach(el => el.classList.add('hidden'));
    document.getElementById(tabId)?.classList.remove('hidden');

    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelector(`.tab-btn[data-tab="${tabId}"]`)?.classList.add('active');
}
