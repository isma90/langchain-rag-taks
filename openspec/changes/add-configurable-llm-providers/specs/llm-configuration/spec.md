# LLM Configuration - Configurable Provider Capability

## ADDED Requirements

### Requirement: Provider Configuration Options
The system SHALL support selecting different LLM providers (OpenAI, Google Gemini) independently for three pipeline stages: embeddings, metadata extraction, and Q&A generation.

#### Scenario: Configure embeddings provider
- **WHEN** EMBEDDINGS_PROVIDER is set to "openai" or "gemini"
- **THEN** embeddings service uses specified provider
- **AND** configuration is applied without code changes
- **AND** embeddings service instance created via factory

#### Scenario: Configure metadata extraction provider
- **WHEN** METADATA_PROVIDER is set to "openai" or "gemini"
- **THEN** metadata extraction uses specified provider's LLM
- **AND** metadata handler created with correct LLM instance
- **AND** no code deployment needed

#### Scenario: Configure Q&A generation provider
- **WHEN** QA_PROVIDER is set to "openai" or "gemini"
- **THEN** answer generation uses specified provider's LLM
- **AND** all prompts executed with selected LLM
- **AND** configuration applied at runtime

#### Scenario: Default providers when not specified
- **WHEN** environment variables are not set
- **THEN** system defaults to OpenAI for all stages
- **AND** system remains fully functional
- **AND** user can override at any time

### Requirement: Factory Pattern LLM Service Creation
The system SHALL implement factory functions that create appropriate LLM service instances based on configuration.

#### Scenario: Embeddings service factory
- **WHEN** create_embeddings_service() is called
- **THEN** factory reads EMBEDDINGS_PROVIDER setting
- **AND** returns OpenAI text-embedding-3-large if openai
- **AND** returns Gemini embedding-001 if gemini
- **AND** embeddings service is ready to use

#### Scenario: Metadata LLM selection
- **WHEN** MetadataHandler is initialized
- **THEN** reads METADATA_PROVIDER from settings
- **AND** creates ChatOpenAI instance if openai
- **AND** creates ChatGoogleGenerativeAI instance if gemini
- **AND** handler uses selected LLM for metadata extraction

#### Scenario: Q&A LLM selection
- **WHEN** ChainBuilder creates answer generation chain
- **THEN** reads QA_PROVIDER from settings
- **AND** creates appropriate LLM (ChatOpenAI or ChatGoogleGenerativeAI)
- **AND** LLM is bound to all prompts in chain

### Requirement: Provider Switching Without Code Changes
Changing LLM providers SHALL require only environment variable changes and container restart.

#### Scenario: Switch providers via environment variables
- **WHEN** environment variables are updated in .env or docker-compose.yml:
  - EMBEDDINGS_PROVIDER=gemini
  - METADATA_PROVIDER=gemini
  - QA_PROVIDER=openai
- **THEN** container is rebuilt: `podman-compose build && podman-compose up -d`
- **AND** system uses new provider configuration
- **AND** no code changes necessary

#### Scenario: Cost optimization without code
- **WHEN** switching to all-Gemini configuration for cost savings
- **THEN** environment variables are updated
- **AND** container restarted
- **AND** system operates identically with 70% lower costs
- **AND** no code deployment required

## MODIFIED Requirements

### Requirement: Embeddings Generation
The system SHALL generate embeddings using configured provider, supporting both OpenAI and Google Gemini.

#### Scenario: Generate embeddings with OpenAI
- **WHEN** embeddings are needed and EMBEDDINGS_PROVIDER=openai
- **THEN** text-embedding-3-large model is used
- **AND** embeddings are 3072-dimensional (reduced to 512)
- **AND** high quality embeddings for semantic search

#### Scenario: Generate embeddings with Gemini
- **WHEN** embeddings are needed and EMBEDDINGS_PROVIDER=gemini
- **THEN** Gemini embedding-001 model is used
- **AND** embeddings are 768-dimensional
- **AND** faster generation, lower cost

### Requirement: Metadata Extraction
The system SHALL extract metadata using configured LLM provider.

#### Scenario: Extract metadata with OpenAI
- **WHEN** METADATA_PROVIDER=openai
- **THEN** ChatOpenAI is used for metadata extraction prompts
- **AND** high-quality metadata generation

#### Scenario: Extract metadata with Gemini
- **WHEN** METADATA_PROVIDER=gemini
- **THEN** ChatGoogleGenerativeAI is used
- **AND** lower cost metadata generation

### Requirement: Answer Generation
The system SHALL generate answers using configured LLM provider with maintained prompt quality.

#### Scenario: Generate answers with OpenAI
- **WHEN** QA_PROVIDER=openai
- **THEN** gpt-4o or gpt-4o-mini is used
- **AND** high-quality answers

#### Scenario: Generate answers with Gemini
- **WHEN** QA_PROVIDER=gemini
- **THEN** gemini-2.5-flash or gemini-2.0-flash is used
- **AND** good quality answers with lower cost

## REMOVED Requirements

None - all existing requirements remain, provider flexibility is purely additive.
