async function refreshAccessToken() {
    const refreshToken = localStorage.getItem('refresh-token');
    if (!refreshToken) {
        return false;
    }

    const result = await fetch('http://api.localhost/auth/refresh', {
        method: 'POST',
        body: refreshToken
    });

    if (!result.ok) {
        localStorage.removeItem('access-token');
        localStorage.removeItem('refresh-token');
        window.location.href = '/login';
        return false;
    }

    localStorage.setItem('access-token', await result.text());
    return true;
}

async function apiFetch(path, options = {}) {
    const headers = new Headers(options.headers || {});
    headers.set('Authorization', `Bearer ${localStorage.getItem('access-token')}`);

    let result = await fetch(`http://api.localhost${path}`, {...options, headers});

    if (result.status !== 401 || !await refreshAccessToken()) {
        return result;
    }

    headers.set('Authorization', `Bearer ${localStorage.getItem('access-token')}`);
    return fetch(`http://api.localhost${path}`, {...options, headers});
}

function homePage() {
    return {logged: Boolean(localStorage.getItem('access-token'))};
}

function loginPage() {
    return {
        email: '',
        password: '',
        error: '',

        async submit() {
            const result = await fetch('http://api.localhost/auth/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({email: this.email.trim(), password: this.password})
            });

            if (!result.ok) {
                this.error = `Login failed: ${await result.text()}`;
                return;
            }

            const [accessToken, refreshToken] = (await result.text()).split('|');
            localStorage.setItem('access-token', accessToken);
            localStorage.setItem('refresh-token', refreshToken);
            window.location.href = '/profile';
        }
    };
}

function registerPage() {
    return {
        email: '',
        password: '',
        confirm: '',
        terms: false,
        error: '',

        async submit() {
            const result = await fetch('http://api.localhost/auth/register', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    email: this.email,
                    password: this.password,
                    confirm: this.confirm,
                    terms: this.terms
                })
            });

            if (result.status === 201) {
                window.location.href = '/login';
                return;
            }

            this.error = `Registration failed: ${(await result.text()) || result.status}`;
        }
    };
}

function confirmPage() {
    return {
        status: 'Confirming your email...',
        confirmed: false,

        async confirm() {
            const token = new URLSearchParams(window.location.search).get('token');
            if (!token) {
                this.status = 'Confirmation token is missing.';
                return;
            }

            const result = await fetch('http://api.localhost/auth/confirm', {
                method: 'POST',
                body: token
            });
            const message = await result.text();

            if (!result.ok) {
                this.status = `Confirmation failed: ${message || result.status}`;
                return;
            }

            this.status = message || 'Email confirmed.';
            this.confirmed = true;
        }
    };
}

function profilePage() {
    return {
        profile: '',
        error: '',

        async load() {
            const result = await apiFetch('/core/profile');
            if (!result.ok) {
                this.error = `Could not load profile: ${result.status}`;
                return;
            }

            this.profile = await result.text();
        },

        async logout() {
            const refreshToken = localStorage.getItem('refresh-token');
            if (refreshToken) {
                await fetch('http://api.localhost/auth/logout', {
                    method: 'POST',
                    body: refreshToken
                });
            }

            localStorage.removeItem('access-token');
            localStorage.removeItem('refresh-token');
            window.location.href = '/';
        }
    };
}

function eventsPage() {
    return cataloguePage('/core/events', event => `${event.name} — ${event.venue.name}`);
}

function venuesPage() {
    return {
        ...cataloguePage('/core/venues'),
        venues: [],

        async load() {
            const result = await apiFetch(`/core/venues?page=${this.page}`);
            if (!result.ok) {
                this.status = `Could not load venues: ${result.status}`;
                return;
            }

            this.venues = await result.json();
            this.status = this.venues.length ? '' : 'No venues are available.';
        }
    };
}

function venuePage() {
    return {
        ...cataloguePage('', event => event.name),
        venue: null,
        venueId: null,

        async init() {
            const match = window.location.pathname.match(/^\/venues\/(\d+)$/);
            if (!match) {
                this.status = 'Venue is missing.';
                return;
            }

            this.venueId = match[1];
            const result = await apiFetch(`/core/venues/${this.venueId}`);
            if (!result.ok) {
                this.status = result.status === 404 ? 'Venue not found.' : `Could not load venue: ${result.status}`;
                return;
            }

            this.venue = await result.json();
            await this.load();
        },

        async load() {
            const result = await apiFetch(`/core/venues/${this.venueId}/events?page=${this.page}`);
            if (!result.ok) {
                this.status = `Could not load events: ${result.status}`;
                return;
            }

            this.items = await result.json();
            this.status = this.items.length ? '' : 'No upcoming events are available.';
        }
    };
}

function cataloguePage(path, itemLabel) {
    return {
        items: [],
        page: 1,
        status: 'Loading...',
        itemLabel,

        async load() {
            const result = await apiFetch(`${path}?page=${this.page}`);
            if (!result.ok) {
                this.status = `Could not load items: ${result.status}`;
                return;
            }

            this.items = await result.json();
            this.status = this.items.length ? '' : 'No items are available.';
        },

        previous() {
            this.page -= 1;
            this.load();
        },

        next() {
            this.page += 1;
            this.load();
        }
    };
}
