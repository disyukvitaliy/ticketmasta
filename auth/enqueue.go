package main

import (
	"auth/logging"
	"context"

	"github.com/hibiken/asynq"
)

func (s *Server) enqueueTask(ctx context.Context, task *asynq.Task, opts ...asynq.Option) error {
	logger := logging.LoggerFromContext(ctx)
	info, err := s.AsynqClient.Enqueue(task, opts...)
	if err != nil {
		logger.Error("could not enqueue task", "error", err)
		return err
	}

	logger.Info("enqueued task", "id", info.ID, "queue", info.Queue)
	return nil
}
