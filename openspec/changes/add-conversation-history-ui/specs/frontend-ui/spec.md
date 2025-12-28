# Frontend UI - Conversation History Capability

## ADDED Requirements

### Requirement: Conversation Session Management
The system SHALL maintain multiple independent conversation sessions, with each session storing messages, metadata, and timestamps persistently across page reloads.

#### Scenario: Session persistence across reload
- **WHEN** user creates a conversation with messages
- **THEN** session is stored in localStorage with unique ID, title, and timestamp
- **AND** session persists after page reload

#### Scenario: Automatic new session on first load
- **WHEN** app loads with no existing sessions
- **THEN** system automatically creates a new blank session
- **AND** session is displayed as active in the sidebar

#### Scenario: Session switching
- **WHEN** user clicks a conversation in the sidebar
- **THEN** chat view switches to that conversation's messages
- **AND** new message input references the selected session

### Requirement: Conversation Sidebar
The system SHALL display a responsive sidebar showing all conversation sessions with metadata, allowing users to view history and switch between conversations.

#### Scenario: Sidebar displays conversation list
- **WHEN** sidebar is open
- **THEN** all sessions are displayed with:
  - Session title (creation timestamp)
  - Message count
  - Last updated time (formatted as "Today 2:30 PM", "Yesterday", or "Dec 28")

#### Scenario: Sidebar highlights current session
- **WHEN** a session is active
- **THEN** that session is highlighted in blue
- **AND** other sessions show neutral background

#### Scenario: Mobile sidebar toggle
- **WHEN** screen width is less than 768px (md breakpoint)
- **THEN** sidebar is fixed/hidden by default with -translate-x-full
- **AND** hamburger button in header toggles sidebar visibility
- **AND** overlay appears behind sidebar when open
- **AND** clicking overlay closes sidebar

#### Scenario: Desktop sidebar always visible
- **WHEN** screen width is 768px or greater (md breakpoint)
- **THEN** sidebar is always visible and relative positioned
- **AND** no overlay appears

### Requirement: New Conversation Action
The system SHALL provide clear, accessible buttons to create new conversations at multiple locations in the UI.

#### Scenario: Primary new conversation button
- **WHEN** user views the sidebar
- **THEN** a prominent "New Conversation" button is visible at the top
- **AND** clicking it creates a new blank session
- **AND** new session becomes immediately active

#### Scenario: Secondary new conversation button
- **WHEN** user scrolls through conversation history in sidebar
- **THEN** a "Start New Chat" button is visible in the footer
- **AND** clicking it creates a new blank session (same behavior as primary)

### Requirement: Auto-Scroll to Bottom
The system SHALL automatically scroll the message view to the bottom when new messages arrive, preventing messages from going off-screen.

#### Scenario: Auto-scroll on assistant response
- **WHEN** assistant message is added to chat
- **THEN** chat view automatically scrolls to bottom
- **AND** scroll uses smooth animation (behavior: smooth)
- **AND** user can manually scroll up without interruption

#### Scenario: Auto-scroll on user message
- **WHEN** user sends a message
- **THEN** chat view automatically scrolls to show the message
- **AND** scroll executes before loading indicator appears

### Requirement: Session Metadata
Each conversation session SHALL store metadata about the conversation including creation time, last update time, message count, and collection reference.

#### Scenario: Session metadata structure
- **WHEN** a session is created
- **THEN** it includes:
  - `id`: Unique UUID
  - `title`: Human-readable title (e.g., "Chat 02:30 PM")
  - `messages`: Array of Message objects
  - `createdAt`: ISO timestamp
  - `updatedAt`: ISO timestamp
  - `collectionName`: Reference to vector database collection

#### Scenario: Metadata updates on activity
- **WHEN** a message is added to a session
- **THEN** `updatedAt` timestamp is automatically updated
- **AND** sidebar displays updated "Last changed" time

## MODIFIED Requirements

### Requirement: Message Display
The chat view SHALL display messages from the currently selected session, with proper sender attribution and timestamps.

#### Scenario: Display current session messages
- **WHEN** user is viewing a conversation
- **THEN** only messages from that session are displayed
- **AND** messages maintain their original timestamps
- **AND** user messages display with "User" attribution
- **AND** assistant messages display with "Assistant" attribution

#### Scenario: Empty session state
- **WHEN** user creates a new conversation or switches to an empty session
- **THEN** chat view displays empty state message:
  - "💬 Start a conversation"
  - "Ask a question to begin"
  - "Make sure you've uploaded documents first!"

### Requirement: Chat Input
The chat input field SHALL remain available and functional, always submitting to the currently active session.

#### Scenario: Input references active session
- **WHEN** user types and submits a message
- **THEN** message is added to the currently active session
- **AND** other sessions remain unaffected
- **AND** updatedAt timestamp is updated for active session only

## REMOVED Requirements

None - all existing requirements remain, behavior changes are additive or scoped to sessions.
