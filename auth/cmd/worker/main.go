package main

import (
	"auth/logging"
	"auth/tasks"
	"context"
	"log/slog"
	"os"

	"github.com/hibiken/asynq"
)

func main() {
	logging.Configure()

	srv := asynq.NewServer(
		asynq.RedisClientOpt{Addr: os.Getenv("AUTH_REDIS_ADDR")},
		asynq.Config{
			Concurrency: 2,
			Queues: map[string]int{
				"critical": 6,
				"default":  3,
				"low":      1,
			},
		},
	)

	mux := asynq.NewServeMux()
	mux.Use(taskLoggerMiddleware)
	mux.HandleFunc(tasks.ConfirmEmailTask, tasks.HandleConfirmEmailTask)

	if err := srv.Run(mux); err != nil {
		slog.Error("could not run server", "error", err)
	}
}

func taskLoggerMiddleware(next asynq.Handler) asynq.Handler {
	return asynq.HandlerFunc(func(ctx context.Context, t *asynq.Task) error {
		taskID, _ := asynq.GetTaskID(ctx)
		logger := slog.Default().With("task_id", taskID)
		logger.Info("task started", "task_type", t.Type())

		return next.ProcessTask(logging.WithLogger(ctx, logger), t)
	})
}
