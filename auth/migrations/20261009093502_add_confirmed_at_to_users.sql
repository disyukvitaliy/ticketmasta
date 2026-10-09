-- +goose Up
-- +goose StatementBegin
ALTER TABLE users ADD COLUMN confirmed_at TIMESTAMPTZ;
-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin
ALTER TABLE users DROP COLUMN confirmed_at;
-- +goose StatementEnd
