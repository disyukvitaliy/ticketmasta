package main

import (
	"auth/models"
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
	refreshToken := createRefreshToken(t, app, user, time.Now().Add(-time.Hour), nil)

	rec := app.post("/refresh", refreshToken)

	assertStatus(t, rec, http.StatusUnauthorized)
	assertBodyContains(t, rec, "invalid credentials")
}

func TestRefreshRevokedToken(t *testing.T) {
	app := newTestApp(t)
	user := createUser(t, app.DB, "test@example.com", "password")
	revokedAt := time.Now()
	refreshToken := createRefreshToken(t, app, user, time.Now().Add(time.Hour), &revokedAt)

	rec := app.post("/refresh", refreshToken)

	assertStatus(t, rec, http.StatusUnauthorized)
	assertBodyContains(t, rec, "invalid credentials")
}

func createRefreshToken(t *testing.T, app *testApp, user models.User, expiresAt time.Time, revokedAt *time.Time) string {
	t.Helper()

	token, tokenHash := generateToken()
	refreshToken := models.RefreshToken{
		UserID:    user.ID,
		TokenHash: tokenHash,
		ExpiresAt: expiresAt,
		RevokedAt: revokedAt,
	}

	if err := app.DB.Gorm.Create(&refreshToken).Error; err != nil {
		t.Fatalf("create refresh token: %v", err)
	}

	return token
}
