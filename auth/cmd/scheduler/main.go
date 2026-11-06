package main

import (
	"auth/logging"
	"auth/tasks"
	"log/slog"
	"os"
	"time"

	"github.com/hibiken/asynq"
)

func main() {
	logging.Configure()

	scheduler := asynq.NewScheduler(
		asynq.RedisClientOpt{Addr: os.Getenv("AUTH_REDIS_ADDR")},
		&asynq.SchedulerOpts{
			Logger:   logging.AsynqLogger{},
			Location: time.UTC,
			PostEnqueueFunc: func(info *asynq.TaskInfo, err error) {
				if err != nil {
					slog.Error("could not enqueue scheduled task", "error", err)
					return
				}
				slog.Info("enqueued scheduled task", "task_id", info.ID, "task_type", info.Type, "queue", info.Queue)
			},
		},
	)
	if _, err := scheduler.Register("0 2 * * *", tasks.NewWarnUnconfirmedUsersTask()); err != nil {
		slog.Error("could not register task", "error", err)
		os.Exit(1)
	}
	if err := scheduler.Run(); err != nil {
		slog.Error("could not run scheduler", "error", err)
		os.Exit(1)
	}
}
