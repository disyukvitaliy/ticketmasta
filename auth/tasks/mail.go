package tasks

import (
	"errors"
	"fmt"
	"os"
	"strconv"
	"time"

	"github.com/knadh/smtppool/v2"
)

func NewMailPool() (*smtppool.Pool, error) {
	host := os.Getenv("AUTH_SMTP_HOST")
	if host == "" {
		return nil, errors.New("AUTH_SMTP_HOST is required")
	}

	port, err := strconv.Atoi(os.Getenv("AUTH_SMTP_PORT"))
	if err != nil {
		return nil, fmt.Errorf("AUTH_SMTP_PORT is invalid: %w", err)
	}

	return smtppool.New(smtppool.Opt{
		Host:              host,
		Port:              port,
		MaxConns:          3,
		IdleTimeout:       30 * time.Second,
		PoolWaitTimeout:   5 * time.Second,
		MaxMessageRetries: 3,
		MessageRetryDelay: time.Second,
		SSL:               smtppool.SSLNone,
	})
}
