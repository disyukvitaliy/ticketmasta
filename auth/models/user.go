package models

import "time"

// User represents an account in the auth service.
// It is mapped to the existing "users" table managed by goose migrations.

type User struct {
	ID           int64      `gorm:"column:id;primaryKey;autoIncrement"`
	Email        string     `gorm:"column:email;uniqueIndex;not null"`
	PasswordHash string     `gorm:"column:password_hash;not null"`
	Role         string     `gorm:"column:role;not null;default:user"`
	ConfirmedAt  *time.Time `gorm:"column:confirmed_at"`
	CreatedAt    time.Time  `gorm:"column:created_at;autoCreateTime"`
	UpdatedAt    time.Time  `gorm:"column:updated_at;autoUpdateTime"`
}

// TableName sets the table name for the User model.
func (User) TableName() string { return "users" }
