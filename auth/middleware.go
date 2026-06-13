package main

import (
	"auth/logging"
	"context"
	"fmt"
	"log/slog"
	"net/http"
	"time"
)

type statusResponseWriter struct {
	http.ResponseWriter
	status int
}

func (w *statusResponseWriter) WriteHeader(status int) {
	w.status = status
	w.ResponseWriter.WriteHeader(status)
}

func requestIDMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		rid := r.Header.Get("X-Request-ID")
		if rid == "" {
			rid = fmt.Sprintf("%d", time.Now().UnixNano())
		}
		w.Header().Set("X-Request-ID", rid)
		ctx := context.WithValue(r.Context(), "request_id", rid)
		r = r.WithContext(ctx)
		next.ServeHTTP(w, r)
	})
}

func loggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		rid, _ := r.Context().Value("request_id").(string)
		logger := slog.Default().With("req_id", rid)
		sw := &statusResponseWriter{ResponseWriter: w, status: http.StatusOK}
		ctx := logging.WithLogger(r.Context(), logger)
		logger.Info("request started", "method", r.Method, "url", r.URL.String())
		start := time.Now()
		next.ServeHTTP(sw, r.WithContext(ctx))
		logger.Info("request completed", "status", sw.status, "took", time.Since(start))
	})
}
