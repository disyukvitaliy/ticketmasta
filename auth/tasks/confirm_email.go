package tasks

import (
	"auth/logging"
	"context"
	"crypto/rand"
	"encoding/base64"
	"time"

	"github.com/hibiken/asynq"
	"github.com/wneessen/go-mail"
)

const (
	ConfirmEmailTask = "email:confirm"
)

func NewConfirmEmailTask(email string) *asynq.Task {
	return asynq.NewTask(ConfirmEmailTask, []byte(email))
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

	msg, err := buildConfirmEmailMsg(email, token)
	if err != nil {
		return err
	}

	client, err := newMailClient()
	if err != nil {
		return err
	}

	if err := client.DialAndSendWithContext(ctx, msg); err != nil {
		return err
	}

	logging.LoggerFromContext(ctx).Info("Confirmation email sent", "email", email)
	return nil
}

func buildConfirmEmailMsg(email, token string) (*mail.Msg, error) {
	msg := mail.NewMsg()
	if err := msg.From("no-reply@example.com"); err != nil {
		return nil, err
	}
	if err := msg.To(email); err != nil {
		return nil, err
	}
	msg.Subject("Confirm your email")
	msg.SetBodyString(mail.TypeTextPlain, "Click here to confirm your email: http://localhost/confirmation?token="+token)
	return msg, nil
}

func generateToken() (string, error) {
	tokenBytes := make([]byte, 32)

	if _, err := rand.Read(tokenBytes); err != nil {
		return "", err
	}

	return base64.RawURLEncoding.EncodeToString(tokenBytes), nil
}
