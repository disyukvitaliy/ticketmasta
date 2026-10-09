package main

import "net/http"

func newHandler(srv *Server) http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("POST /login", srv.Login)
	mux.HandleFunc("POST /logout", srv.Logout)
	mux.HandleFunc("POST /register", srv.Register)
	mux.HandleFunc("POST /confirmation", srv.Confirm)
	mux.HandleFunc("POST /refresh", srv.Refresh)

	return requestIDMiddleware(loggingMiddleware(mux))
}
