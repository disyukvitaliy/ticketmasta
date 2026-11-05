package main

import (
	"auth/models"
	"context"
	"encoding/json"
	"strconv"
	"time"

	"github.com/segmentio/kafka-go"
)

type EventPublisher struct {
	Writer *kafka.Writer
}

type UserEvent struct {
	Type        string     `json:"type"`
	ID          int64      `json:"id"`
	Email       string     `json:"email"`
	CreatedAt   time.Time  `json:"created_at"`
	ConfirmedAt *time.Time `json:"confirmed_at"`
}

func (p *EventPublisher) UserRegistered(ctx context.Context, user *models.User) error {
	return p.publishUserEvent(ctx, "created", user)
}

func (p *EventPublisher) UserConfirmed(ctx context.Context, user *models.User) error {
	return p.publishUserEvent(ctx, "confirmed", user)
}

func (p *EventPublisher) publishUserEvent(ctx context.Context, eventType string, user *models.User) error {
	payload, err := json.Marshal(UserEvent{
		Type:        eventType,
		ID:          user.ID,
		Email:       user.Email,
		CreatedAt:   user.CreatedAt,
		ConfirmedAt: user.ConfirmedAt,
	})
	if err != nil {
		return err
	}

	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	return p.Writer.WriteMessages(ctx, kafka.Message{
		Topic: "auth.users",
		Key:   []byte(strconv.FormatInt(user.ID, 10)),
		Value: payload,
	})
}
