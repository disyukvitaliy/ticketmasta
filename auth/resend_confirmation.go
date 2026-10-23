package main

import (
	"auth/logging"
	"auth/models"
	"auth/tasks"
	"io"
	"net/http"
	"strings"
)

func (s *Server) ResendConfirmation(w http.ResponseWriter, r *http.Request) {
	logger := logging.LoggerFromContext(r.Context())
	emailBytes, err := io.ReadAll(r.Body)
	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		logger.Warn("Failed to read email", "error", err)
		return
	}

	email := strings.TrimSpace(strings.ToLower(string(emailBytes)))

	var count int64
	err = s.DB.Model(&models.User{}).Where("confirmed_at IS NULL AND email = ?", email).Count(&count).Error
	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		return
	}
	if count == 0 {
		logger.Warn("no unconfirmed user found for confirmation resend")
		w.WriteHeader(http.StatusAccepted)
		return
	}

	if err := s.enqueueTask(r.Context(), tasks.NewConfirmEmailTask(email)); err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusAccepted)
}
