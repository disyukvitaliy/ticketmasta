package tasks

import (
	"auth/logging"
	"context"
	"errors"
	"fmt"
	"os"
	"strconv"

	"github.com/hibiken/asynq"
	"github.com/wneessen/go-mail"
)

const (
	ConfirmEmailTask = "email:confirm"
)

func NewConfirmEmailTask(email string) *asynq.Task {
	return asynq.NewTask(ConfirmEmailTask, []byte(email))
}

func HandleConfirmEmailTask(ctx context.Context, t *asynq.Task) error {
	email := string(t.Payload())

	msg, err := buildConfirmEmailMsg(email)
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

func buildConfirmEmailMsg(email string) (*mail.Msg, error) {
	msg := mail.NewMsg()
	if err := msg.From("no-reply@example.com"); err != nil {
		return nil, err
	}
	if err := msg.To(email); err != nil {
		return nil, err
	}
	msg.Subject("Confirm your email")
	msg.SetBodyString(mail.TypeTextPlain, "Click here to confirm your email: http://localhost/confirm?token=")
	return msg, nil
}

func newMailClient() (*mail.Client, error) {
	host := os.Getenv("AUTH_SMTP_HOST")
	if host == "" {
		return nil, errors.New("AUTH_SMTP_HOST is required")
	}

	port, err := strconv.Atoi(os.Getenv("AUTH_SMTP_PORT"))
	if err != nil {
		return nil, fmt.Errorf("AUTH_SMTP_PORT is invalid: %w", err)
	}

	return mail.NewClient(
		host,
		mail.WithPort(port),
		mail.WithTLSPolicy(mail.TLSOpportunistic),
	)
}
