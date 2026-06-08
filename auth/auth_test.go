package main

import (
	dbpkg "auth/db"
	"auth/models"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"testing"
	"time"

	"golang.org/x/crypto/bcrypt"
)

type testApp struct {
	Handler http.Handler
	DB      *dbpkg.DB
}

func newTestApp(t *testing.T) *testApp {
	t.Helper()

	gdb := openTestDB(t)
	clearTestDB(t, gdb)

	return &testApp{
		Handler: newHandler(&Server{DB: gdb}),
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
	t.Cleanup(closer)

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

func createUser(t *testing.T, db *dbpkg.DB, email, password string) models.User {
	t.Helper()

	hash, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	if err != nil {
		t.Fatalf("hash could not be generated for the password %q", password)
	}

	user := models.User{
		Email:        email,
		PasswordHash: string(hash),
	}

	err = db.Gorm.Create(&user).Error
	if err != nil {
		t.Fatalf("could not create user %q: %v", email, err)
	}

	return user
}

func createRefreshToken(t *testing.T, app *testApp, user models.User, expiresAt time.Time, revokedAt *time.Time) (models.RefreshToken, string) {
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

	return refreshToken, token
}

func (app *testApp) post(path string, body string) *httptest.ResponseRecorder {
	req := httptest.NewRequest(http.MethodPost, path, strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")

	rec := httptest.NewRecorder()
	app.Handler.ServeHTTP(rec, req)

	return rec
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

func assertBodyPresent(t *testing.T, body string, name string) {
	t.Helper()

	if strings.TrimSpace(body) == "" {
		t.Fatalf("%s is empty", name)
	}
}
