package main

import (
	"auth/models"
	"io"
	"net/http"
	"time"
)

func (s *Server) Logout(w http.ResponseWriter, r *http.Request) {
	refreshTokenBytes, err := io.ReadAll(r.Body)
	if err != nil {
		http.Error(w, "could not read body", http.StatusBadRequest)
		return
	}

	err = s.DB.Model(&models.RefreshToken{}).
		Where("token_hash = ?", hashToken(refreshTokenBytes)).
		Update("revoked_at", time.Now()).Error

	if err != nil {
		http.Error(w, "could not revoke token", http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusNoContent)
}
