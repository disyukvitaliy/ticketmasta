package main

import (
	"auth/models"
	"net/http"
	"testing"
	"time"
)

func TestLogoutSuccess(t *testing.T) {
	app := newTestApp(t)
	user := createUser(t, app.DB, "test@example.com", "password")
	refreshTokenRow, refreshToken := createRefreshToken(t, app, user, time.Now().Add(time.Hour), nil)

	rec := app.post("/logout", refreshToken)

	assertStatus(t, rec, http.StatusNoContent)

	var savedRefreshToken models.RefreshToken
	if err := app.DB.Take(&savedRefreshToken, refreshTokenRow.ID).Error; err != nil {
		t.Fatalf("find refresh token: %v", err)
	}
	if savedRefreshToken.RevokedAt == nil {
		t.Fatal("refresh token was not revoked")
	}
}

func TestLogoutUnknownToken(t *testing.T) {
	app := newTestApp(t)
	user := createUser(t, app.DB, "test@example.com", "password")
	refreshTokenRow, _ := createRefreshToken(t, app, user, time.Now().Add(time.Hour), nil)

	rec := app.post("/logout", "wrong-refresh-token")

	assertStatus(t, rec, http.StatusNoContent)

	var savedRefreshToken models.RefreshToken
	if err := app.DB.Take(&savedRefreshToken, refreshTokenRow.ID).Error; err != nil {
		t.Fatalf("find refresh token: %v", err)
	}
	if savedRefreshToken.RevokedAt != nil {
		t.Fatal("logout with unknown token revoked another refresh token")
	}
}
