package main

import (
	"auth/logging"
	"auth/models"
	"errors"
	"io"
	"net/http"
	"time"

	"github.com/redis/go-redis/v9"
)

func (s *Server) Confirm(w http.ResponseWriter, r *http.Request) {
	logger := logging.LoggerFromContext(r.Context())
	confirmationTokenBytes, err := io.ReadAll(r.Body)
	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		logger.Warn("Failed to read confirmation token", "error", err)
		return
	}

	confirmationToken := string(confirmationTokenBytes)

	email, err := s.Redis.Get(r.Context(), "confirm:"+confirmationToken).Result()

	if errors.Is(err, redis.Nil) {
		http.NotFound(w, r)
		logger.Warn("Token not found", "token", confirmationToken)
		return
	}

	result := s.DB.
		Model(&models.User{}).
		Where("email = ?", email).
		Where("confirmed_at IS NULL").
		Update("confirmed_at", time.Now())

	if result.Error != nil {
		w.WriteHeader(http.StatusInternalServerError)
		return
	}

	if result.RowsAffected == 0 {
		http.NotFound(w, r)
		return
	}

	s.Redis.Del(r.Context(), "confirm:"+confirmationToken)
	w.WriteHeader(http.StatusNoContent)
}
