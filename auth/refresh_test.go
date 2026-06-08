package main

import (
	"net/http"
	"testing"
	"time"
)

func TestRefreshSuccess(t *testing.T) {
	app := newTestApp(t)
	user := createUser(t, app.DB, "test@example.com", "password")
	login := app.post("/login", `{"email":"`+user.Email+`","password":"password"}`)
	_, refreshToken := loginTokens(t, login.Body.String())

	rec := app.post("/refresh", refreshToken)

	assertStatus(t, rec, http.StatusOK)
	assertBodyPresent(t, rec.Body.String(), "access token")
}

func TestRefreshUnknownToken(t *testing.T) {
	app := newTestApp(t)
	rec := app.post("/refresh", "wrong-refresh-token")

	assertStatus(t, rec, http.StatusUnauthorized)
	assertBodyContains(t, rec, "invalid credentials")
}

func TestRefreshExpiredToken(t *testing.T) {
	app := newTestApp(t)
	user := createUser(t, app.DB, "test@example.com", "password")
	_, refreshToken := createRefreshToken(t, app, user, time.Now().Add(-time.Hour), nil)

	rec := app.post("/refresh", refreshToken)

	assertStatus(t, rec, http.StatusUnauthorized)
	assertBodyContains(t, rec, "invalid credentials")
}

func TestRefreshRevokedToken(t *testing.T) {
	app := newTestApp(t)
	user := createUser(t, app.DB, "test@example.com", "password")
	revokedAt := time.Now()
	_, refreshToken := createRefreshToken(t, app, user, time.Now().Add(time.Hour), &revokedAt)

	rec := app.post("/refresh", refreshToken)

	assertStatus(t, rec, http.StatusUnauthorized)
	assertBodyContains(t, rec, "invalid credentials")
}
