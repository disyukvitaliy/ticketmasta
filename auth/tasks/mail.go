package tasks

import (
	"errors"
	"fmt"
	"os"
	"strconv"

	"github.com/wneessen/go-mail"
)

func newMailClient() (*mail.Client, error) {
	host := os.Getenv("AUTH_SMTP_HOST")
	if host == "" {
		return nil, errors.New("AUTH_SMTP_HOST is required")
	}

	port, err := strconv.Atoi(os.Getenv("AUTH_SMTP_PORT"))
	if err != nil {
		return nil, fmt.Errorf("AUTH_SMTP_PORT is invalid: %w", err)
	}

	return mail.NewClient(
		host,
		mail.WithPort(port),
		mail.WithTLSPolicy(mail.TLSOpportunistic),
	)
}
