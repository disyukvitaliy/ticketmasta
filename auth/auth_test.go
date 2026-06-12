package main

import (
	dbpkg "auth/db"
	"auth/models"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"testing"
	"time"

	"github.com/hibiken/asynq"
	"golang.org/x/crypto/bcrypt"
)

var testDB *dbpkg.DB

type testApp struct {
	Handler    http.Handler
	DB         *dbpkg.DB
	TaskClient *fakeTaskClient
}

func TestMain(m *testing.M) {
	dsn := os.Getenv("AUTH_DB_DSN")
	if dsn == "" {
		fmt.Fprintln(os.Stderr, "AUTH_DB_DSN is required")
		os.Exit(1)
	}

	if !strings.Contains(dsn, "/auth_test?") {
		fmt.Fprintf(os.Stderr, "AUTH_DB_DSN must point to auth_test, got %q\n", dsn)
		os.Exit(1)
	}

	var err error
	var closeTestDB func()
	testDB, closeTestDB, err = dbpkg.Open(dsn)
	if err != nil {
		fmt.Fprintf(os.Stderr, "open db: %v\n", err)
		os.Exit(1)
	}

	code := m.Run()
	closeTestDB()
	os.Exit(code)
}

func newTestApp(t *testing.T) *testApp {
	t.Helper()

	tx := testDB.Gorm.Begin()
	if tx.Error != nil {
		t.Fatalf("begin transaction: %v", tx.Error)
	}

	t.Cleanup(func() {
		if err := tx.Rollback().Error; err != nil {
			t.Fatalf("rollback transaction: %v", err)
		}
	})

	db := &dbpkg.DB{Gorm: tx}
	taskClient := &fakeTaskClient{}

	return &testApp{
		Handler:    newHandler(&Server{DB: db, AsynqClient: taskClient}),
		DB:         db,
		TaskClient: taskClient,
	}
}

type fakeTaskClient struct {
	tasks []*asynq.Task
}

func (tc *fakeTaskClient) Enqueue(task *asynq.Task, opts ...asynq.Option) (*asynq.TaskInfo, error) {
	tc.tasks = append(tc.tasks, task)
	return &asynq.TaskInfo{
		ID:    "test-task-id",
		Queue: "default",
	}, nil
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
