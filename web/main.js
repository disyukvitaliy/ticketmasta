async function handleLogin() {
    let result = await fetch('http://api.localhost/auth/login')
    let token = await result.text()
    localStorage.setItem('access-token', token)
    window.location.href = "/profile.html"
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