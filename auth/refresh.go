package main

import (
	"auth/models"
	"errors"
	"io"
	"net/http"

	"gorm.io/gorm"
)

func (s *Server) Refresh(w http.ResponseWriter, r *http.Request) {
	refreshTokenBytes, err := io.ReadAll(r.Body)
	if err != nil {
		http.Error(w, "could not read body", http.StatusBadRequest)
		return
	}

	var refreshToken models.RefreshToken
	err = s.DB.
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
	io.WriteString(w, tokenString)
}
