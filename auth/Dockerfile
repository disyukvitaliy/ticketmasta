FROM golang:1.26.4
WORKDIR /app

# Install goose CLI in the image for running migrations from the container
RUN go install github.com/pressly/goose/v3/cmd/goose@v3.20.0

COPY go.mod go.sum ./
RUN go mod download
