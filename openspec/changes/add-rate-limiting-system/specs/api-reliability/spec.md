# API Reliability - Rate Limiting Capability

## ADDED Requirements

### Requirement: Request Rate Limiting
The system SHALL enforce a configurable maximum requests per minute (RPM) limit using a sliding window algorithm to prevent API quota violations.

#### Scenario: Request allowed under limit
- **WHEN** current request rate is below configured maximum
- **THEN** request proceeds immediately
- **AND** no additional delay is imposed
- **AND** request is counted in the current window

#### Scenario: Request delayed at limit
- **WHEN** request rate reaches maximum RPM
- **THEN** request is delayed until oldest request in window expires
- **AND** delay time = (time remaining for oldest request) + small jitter
- **AND** request then proceeds normally
- **AND** request is counted in window

#### Scenario: Sliding window removes old requests
- **WHEN** time passes in the 60-second window
- **THEN** requests older than 60 seconds are automatically removed
- **AND** this frees capacity for new requests
- **AND** window slides automatically without manual intervention

#### Scenario: Configuration via environment variable
- **WHEN** application starts
- **THEN** rate limit is read from RATE_LIMIT_RPM environment variable
- **AND** default is 10 RPM if not specified
- **AND** configuration applies to all requests globally

### Requirement: Rate Limit Monitoring
The system SHALL provide `/rate-limit-stats` endpoint to monitor current rate limiting status and per-service request counts.

#### Scenario: Global rate limiting stats
- **WHEN** client calls `/rate-limit-stats`
- **THEN** response includes:
  - `current_rpm`: Current requests in last minute
  - `max_rpm`: Configured maximum
  - `utilization_percent`: Current usage as percentage
  - `min_delay_seconds`: Minimum delay if limit reached

#### Scenario: Per-service request tracking
- **WHEN** stats endpoint is called
- **THEN** response includes breakdown by service:
  - OpenAI embeddings requests
  - Metadata extraction requests
  - Chain builder requests
  - Other identified services

#### Scenario: Real-time utilization visibility
- **WHEN** monitoring rate limit status
- **THEN** client can see:
  - How many requests in current minute
  - How much headroom remains
  - Estimated time to next available slot if waiting

### Requirement: Automatic Throttling
The system SHALL automatically apply delays when approaching rate limits, distributing traffic evenly without requiring client retry logic.

#### Scenario: Transparent delay application
- **WHEN** rate limit is approached
- **THEN** request is held in middleware
- **AND** delay is calculated based on window
- **AND** client is blocked transparently (time.sleep)
- **AND** request completes normally after delay

#### Scenario: Jitter prevents thundering herd
- **WHEN** multiple requests hit rate limit simultaneously
- **THEN** small random jitter is added to delay
- **AND** prevents synchronized retry storms
- **AND** spreads load evenly

## MODIFIED Requirements

### Requirement: API Endpoint Processing
All API endpoints SHALL be subject to rate limiting middleware, enforcing request limits transparently.

#### Scenario: Rate limiting applies to all endpoints
- **WHEN** any API endpoint is called
- **THEN** request passes through rate limiting middleware
- **AND** middleware may delay request if at limit
- **AND** request processes normally after any delay
- **AND** rate limit counts for all services aggregated globally

#### Scenario: Question answering with rate limiting
- **WHEN** `/question` endpoint is called
- **THEN** request may be delayed by rate limiter
- **AND** OpenAI API calls within endpoint are tracked
- **AND** next request is throttled accordingly

## REMOVED Requirements

None - all existing requirements remain, rate limiting is transparent and purely additive.
