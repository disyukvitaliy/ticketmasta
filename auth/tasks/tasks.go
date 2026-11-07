package tasks

import (
	"github.com/knadh/smtppool/v2"
	"github.com/redis/go-redis/v9"
	"gorm.io/gorm"
)

type Mailer interface {
	Send(smtppool.Email) error
}

type TaskHandler struct {
	DB    *gorm.DB
	Redis *redis.Client
	Mail  Mailer
}
