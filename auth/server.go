package main

import (
	"auth/models"
	"context"

	"github.com/hibiken/asynq"
	"github.com/redis/go-redis/v9"
	"gorm.io/gorm"
)

type TaskClient interface {
	Enqueue(task *asynq.Task, opts ...asynq.Option) (*asynq.TaskInfo, error)
}

type UserEventPublisher interface {
	UserRegistered(ctx context.Context, user *models.User) error
	UserConfirmed(ctx context.Context, user *models.User) error
}

type Server struct {
	DB                      *gorm.DB
	Redis                   *redis.Client
	AsynqClient             TaskClient
	Events                  UserEventPublisher
	ConfirmationSendLimiter *KeyedRateLimiter
}
