package models

import "time"

// RefreshToken represents a persisted refresh token (one row per session/device).
type RefreshToken struct {
	ID         int64      `gorm:"column:id;primaryKey;autoIncrement"`
	UserID     int64      `gorm:"column:user_id;not null"`
	TokenHash  string     `gorm:"column:token_hash;not null;unique"`
	ExpiresAt  time.Time  `gorm:"column:expires_at;not null"`
	RevokedAt  *time.Time `gorm:"column:revoked_at"`
	CreatedAt  time.Time  `gorm:"column:created_at;autoCreateTime"`

	// Optional relation to the user
	User *User `gorm:"foreignKey:UserID;references:ID"`
}

// TableName sets the table name for the RefreshToken model.
func (RefreshToken) TableName() string { return "refresh_tokens" }
