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
        canResendConfirmation: false,
        resendingConfirmation: false,
        resendMessage: '',

        async submit() {
            this.canResendConfirmation = false;
            this.resendMessage = '';

            const result = await fetch('http://api.localhost/auth/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({email: this.email.trim(), password: this.password})
            });

            if (!result.ok) {
                if (result.status === 403) {
                    this.error = 'Your email has not been confirmed.';
                    this.canResendConfirmation = true;
                    return;
                }

                this.error = `Login failed: ${await result.text()}`;
                return;
            }

            const [accessToken, refreshToken] = (await result.text()).split('|');
            localStorage.setItem('access-token', accessToken);
            localStorage.setItem('refresh-token', refreshToken);
            window.location.href = '/';
        },

        async resendConfirmation() {
            this.resendingConfirmation = true;
            this.resendMessage = '';

            const result = await fetch('http://api.localhost/auth/confirmation/resend', {
                method: 'POST',
                body: this.email.trim()
            });

            this.resendingConfirmation = false;

            if (result.status === 202) {
                this.resendMessage = 'If your account needs confirmation, we will send a new link.';
                this.canResendConfirmation = false;
                return;
            }

            this.resendMessage = 'Could not request a confirmation email. Please try again later.';
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
        registered: false,

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
                this.password = '';
                this.confirm = '';
                this.terms = false;
                this.error = '';
                this.registered = true;
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

            const result = await fetch('http://api.localhost/auth/confirmation', {
                method: 'POST',
                body: token
            });

            if (result.status === 404) {
                this.status = 'This confirmation link has expired or has already been used.';
                return;
            }

            if (result.status !== 204) {
                this.status = 'Something went wrong. Please try again later.';
                return;
            }

            this.status = 'Email confirmed.';
            this.confirmed = true;
        }
    };
}

function profilePage() {
    return {
        profile: null,
        status: 'Loading...',
        loading: false,

        async init() {
            if (!localStorage.getItem('access-token')) {
                window.location.href = '/login';
                return;
            }

            await this.load();
        },

        async load() {
            this.loading = true;
            this.status = 'Loading...';

            try {
                for (let attempt = 0; attempt < 5; attempt++) {
                    const result = await apiFetch('/core/profile');
                    if (result.status === 401) {
                        window.location.href = '/login';
                        return;
                    }

                    if (result.ok) {
                        this.profile = await result.json();
                        this.status = '';
                        return;
                    }

                    if (result.status !== 404) {
                        this.status = 'Could not load your profile. Please try again.';
                        return;
                    }

                    this.status = 'We are setting up your profile. Please wait a moment.';
                    if (attempt < 4) {
                        await new Promise(resolve => setTimeout(resolve, 1000));
                    }
                }

                this.status = 'Your profile is taking longer to prepare. Please try again shortly.';
            } catch {
                this.status = 'Could not load your profile. Please try again.';
            } finally {
                this.loading = false;
            }
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

function formatPrice(priceCents) {
    return `$${(priceCents / 100).toFixed(2)}`;
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

function eventPage() {
    return {
        event: null,
        ticketTypes: [],
        quantities: {},
        status: 'Loading...',

        async init() {
            const match = window.location.pathname.match(/^\/events\/(\d+)$/);
            if (!match) {
                this.status = 'Event is missing.';
                return;
            }

            const eventId = match[1];
            const eventResult = await apiFetch(`/core/events/${eventId}`);
            if (!eventResult.ok) {
                this.status = eventResult.status === 404 ? 'Event not found.' : `Could not load event: ${eventResult.status}`;
                return;
            }

            this.event = await eventResult.json();

            const ticketTypesResult = await apiFetch(`/core/events/${eventId}/ticket-types`);
            if (!ticketTypesResult.ok) {
                this.status = `Could not load ticket types: ${ticketTypesResult.status}`;
                return;
            }

            this.ticketTypes = await ticketTypesResult.json();
            this.status = this.ticketTypes.length ? '' : 'No ticket types are available.';
        },

        ticketTypeLabel(ticketType) {
            return `${ticketType.name} — ${formatPrice(ticketType.price_cents)} — ${ticketType.quantity} available`;
        },

        async buy(ticketType) {
            const quantity = this.quantities[ticketType.id];
            const result = await apiFetch(`/core/ticket-types/${ticketType.id}/holds`, {
                method: 'POST',
                body: new URLSearchParams({quantity})
            });

            if (!result.ok) {
                this.status = `Could not reserve tickets: ${result.status}`;
                return;
            }

            const ticketHold = await result.json();
            window.location.href = `/ticket-holds/${ticketHold.id}`;
        }
    };
}

function ticketHoldPage() {
    return {
        ticketHold: null,
        ticketType: null,
        event: null,
        venue: null,
        status: 'Loading...',

        async init() {
            const match = window.location.pathname.match(/^\/ticket-holds\/(\d+)$/);
            if (!match) {
                this.status = 'Ticket hold is missing.';
                return;
            }

            const result = await apiFetch(`/core/ticket-holds/${match[1]}`);
            if (!result.ok) {
                this.status = result.status === 404 ? 'Ticket hold not found.' : `Could not load ticket hold: ${result.status}`;
                return;
            }

            this.ticketHold = await result.json();

            const ticketTypeResult = await apiFetch(`/core/ticket-types/${this.ticketHold.ticket_type_id}`);
            if (!ticketTypeResult.ok) {
                this.status = `Could not load ticket type: ${ticketTypeResult.status}`;
                return;
            }

            this.ticketType = await ticketTypeResult.json();

            const eventResult = await apiFetch(`/core/events/${this.ticketType.event_id}`);
            if (!eventResult.ok) {
                this.status = `Could not load event: ${eventResult.status}`;
                return;
            }

            this.event = await eventResult.json();
            this.venue = this.event.venue;
            this.status = '';
        },

        async complete() {
            const result = await apiFetch(`/core/ticket-holds/${this.ticketHold.id}/complete`, {
                method: 'POST'
            });

            if (!result.ok) {
                this.status = `Could not complete purchase: ${result.status}`;
                return;
            }

            this.ticketHold.status = 'completed';
            this.status = '';
        },

        async cancel() {
            const result = await apiFetch(`/core/ticket-holds/${this.ticketHold.id}`, {
                method: 'DELETE'
            });

            if (!result.ok) {
                this.status = `Could not cancel hold: ${result.status}`;
                return;
            }

            this.ticketHold.status = 'canceled';
            this.status = '';
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
