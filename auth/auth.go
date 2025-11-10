package main

import (
    "github.com/golang-jwt/jwt/v4"
    "log"
    "net/http"
    "os"
    "time"
)

func getenv(key, fallback string) string {
    if v := os.Getenv(key); v != "" {
        return v
    }
    log.Printf("%s not set; using default dev value", key)
    return fallback
}

var secretKey = []byte(getenv("AUTH_JWT_SECRET", "your-very-secret-key"))

func login(w http.ResponseWriter, r *http.Request) {
    token := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
        "id":    1,
        "email": "example@mail.com",
        "role":  "admin",
        "exp":   time.Now().Add(time.Hour).Unix(),
        "iss":   "example_issuer",
    })

    tokenString, err := token.SignedString(secretKey)
    if err != nil {
        http.Error(w, "Could not create token", http.StatusInternalServerError)
        return
    }

    w.Write([]byte(tokenString))
}

func loggingMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        log.Printf("%s %s %s", r.RemoteAddr, r.Method, r.URL)
        next.ServeHTTP(w, r)
    })
}

func main() {
    mux := http.NewServeMux()
    mux.HandleFunc("/login", login)

    loggedMux := loggingMiddleware(mux)

    log.Println("Starting server on :3000")
    http.ListenAndServe(":3000", loggedMux)
}
