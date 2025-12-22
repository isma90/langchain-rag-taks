# OpenSpec - RAG Project Specifications

Esta carpeta contiene las especificaciones formales del proyecto RAG siguiendo la metodología OpenSpec.

## Estructura

```
openspec/
├── project.md                    # Contexto general del proyecto
├── AGENTS.md                     # Guías para asistentes IA (Claude)
├── README.md                     # Este archivo
└── changes/                      # Especificaciones de cambios/fases
    ├── phase-1-foundation/       # Foundation & Infrastructure
    ├── phase-2-chunking/         # Text Chunking Implementation
    ├── phase-3-vector-store/     # Vector Store & Indexing (Qdrant)
    ├── phase-4-rag-pipeline/     # Basic RAG Pipeline
    └── phase-5-deployment/       # Containerization & Deployment
```

## Documentos Principales

### 1. project.md
Define el propósito, tech stack, convenciones y contexto general del proyecto.

**Contiene**:
- Propósito y objetivos principales
- Tech stack completo (Backend, DevOps, Frontend, Infraestructura)
- Convenciones de código (naming, type hints, docstrings)
- Patrones arquitectónicos utilizados
- Estructura de directorios
- Constraints técnicos y de performance
- Dependencias externas

### 2. AGENTS.md
Guías e instrucciones para asistentes IA (Claude Code).

**Contiene**:
- Workflow de 3 etapas para crear/implementar/aplicar cambios
- Patrones específicos del proyecto
- Convenciones de comunicación
- Mejores prácticas

### 3. changes/*/proposal.md & spec.md
Especificaciones formales para cada fase del proyecto.

**Cada fase tiene**:
- `proposal.md` - Resumen del cambio (propuesta)
  - Problema que resuelve
  - Solución propuesta
  - Criterios de éxito
  - Dependencias
  - Fases relacionadas

- `spec.md` - Especificación detallada
  - ADDED/MODIFIED/REMOVED Requirements
  - Scenarios (casos de uso concretos)
  - Métodos y especificaciones
  - Architecture & Patterns
  - Integration Points
  - Testing status
  - Status del cambio

## Fases Documentadas

### Phase 1: Foundation & Infrastructure ✅
Logging, configuration management, utilities, resilience patterns, token counting.

**Files**: `phase-1-foundation/{proposal,spec}.md`

### Phase 2: Text Chunking ✅
4 estrategias de chunking (recursive, semantic, markdown, HTML) con token-based sizing.

**Files**: `phase-2-chunking/{proposal,spec}.md`

### Phase 3: Vector Store & Indexing ✅
Integración con Qdrant Cloud, metadata enrichment, embeddings, 4 retrieval strategies.

**Files**: `phase-3-vector-store/{proposal,spec}.md`

### Phase 4: Basic RAG Pipeline ✅
LCEL chains, 4 tipos de prompts, RAGService, métricas de performance.

**Files**: `phase-4-rag-pipeline/{proposal,spec}.md`

### Phase 5: Containerization & Deployment ✅
Docker multi-stage, docker-compose, FastAPI REST API, scripts de deployment.

**Files**: `phase-5-deployment/{proposal,spec}.md`

## Cómo Usar

### Leer Especificaciones
1. Comienza con `project.md` para contexto general
2. Lee `AGENTS.md` para entender el workflow
3. Explora `changes/phase-X/proposal.md` para resumen de cada fase
4. Lee `changes/phase-X/spec.md` para detalles completos

### Validar Especificaciones
```bash
# Validar una fase específica
openspec validate phase-1-foundation --strict

# Listar todas las fases
openspec list

# Ver especificaciones con detalles
openspec list --specs
```

### Entender la Arquitectura
La arquitectura se documenta en cada spec.md:
1. Lee "Architecture & Patterns" para patrones usados
2. Lee "Integration Points" para ver cómo interactúan las fases
3. Lee "Dependencies" para entender dependencias externas

## Convenciones

### Nombres de Cambios (Change IDs)
Formato: `kebab-case` con verbo al inicio
- `phase-1-foundation` - Foundation phase
- `phase-2-chunking` - Chunking phase
- `add-feature-name` - Para nuevas características
- `update-feature-name` - Para mejoras
- `fix-issue-name` - Para fixes
- `refactor-component-name` - Para refactoring

### Estructura de Requirements
Cada spec.md usa:
- `## ADDED Requirements` - Nuevas capacidades
- `## MODIFIED Requirements` - Cambios a existentes
- `## REMOVED Requirements` - Características eliminadas
- `#### Scenario:` - Casos de uso concretos

### Archivos por Cambio
```
changes/<change-id>/
├── proposal.md       # Propuesta (resumen)
├── spec.md          # Especificación detallada
├── design.md        # Opcional: Diseño técnico detallado
└── tasks.md         # Opcional: Tareas de implementación
```

## Estados de Cambios

**APPROVED & IMPLEMENTED**
- Cambio fue aprobado y completamente implementado
- Tests pasando
- Documentado y listo para producción

**IN PROGRESS**
- Cambio en proceso de implementación
- Especificación definida
- Algunos tests passing

**PROPOSED**
- Cambio propuesto pero no aprobado
- Necesita revisión y validación

**PENDING**
- Cambio planeado para futuro
- No iniciado aún

## Información Adicional

### Dependencias Entre Fases
```
Phase 1 (Foundation)
  └─→ Phase 2 (Chunking) uses config & logging
      └─→ Phase 3 (Vector Store) uses chunks
          └─→ Phase 4 (RAG Pipeline) uses retriever
              └─→ Phase 5 (Deployment) packages all
```

### Archivo de Configuración Relacionado
`project.md` define la configuración global que todas las fases respetan:
- Code style (PEP 8, type hints)
- Naming conventions
- Testing strategy
- Git workflow
- Domain concepts

## Próximos Pasos

- [ ] Implementar Phase 6: Frontend (React + TypeScript)
- [ ] Crear specs para Phase 6
- [ ] Implementar Phase 7: Evaluation Datasets
- [ ] Crear specs para Phase 7
- [ ] Implementar Phase 8: Production Monitoring
- [ ] Crear specs para Phase 8

## Recursos

- [OpenSpec Documentation](https://openspec.dev)
- [Project Context](./project.md)
- [AI Assistant Guidelines](./AGENTS.md)
- [Implementation Phases](./changes/)

---

**Última actualización**: December 22, 2025
**Status**: 5/8 Fases documentadas (62.5%)
