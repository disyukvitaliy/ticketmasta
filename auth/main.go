package main

import (
	"auth/logging"
	"log/slog"
	"net/http"
	"os"
	"time"

	"github.com/hibiken/asynq"
	"github.com/redis/go-redis/v9"
	"github.com/segmentio/kafka-go"

	dbpkg "auth/db"
)

func main() {
	logging.Configure()

	asynqClient := asynq.NewClient(asynq.RedisClientOpt{Addr: os.Getenv("AUTH_REDIS_ADDR")})
	defer asynqClient.Close()

	gdb, closer, err := dbpkg.Open(os.Getenv("AUTH_DB_DSN"))
	if err != nil {
		slog.Error("failed to open GORM DB", "err", err)
		os.Exit(1)
	}
	defer closer()

	redisClient := redis.NewClient(&redis.Options{
		Addr: os.Getenv("AUTH_REDIS_ADDR"),
	})

	defer redisClient.Close()

	kafkaWriter := &kafka.Writer{
		Addr:                   kafka.TCP(os.Getenv("AUTH_KAFKA_ADDR")),
		Balancer:               &kafka.Hash{},
		RequiredAcks:           kafka.RequireAll,
		BatchTimeout:           10 * time.Millisecond,
		AllowAutoTopicCreation: true,
	}
	defer kafkaWriter.Close()

	slog.Debug("GORM connected to Postgres successfully")
	slog.Debug("Starting server on :3000")

	srv := &Server{
		DB:                      gdb,
		Redis:                   redisClient,
		AsynqClient:             asynqClient,
		Events:                  &EventPublisher{Writer: kafkaWriter},
		ConfirmationSendLimiter: NewKeyedRateLimiter(time.Minute),
	}
	if err := http.ListenAndServe(":3000", newHandler(srv)); err != nil {
		slog.Error("http server error", "err", err)
	}
}
