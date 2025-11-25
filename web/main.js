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

    const token = await res.text();
    localStorage.setItem('access-token', token);
    window.location.href = "/profile.html";
}

async function handleLogout() {
    localStorage.removeItem('access-token')
    window.location.href = "/"
}

async function getProfile() {
    let result = await fetch('http://api.localhost/core/profile', {
        headers: {
            "Authorization": `Bearer ${localStorage.getItem('access-token')}`,
        }
    })
    let profile = await result.text()
    document.getElementById('profile').innerText = profile
}
// Attach submit handler for the login form to use handleLogin()
document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('login-form');
  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      handleLogin();
    });
  }
});
