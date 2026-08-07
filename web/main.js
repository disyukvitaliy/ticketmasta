async function handleLogin() {
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const email = emailInput ? emailInput.value.trim() : '';
    const password = passwordInput ? passwordInput.value : '';

    if (!email) {
        alert('Please enter your email');
        return;
    }
    if (!password) {
        alert('Please enter your password');
        return;
    }

    const res = await fetch('http://api.localhost/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
    });

    if (!res.ok) {
        const msg = await res.text();
        alert('Login failed: ' + msg);
        return;
    }

    const raw = await res.text(); // expected format: "token|refreshToken"
    const [accessToken, refreshToken] = raw.split('|');

    localStorage.setItem('access-token', accessToken);
    localStorage.setItem('refresh-token', refreshToken);
    window.location.href = "/profile.html";
}

async function handleLogout() {
    const refreshToken = localStorage.getItem('refresh-token');

    if (refreshToken) {
        fetch('http://api.localhost/auth/logout', {
            method: 'POST',
            body: refreshToken
        });
    }

    localStorage.removeItem('access-token');
    localStorage.removeItem('refresh-token');
    window.location.href = "/";
}

async function refreshAccessToken() {
    const refreshToken = localStorage.getItem('refresh-token');
    if (!refreshToken) {
        return false;
    }

    const res = await fetch('http://api.localhost/auth/refresh', {
        method: 'POST',
        body: refreshToken
    });

    if (!res.ok) {
        localStorage.removeItem('access-token');
        localStorage.removeItem('refresh-token');
        window.location.href = "/login.html";
        return false;
    }

    localStorage.setItem('access-token', await res.text());
    return true;
}

async function apiFetch(path, options = {}) {
    const headers = new Headers(options.headers || {});
    headers.set('Authorization', `Bearer ${localStorage.getItem('access-token')}`);

    let result = await fetch(`http://api.localhost${path}`, {
        ...options,
        headers
    });

    if (result.status !== 401 || !await refreshAccessToken()) {
        return result;
    }

    headers.set('Authorization', `Bearer ${localStorage.getItem('access-token')}`);
    return fetch(`http://api.localhost${path}`, {
        ...options,
        headers
    });
}

async function getProfile() {
    let result = await apiFetch('/core/profile');

    let profile = await result.text();
    document.getElementById('profile').innerText = profile;
}

async function getEvents() {
    const status = document.getElementById('events-status');
    const list = document.getElementById('events');
    const pagination = document.getElementById('events-pagination');
    const previous = document.getElementById('events-previous');
    const next = document.getElementById('events-next');
    let currentPage = 1;

    async function loadEvents() {
        const result = await apiFetch(`/core/events?page=${currentPage}`);

        if (!result.ok) {
            status.innerText = `Could not load events: ${result.status}`;
            return;
        }

        const events = await result.json();

        list.replaceChildren();

        for (const event of events) {
            const item = document.createElement('li');
            item.innerText = `${event.name} — ${event.venue.name}`;
            list.appendChild(item);
        }

        status.hidden = events.length > 0;
        pagination.hidden = false;
        previous.disabled = currentPage === 1;
    }

    previous.addEventListener('click', () => {
        currentPage -= 1;
        loadEvents();
    });

    next.addEventListener('click', () => {
        currentPage += 1;
        loadEvents();
    });

    loadEvents();
}

// Registration handler: validate fields and call auth service
async function handleRegister() {
    const email = (document.getElementById('reg-email') || {}).value || '';
    const password = (document.getElementById('reg-password') || {}).value || '';
    const confirm = (document.getElementById('reg-password-confirm') || {}).value || '';
    const terms = (document.getElementById('reg-terms') || {}).checked || false;

    try {
        const res = await fetch('http://api.localhost/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password, confirm, terms })
        });

        const msg = await res.text();
        if (res.status === 201) {
            alert('Registration successful. Please login.');
            window.location.href = '/login.html';
            return;
        }
        alert('Registration failed: ' + (msg || res.status));
    } catch (e) {
        alert('Registration error: ' + e);
    }
}

async function handleConfirmEmail() {
    const status = document.getElementById('confirm-status');
    const loginLink = document.getElementById('confirm-login-link');
    const token = new URLSearchParams(window.location.search).get('token');

    if (!status) {
        return;
    }

    if (!token) {
        status.innerText = 'Confirmation token is missing.';
        return;
    }

    try {
        const res = await fetch('http://api.localhost/auth/confirm', {
            method: 'POST',
            body: token
        });

        const msg = await res.text();
        if (!res.ok) {
            status.innerText = 'Confirmation failed: ' + (msg || res.status);
            return;
        }

        status.innerText = msg || 'Email confirmed.';
        if (loginLink) {
            loginLink.hidden = false;
        }
    } catch (e) {
        status.innerText = 'Confirmation error: ' + e;
    }
}

// Attach submit handlers for login/register forms
document.addEventListener('DOMContentLoaded', () => {
  const loginForm = document.getElementById('login-form');
  if (loginForm) {
    loginForm.addEventListener('submit', (e) => {
      e.preventDefault();
      handleLogin();
    });
  }

  const registerForm = document.getElementById('register-form');
  if (registerForm) {
    registerForm.addEventListener('submit', (e) => {
      e.preventDefault();
      handleRegister();
    });
  }

  if (document.getElementById('confirm-status')) {
    handleConfirmEmail();
  }

  if (document.getElementById('events')) {
    getEvents();
  }
});
