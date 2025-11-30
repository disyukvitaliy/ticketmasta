package main

import (
    "crypto/rand"
    "crypto/sha256"
    "encoding/base64"
    "encoding/hex"
    "auth/models"
    "time"
    "os"

    "github.com/golang-jwt/jwt/v4"
)

func generateJWT(u *models.User) (string, error) {
    token := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
        "id":    u.ID,
        "email": u.Email,
        "role":  u.Role,
        "exp":   time.Now().Add(time.Hour).Unix(),
        "iss":   "ticketmasta-auth",
    })

    return token.SignedString([]byte(os.Getenv("AUTH_JWT_SECRET")))
}

func generateToken() (token string, hash string) {
    tokenBytes := make([]byte, 32)
    rand.Read(tokenBytes)

    tokenString := base64.RawURLEncoding.EncodeToString(tokenBytes)

    return tokenString, hashToken(tokenString)
}

func hashToken(token string) (hash string) {
    tokenSum := sha256.Sum256([]byte(token))
    return hex.EncodeToString(tokenSum[:])
}