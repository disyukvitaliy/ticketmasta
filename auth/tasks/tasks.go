package tasks

import (
	"auth/logging"
	"context"
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

	msg := mail.NewMsg()
	if err := msg.From("no-reply@example.com"); err != nil {
		return err
	}
	if err := msg.To(email); err != nil {
		return err
	}
	msg.Subject("Confirm your email")
	msg.SetBodyString(mail.TypeTextPlain, "Click here to confirm your email: http://localhost/confirm?token=")

	port, err := strconv.Atoi(os.Getenv("AUTH_SMTP_PORT"))
	if err != nil {
		return err
	}

	client, err := mail.NewClient(
		os.Getenv("AUTH_SMTP_HOST"),
		mail.WithPort(port),
		mail.WithTLSPolicy(mail.TLSOpportunistic),
	)
	if err != nil {
		return err
	}

	if err := client.DialAndSendWithContext(ctx, msg); err != nil {
		return err
	}

	logging.LoggerFromContext(ctx).Info("Confirmation email sent", "email", email)
	return nil
}
