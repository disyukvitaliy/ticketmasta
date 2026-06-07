package db

import (
	"log"
	"log/slog"
	"os"
	"time"

	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
)

// DB is a thin wrapper around *gorm.DB so we can evolve internals without touching handlers.
type DB struct {
	Gorm *gorm.DB
}

// Open initializes a GORM connection to Postgres using the provided DSN.
// It returns a wrapper DB, a closer to be called on shutdown, and an error if connection fails.
func Open(dsn string) (*DB, func(), error) {
	logLevel := logger.Info
	if os.Getenv("LOG_LEVEL") == "silent" {
		logLevel = logger.Silent
	}

	// Configure a lightweight logger for dev.
	newLogger := logger.New(
		log.New(os.Stdout, "gorm: ", log.LstdFlags|log.Lmsgprefix),
		logger.Config{
			SlowThreshold:             200 * time.Millisecond,
			LogLevel:                  logLevel,
			IgnoreRecordNotFoundError: true,
			ParameterizedQueries:      true,
			Colorful:                  true,
		},
	)

	gdb, err := gorm.Open(postgres.Open(dsn), &gorm.Config{Logger: newLogger, TranslateError: true})
	if err != nil {
		return nil, nil, err
	}

	// Tune the underlying sql.DB pool.
	sqlDB, err := gdb.DB()
	if err != nil {
		return nil, nil, err
	}
	sqlDB.SetMaxOpenConns(5)
	sqlDB.SetMaxIdleConns(5)
	sqlDB.SetConnMaxLifetime(30 * time.Minute)

	closer := func() {
		if err := sqlDB.Close(); err != nil {
			slog.Error("failed to close GORM DB", "err", err)
		}
	}

	return &DB{Gorm: gdb}, closer, nil
}
