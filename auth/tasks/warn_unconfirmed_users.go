package tasks

import (
	"auth/logging"
	"auth/models"
	"context"
	"time"

	"github.com/hibiken/asynq"
	"github.com/wneessen/go-mail"
)

const WarnUnconfirmedUsersTask = "users:warn_unconfirmed"

func NewWarnUnconfirmedUsersTask() *asynq.Task {
	return asynq.NewTask(WarnUnconfirmedUsersTask, nil)
}

func (h *TaskHandler) HandleWarnUnconfirmedUsers(ctx context.Context, t *asynq.Task) error {
	now := time.Now().UTC()
	today := time.Date(now.Year(), now.Month(), now.Day(), 0, 0, 0, 0, time.UTC)
	yesterday := today.AddDate(0, 0, -1)
	start := yesterday.AddDate(0, -5, 0)
	end := today.AddDate(0, -5, 0)
	var users []models.User
	// Load all matching users without batching for simplicity.
	if err := h.DB.WithContext(ctx).
		Where("confirmed_at IS NULL").
		Where("created_at >= ? AND created_at < ?", start, end).
		Find(&users).Error; err != nil {
		return err
	}

	client, err := newMailClient()
	if err != nil {
		return err
	}

	if err := client.DialWithContext(ctx); err != nil {
		return err
	}

	defer client.Close()

	logger := logging.LoggerFromContext(ctx)

	for _, user := range users {
		if err := sendWarningEmail(client, user.Email); err != nil {
			logger.Error("Could not send account deletion warning email", "error", err, "user_id", user.ID)
		}
	}

	return nil
}

func sendWarningEmail(client *mail.Client, email string) error {
	msg, err := buildWarningEmailMsg(email)
	if err != nil {
		return err
	}
	return client.Send(msg)
}

func buildWarningEmailMsg(email string) (*mail.Msg, error) {
	msg := mail.NewMsg()
	if err := msg.From("no-reply@example.com"); err != nil {
		return nil, err
	}
	if err := msg.To(email); err != nil {
		return nil, err
	}
	msg.Subject("We will destroy you")
	msg.SetBodyString(mail.TypeTextPlain, "Hello! Your account is still awaiting confirmation and will be deleted in one month. We’d love for you to stay.\n\nPlease confirm your account. Or else.")
	return msg, nil
}
