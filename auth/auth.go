package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"strings"
	"time"

	"gorm.io/gorm"

	dbpkg "auth/db"
	"auth/models"

	"golang.org/x/crypto/bcrypt"
)

type Server struct {
	DB *dbpkg.DB
}

type LoginRequest struct {
	Email    string `json:"email"`
	Password string `json:"password"`
}

type RegisterRequest struct {
	Email    string `json:"email"`
	Password string `json:"password"`
	Confirm  string `json:"confirm"`
	Terms    bool   `json:"terms"`
}

func (s *Server) Refresh(w http.ResponseWriter, r *http.Request) {
	refreshTokenBytes, err := io.ReadAll(r.Body)
	if err != nil {
		http.Error(w, "could not read body", http.StatusBadRequest)
		return
	}

	var refreshToken models.RefreshToken
	err = s.DB.Gorm.
		Preload("User").
		Where("revoked_at IS NULL").
		Where("expires_at > NOW()").
		Where("token_hash = ?", hashToken(refreshTokenBytes)).
		Take(&refreshToken).Error

	if err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			http.Error(w, "invalid credentials", http.StatusUnauthorized)
			return
		}
		http.Error(w, "db error", http.StatusInternalServerError)
		return
	}

	tokenString, err := generateJWT(refreshToken.User)
	if err != nil {
		http.Error(w, "could not create token", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "text/plain; charset=utf-8")
	_, _ = io.WriteString(w, tokenString)
}

func (s *Server) Login(w http.ResponseWriter, r *http.Request) {
	var req LoginRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}

	if req.Email == "" {
		http.Error(w, "email is required", http.StatusBadRequest)
		return
	}

	if req.Password == "" {
		http.Error(w, "password is required", http.StatusBadRequest)
		return
	}

	var u models.User
	err := s.DB.Gorm.Where("email = ?", req.Email).Take(&u).Error
	if err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			http.Error(w, "invalid credentials", http.StatusUnauthorized)
			return
		}
		http.Error(w, "db error", http.StatusInternalServerError)
		return
	}

	if bcrypt.CompareHashAndPassword([]byte(u.PasswordHash), []byte(req.Password)) != nil {
		http.Error(w, "invalid credentials", http.StatusUnauthorized)
		return
	}

	tokenString, err := generateJWT(&u)
	if err != nil {
		http.Error(w, "could not create token", http.StatusInternalServerError)
		return
	}

	refreshTokenString, refreshTokenHash := generateToken()
	refreshToken := models.RefreshToken{
		UserID:    u.ID,
		TokenHash: refreshTokenHash,
		ExpiresAt: time.Now().Add(7 * 24 * time.Hour),
	}

	if err := s.DB.Gorm.Create(&refreshToken).Error; err != nil {
		http.Error(w, "could not create token", http.StatusInternalServerError)
		return
	}

	// For backward-compat with the current frontend, return plain text token
	w.Header().Set("Content-Type", "text/plain; charset=utf-8")
	_, _ = io.WriteString(w, tokenString+"|"+refreshTokenString)
}

func (s *Server) Register(w http.ResponseWriter, r *http.Request) {
	var req RegisterRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}

	email := strings.TrimSpace(strings.ToLower(req.Email))
	if email == "" {
		http.Error(w, "email is required", http.StatusBadRequest)
		return
	}
	if req.Password == "" {
		http.Error(w, "password is required", http.StatusBadRequest)
		return
	}
	if req.Confirm == "" {
		http.Error(w, "confirm is required", http.StatusBadRequest)
		return
	}
	if req.Confirm != req.Password {
		http.Error(w, "passwords do not match", http.StatusBadRequest)
		return
	}
	if !req.Terms {
		http.Error(w, "terms must be accepted", http.StatusBadRequest)
		return
	}

	// Hash password
	hash, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
	if err != nil {
		http.Error(w, "hash error", http.StatusInternalServerError)
		return
	}

	u := models.User{
		Email:        email,
		PasswordHash: string(hash),
		Role:         "user",
	}

	if err := s.DB.Gorm.Create(&u).Error; err != nil {
		// Use GORM's sentinel error for unique constraint violations
		if errors.Is(err, gorm.ErrDuplicatedKey) {
			http.Error(w, "email already exists", http.StatusConflict)
			return
		}
		http.Error(w, "db error", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "text/plain; charset=utf-8")
	w.WriteHeader(http.StatusCreated)
	_, _ = io.WriteString(w, "ok")
}

func requestIDMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		rid := r.Header.Get("X-Request-ID")
		if rid == "" {
			rid = fmt.Sprintf("%d", time.Now().UnixNano())
		}
		// set header for response so downstream/upstream can see it
		w.Header().Set("X-Request-ID", rid)
		// put into context
		ctx := context.WithValue(r.Context(), "request_id", rid)
		r = r.WithContext(ctx)
		next.ServeHTTP(w, r)
	})
}

func loggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		rid, _ := r.Context().Value("request_id").(string)
		log.Printf("req_id=%s %s %s", rid, r.Method, r.URL)
		next.ServeHTTP(w, r)
	})
}

func newHandler(srv *Server) http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("POST /login", srv.Login)
	mux.HandleFunc("POST /register", srv.Register)
	mux.HandleFunc("POST /refresh", srv.Refresh)

	return requestIDMiddleware(loggingMiddleware(mux))
}

func main() {
	dsn := os.Getenv("AUTH_DB_DSN")
	gdb, closer, err := dbpkg.Open(dsn)
	if err != nil {
		log.Fatalf("failed to open GORM DB: %v", err)
	}
	defer func() {
		if err := closer(); err != nil {
			log.Printf("db close error: %v", err)
		}
	}()
	log.Println("GORM connected to Postgres successfully")

	srv := &Server{DB: gdb}

	log.Println("Starting server on :3000")
	if err := http.ListenAndServe(":3000", newHandler(srv)); err != nil {
		log.Fatalf("http server error: %v", err)
	}
}
