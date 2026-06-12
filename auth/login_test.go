package main

import (
	"auth/models"
	"net/http"
	"strings"
	"testing"
)

func TestLoginBlankEmail(t *testing.T) {
	app := newTestApp(t)
	rec := app.post("/login", `{"email":"","password":"password"}`)

	assertStatus(t, rec, http.StatusBadRequest)
	assertBodyContains(t, rec, "email is required")
}

func TestLoginBlankPassword(t *testing.T) {
	app := newTestApp(t)
	rec := app.post("/login", `{"email":"test@example.com","password":""}`)

	assertStatus(t, rec, http.StatusBadRequest)
	assertBodyContains(t, rec, "password is required")
}

func TestLoginUnknownEmail(t *testing.T) {
	app := newTestApp(t)
	rec := app.post("/login", `{"email":"wrong@example.com","password":"password"}`)

	assertStatus(t, rec, http.StatusUnauthorized)
	assertBodyContains(t, rec, "invalid credentials")
}

func TestLoginSuccess(t *testing.T) {
	app := newTestApp(t)
	user := createUser(t, app.DB, "test@example.com", "password")
	rec := app.post("/login", `{"email":"`+user.Email+`","password":"password"}`)

	assertStatus(t, rec, http.StatusOK)

	_, refreshTokenString := loginTokens(t, rec.Body.String())

	var refreshTokens []models.RefreshToken
	if err := app.DB.Where("user_id = ?", user.ID).Find(&refreshTokens).Error; err != nil {
		t.Fatalf("find refresh tokens: %v", err)
	}
	if len(refreshTokens) != 1 {
		t.Fatalf("refresh token count = %d, want 1", len(refreshTokens))
	}
	if refreshTokens[0].TokenHash != hashToken([]byte(refreshTokenString)) {
		t.Fatal("response refresh token does not match stored refresh token")
	}
}

func TestLoginInvalidPassword(t *testing.T) {
	app := newTestApp(t)
	user := createUser(t, app.DB, "test@example.com", "password")
	rec := app.post("/login", `{"email":"`+user.Email+`","password":"pass"}`)

	assertStatus(t, rec, http.StatusUnauthorized)
	assertBodyContains(t, rec, "invalid credentials")
}

func loginTokens(t *testing.T, body string) (accessToken string, refreshToken string) {
	t.Helper()

	parts := strings.Split(strings.TrimSpace(body), "|")
	if len(parts) != 2 {
		t.Fatalf("body = %q, want access token and refresh token", body)
	}

	if parts[0] == "" {
		t.Fatal("access token is empty")
	}
	if parts[1] == "" {
		t.Fatal("refresh token is empty")
	}

	return parts[0], parts[1]
}
