package tasks

import (
	"auth/logging"
	"context"

	"github.com/hibiken/asynq"
)

const (
	ConfirmEmailTask = "email:confirm"
)

func NewConfirmEmailTask(email string) *asynq.Task {
	return asynq.NewTask(ConfirmEmailTask, []byte(email))
}

func HandleConfirmEmailTask(ctx context.Context, t *asynq.Task) error {
	email := string(t.Payload())
	logging.LoggerFromContext(ctx).Info("Confirmation email sent", "email", email)
	return nil
}
