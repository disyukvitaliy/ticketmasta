package logging

import (
	"fmt"
	"log/slog"
	"os"
)

// AsynqLogger adapts slog to Asynq's variadic logging interface.
type AsynqLogger struct{}

func (AsynqLogger) Debug(args ...any) {
	slog.Debug(fmt.Sprint(args...))
}

func (AsynqLogger) Info(args ...any) {
	slog.Info(fmt.Sprint(args...))
}

func (AsynqLogger) Warn(args ...any) {
	slog.Warn(fmt.Sprint(args...))
}

func (AsynqLogger) Error(args ...any) {
	slog.Error(fmt.Sprint(args...))
}

func (AsynqLogger) Fatal(args ...any) {
	slog.Error(fmt.Sprint(args...))
	os.Exit(1)
}
