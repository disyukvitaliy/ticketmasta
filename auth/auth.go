package main

import (
    "encoding/json"
    "errors"
    "log"
    "net/http"
    "os"
    "time"

    "github.com/golang-jwt/jwt/v4"
    "gorm.io/gorm"

    dbpkg "auth/db"
    "auth/models"
)

func getenv(key string, fallback ...string) string {
    if v := os.Getenv(key); v != "" {
        return v
    }
    if len(fallback) > 0 {
        log.Printf("%s not set; using default dev value", key)
        return fallback[0]
    }
    return ""
}

var secretKey = []byte(getenv("AUTH_JWT_SECRET", "your-very-secret-key"))

// Server holds shared dependencies for handlers (to be used later as logic is added).
type Server struct {
    DB *dbpkg.DB // wrapper with underlying *gorm.DB; not used yet
}

type LoginRequest struct {
    Email string `json:"email"`
}

func (s *Server) Login(w http.ResponseWriter, r *http.Request) {

    var req LoginRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, "bad json", http.StatusBadRequest)
        return
    }
    email := req.Email

    if email == "" {
        http.Error(w, "email is required", http.StatusBadRequest)
        return
    }

    // Look up the user by email
    var u models.User
    err := s.DB.Gorm.Where("email = ?", email).First(&u).Error
    if err != nil {
        if errors.Is(err, gorm.ErrRecordNotFound) {
            http.Error(w, "invalid credentials", http.StatusUnauthorized)
            return
        }
        http.Error(w, "db error", http.StatusInternalServerError)
        return
    }

    // Issue JWT using user fields
    token := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
        "id":    u.ID,
        "email": u.Email,
        "role":  u.Role,
        "exp":   time.Now().Add(time.Hour).Unix(),
        "iss":   "ticketmasta-auth",
    })

    tokenString, err := token.SignedString(secretKey)
    if err != nil {
        http.Error(w, "could not create token", http.StatusInternalServerError)
        return
    }

    // For backward-compat with the current frontend, return plain text token
    w.Header().Set("Content-Type", "text/plain; charset=utf-8")
    _, _ = w.Write([]byte(tokenString))
}

func loggingMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        log.Printf("%s %s %s", r.RemoteAddr, r.Method, r.URL)
        next.ServeHTTP(w, r)
    })
}

func main() {
    // Initialize GORM connection (no business logic yet)
    dsn := getenv("AUTH_DB_DSN")
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

    mux := http.NewServeMux()
    // Login uses JSON body {"email": "..."} via POST
    mux.HandleFunc("POST /login", srv.Login)

    loggedMux := loggingMiddleware(mux)

    log.Println("Starting server on :3000")
    if err := http.ListenAndServe(":3000", loggedMux); err != nil {
        log.Fatalf("http server error: %v", err)
    }
}
