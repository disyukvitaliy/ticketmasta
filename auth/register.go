package main

import (
	"auth/logging"
	"auth/models"
	"auth/tasks"
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"strings"

	"golang.org/x/crypto/bcrypt"
	"gorm.io/gorm"
)

type RegisterRequest struct {
	Email    string `json:"email"`
	Password string `json:"password"`
	Confirm  string `json:"confirm"`
	Terms    bool   `json:"terms"`
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

	if err := s.DB.Create(&u).Error; err != nil {
		if errors.Is(err, gorm.ErrDuplicatedKey) {
			http.Error(w, "email already exists", http.StatusConflict)
			return
		}
		http.Error(w, "db error", http.StatusInternalServerError)
		return
	}

	info, err := s.AsynqClient.Enqueue(tasks.NewConfirmEmailTask(u.Email))
	logger := logging.LoggerFromContext(r.Context())
	if err != nil {
		logger.Error("could not enqueue task", "error", err)
	} else {
		logger.Info("enqueued task", "id", info.ID, "queue", info.Queue)
	}

	w.Header().Set("Content-Type", "text/plain; charset=utf-8")
	w.WriteHeader(http.StatusCreated)
	io.WriteString(w, "ok")
}
