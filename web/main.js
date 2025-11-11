async function handleLogin() {
    const emailInput = document.getElementById('email');
    const email = emailInput ? emailInput.value.trim() : '';
    if (!email) {
        alert('Please enter your email');
        return;
    }

    const res = await fetch('http://api.localhost/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
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
