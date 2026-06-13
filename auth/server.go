package main

import (
	"github.com/hibiken/asynq"
	"gorm.io/gorm"
)

type TaskClient interface {
	Enqueue(task *asynq.Task, opts ...asynq.Option) (*asynq.TaskInfo, error)
}

type Server struct {
	DB          *gorm.DB
	AsynqClient TaskClient
}
