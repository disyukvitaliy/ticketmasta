package main

import (
	"testing"
	"time"
)

func TestKeyedRateLimiterAllowsOncePerIntervalAndKey(t *testing.T) {
	limiter := NewKeyedRateLimiter(50 * time.Millisecond)

	if !limiter.Allow("one@example.com") {
		t.Fatal("first request should be allowed")
	}
	if limiter.Allow("one@example.com") {
		t.Fatal("second request for the same email should be limited")
	}
	if !limiter.Allow("two@example.com") {
		t.Fatal("a different email should have its own limit")
	}

	time.Sleep(60 * time.Millisecond)
	if !limiter.Allow("one@example.com") {
		t.Fatal("request should be allowed after the interval")
	}
}
