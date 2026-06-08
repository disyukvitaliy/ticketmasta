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
});
