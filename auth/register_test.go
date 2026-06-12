package main

import (
	"auth/models"
	"net/http"
	"testing"
	"time"
)

func TestRegisterInvalidJSON(t *testing.T) {
	app := newTestApp(t)
	rec := app.post("/register", `{bad json`)

	assertStatus(t, rec, http.StatusBadRequest)
	assertBodyContains(t, rec, "bad json")
}

func TestRegisterMissingEmail(t *testing.T) {
	app := newTestApp(t)
	rec := app.post("/register", `{"password":"secret","confirm":"secret","terms":true}`)

	assertStatus(t, rec, http.StatusBadRequest)
	assertBodyContains(t, rec, "email is required")
}

func TestRegisterMissingPassword(t *testing.T) {
	app := newTestApp(t)
	rec := app.post("/register", `{"email":"test@example.com","confirm":"secret","terms":true}`)

	assertStatus(t, rec, http.StatusBadRequest)
	assertBodyContains(t, rec, "password is required")
}

func TestRegisterMissingConfirm(t *testing.T) {
	app := newTestApp(t)
	rec := app.post("/register", `{"email":"test@example.com","password":"secret","terms":true}`)

	assertStatus(t, rec, http.StatusBadRequest)
	assertBodyContains(t, rec, "confirm is required")
}

func TestRegisterPasswordMismatch(t *testing.T) {
	app := newTestApp(t)
	rec := app.post("/register", `{"email":"test@example.com","password":"secret","confirm":"different","terms":true}`)

	assertStatus(t, rec, http.StatusBadRequest)
	assertBodyContains(t, rec, "passwords do not match")
}

func TestRegisterTermsNotAccepted(t *testing.T) {
	app := newTestApp(t)
	rec := app.post("/register", `{"email":"test@example.com","password":"secret","confirm":"secret","terms":false}`)

	assertStatus(t, rec, http.StatusBadRequest)
	assertBodyContains(t, rec, "terms must be accepted")
}

func TestRegisterCreatesUser(t *testing.T) {
	app := newTestApp(t)
	email := testEmail()

	rec := app.post("/register", validRegisterBody(email))

	assertStatus(t, rec, http.StatusCreated)
	assertBodyContains(t, rec, "ok")

	var user models.User
	if err := app.DB.Gorm.Where("email = ?", email).Take(&user).Error; err != nil {
		t.Fatalf("find user: %v", err)
	}
	if user.PasswordHash == "secret" {
		t.Fatal("password was stored as plain text")
	}
	if len(app.TaskClient.tasks) == 0 {
		t.Fatal("task was not enqueued")
	}
}

func TestRegisterDuplicateEmail(t *testing.T) {
	app := newTestApp(t)
	email := testEmail()

	first := app.post("/register", validRegisterBody(email))
	assertStatus(t, first, http.StatusCreated)

	second := app.post("/register", validRegisterBody(email))
	assertStatus(t, second, http.StatusConflict)
	assertBodyContains(t, second, "email already exists")
}

func validRegisterBody(email string) string {
	return `{"email":"` + email + `","password":"secret","confirm":"secret","terms":true}`
}

func testEmail() string {
	return "register-test-" + time.Now().Format("20060102150405.000000000") + "@example.com"
}
