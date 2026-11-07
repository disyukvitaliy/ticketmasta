package tasks

import (
	"auth/logging"
	"context"
	"crypto/rand"
	"encoding/base64"
	"time"

	"github.com/hibiken/asynq"
	"github.com/knadh/smtppool/v2"
)

const (
	ConfirmEmailTask = "email:confirm"
)

func NewConfirmEmailTask(email string) *asynq.Task {
	return asynq.NewTask(ConfirmEmailTask, []byte(email), asynq.Queue("critical"))
}

func (h *TaskHandler) HandleConfirmEmail(ctx context.Context, t *asynq.Task) error {
	email := string(t.Payload())

	token, err := generateToken()
	if err != nil {
		return err
	}

	if err := h.Redis.Set(ctx, "confirm:"+token, email, 24*time.Hour).Err(); err != nil {
		return err
	}

	if err := h.Mail.Send(buildConfirmEmailMsg(email, token)); err != nil {
		return err
	}

	logging.LoggerFromContext(ctx).Info("Confirmation email sent", "email", email)
	return nil
}

func buildConfirmEmailMsg(email, token string) smtppool.Email {
	return smtppool.Email{
		From:    "no-reply@example.com",
		To:      []string{email},
		Subject: "Confirm your email",
		Text:    []byte("Click here to confirm your email: http://localhost/confirmation?token=" + token),
	}
}

func generateToken() (string, error) {
	tokenBytes := make([]byte, 32)

	if _, err := rand.Read(tokenBytes); err != nil {
		return "", err
	}

	return base64.RawURLEncoding.EncodeToString(tokenBytes), nil
}
