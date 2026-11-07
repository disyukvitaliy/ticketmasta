package tasks

import (
	"auth/logging"
	"auth/models"
	"context"
	"time"

	"github.com/hibiken/asynq"
	"github.com/knadh/smtppool/v2"
	"golang.org/x/sync/errgroup"
)

const WarnUnconfirmedUsersTask = "users:warn_unconfirmed"

func NewWarnUnconfirmedUsersTask() *asynq.Task {
	return asynq.NewTask(WarnUnconfirmedUsersTask, nil, asynq.Queue("low"))
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

	logger := logging.LoggerFromContext(ctx)
	var workers errgroup.Group
	workers.SetLimit(3)

	for _, user := range users {
		workers.Go(func() error {
			if err := h.Mail.Send(buildWarningEmailMsg(user.Email)); err != nil {
				logger.Error("Could not send account deletion warning email", "error", err, "user_id", user.ID)
			}
			return nil
		})
	}
	return workers.Wait()
}

func buildWarningEmailMsg(email string) smtppool.Email {
	return smtppool.Email{
		From:    "no-reply@example.com",
		To:      []string{email},
		Subject: "We will destroy you",
		Text:    []byte("Hello! Your account is still awaiting confirmation and will be deleted in one month. We’d love for you to stay.\n\nPlease confirm your account. Or else."),
	}
}
