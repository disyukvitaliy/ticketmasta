package main

import (
	"auth/logging"
	"auth/models"
	"errors"
	"io"
	"net/http"
	"time"

	"github.com/redis/go-redis/v9"
	"gorm.io/gorm/clause"
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

	var user models.User
	result := s.DB.
		Model(&user).
		Clauses(clause.Returning{}).
		Where("email = ?", email).
		Where("confirmed_at IS NULL").
		Update("confirmed_at", time.Now())

	if result.Error != nil {
		w.WriteHeader(http.StatusInternalServerError)
		return
	}

	if result.RowsAffected == 0 {
		logger.Warn("no unconfirmed user found")
		http.NotFound(w, r)
		return
	}

	s.Redis.Del(r.Context(), "confirm:"+confirmationToken)

	if err := s.Events.UserConfirmed(r.Context(), &user); err != nil {
		logger.Error("could not publish user confirmation", "user_id", user.ID, "error", err)
	}

	w.WriteHeader(http.StatusNoContent)
}
