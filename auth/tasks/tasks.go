package tasks

import (
	"github.com/redis/go-redis/v9"
	"gorm.io/gorm"
)

type TaskHandler struct {
	DB    *gorm.DB
	Redis *redis.Client
}
