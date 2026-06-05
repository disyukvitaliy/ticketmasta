package main

import (
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"testing"
	"time"

	dbpkg "auth/db"
	"auth/models"
)

type testApp struct {
	Handler http.Handler
	DB      *dbpkg.DB
}

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

func newTestApp(t *testing.T) *testApp {
	t.Helper()

	gdb := openTestDB(t)
	clearTestDB(t, gdb)
	srv := &Server{DB: gdb}

	return &testApp{
		Handler: newHandler(srv),
		DB:      gdb,
	}
}

func openTestDB(t *testing.T) *dbpkg.DB {
	t.Helper()

	dsn := os.Getenv("AUTH_DB_DSN")
	if dsn == "" {
		t.Fatal("AUTH_DB_DSN is required")
	}
	if !strings.Contains(dsn, "/auth_test?") {
		t.Fatalf("AUTH_DB_DSN must point to auth_test, got %q", dsn)
	}

	gdb, closer, err := dbpkg.Open(dsn)
	if err != nil {
		t.Fatalf("open db: %v", err)
	}
	t.Cleanup(func() {
		if err := closer(); err != nil {
			t.Fatalf("close db: %v", err)
		}
	})

	return gdb
}

func clearTestDB(t *testing.T, gdb *dbpkg.DB) {
	t.Helper()

	rows, err := gdb.Gorm.Raw(`
		SELECT quote_ident(schemaname) || '.' || quote_ident(tablename)
		FROM pg_tables
		WHERE schemaname = 'public'
			AND tablename <> 'goose_db_version'
		ORDER BY tablename
	`).Rows()
	if err != nil {
		t.Fatalf("list tables: %v", err)
	}
	defer rows.Close()

	var tables []string
	for rows.Next() {
		var table string
		if err := rows.Scan(&table); err != nil {
			t.Fatalf("scan table: %v", err)
		}
		tables = append(tables, table)
	}

	if len(tables) == 0 {
		return
	}
	if err := gdb.Gorm.Exec("TRUNCATE " + strings.Join(tables, ", ") + " RESTART IDENTITY CASCADE").Error; err != nil {
		t.Fatalf("clear test db: %v", err)
	}
}

func (app *testApp) post(path string, body string) *httptest.ResponseRecorder {
	req := httptest.NewRequest(http.MethodPost, path, strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")

	rec := httptest.NewRecorder()
	app.Handler.ServeHTTP(rec, req)

	return rec
}

func validRegisterBody(email string) string {
	return `{"email":"` + email + `","password":"secret","confirm":"secret","terms":true}`
}

func testEmail() string {
	return "register-test-" + time.Now().Format("20060102150405.000000000") + "@example.com"
}

func assertStatus(t *testing.T, rec *httptest.ResponseRecorder, want int) {
	t.Helper()

	if rec.Code != want {
		t.Fatalf("status = %d, want %d, body = %q", rec.Code, want, rec.Body.String())
	}
}

func assertBodyContains(t *testing.T, rec *httptest.ResponseRecorder, want string) {
	t.Helper()

	if !strings.Contains(rec.Body.String(), want) {
		t.Fatalf("body = %q, want it to contain %q", rec.Body.String(), want)
	}
}
