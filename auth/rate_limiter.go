package main

import (
	"sync"
	"time"

	"golang.org/x/time/rate"
)

type rateLimitEntry struct {
	limiter  *rate.Limiter
	lastUsed time.Time
}

type KeyedRateLimiter struct {
	mu        sync.Mutex
	entries   map[string]rateLimitEntry
	interval  time.Duration
	lastClean time.Time
}

func NewKeyedRateLimiter(interval time.Duration) *KeyedRateLimiter {
	return &KeyedRateLimiter{
		entries:  make(map[string]rateLimitEntry),
		interval: interval,
	}
}

func (l *KeyedRateLimiter) Allow(key string) bool {
	now := time.Now()
	l.mu.Lock()
	defer l.mu.Unlock()

	if now.Sub(l.lastClean) >= l.interval {
		for key, entry := range l.entries {
			if now.Sub(entry.lastUsed) >= l.interval {
				delete(l.entries, key)
			}
		}
		l.lastClean = now
	}

	entry, ok := l.entries[key]
	if !ok {
		entry.limiter = rate.NewLimiter(rate.Every(l.interval), 1)
	}
	entry.lastUsed = now
	l.entries[key] = entry

	return entry.limiter.Allow()
}
