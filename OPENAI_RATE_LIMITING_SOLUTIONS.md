# Soluciones para OpenAI Rate Limiting (429 Too Many Requests)

**Problema**: El error `429 Too Many Requests` ocurre cuando se envían múltiples archivos al mismo tiempo, causando muchas llamadas simultáneas a OpenAI.

**Causas**:
1. Metadata extraction para cada chunk (espera de respuesta OpenAI)
2. Embeddings para cada chunk (llamadas simultáneas)
3. Varias solicitudes concurrentes sin delay

---

## 🎯 Soluciones Propuestas (Ordenadas por Recomendación)

### **SOLUCIÓN 1: Rate Limiting con Retry Automático ⭐ RECOMENDADA**

**Descripción**: Usar LangChain's built-in retry logic con exponential backoff.

**Ventajas**:
- ✅ Automático y transparente
- ✅ Respeta rate limits de OpenAI
- ✅ No requiere cambios en lógica de negocio
- ✅ Maneja otros errores (timeouts, 429, etc)
- ✅ Mejor que delay fijo (más eficiente)

**Ventajas vs Delay Fijo**:
- Delay fijo = esperar siempre, aunque no lo necesites
- Retry automático = solo espera si OpenAI dice que esperes

**Implementación**:

```python
# En metadata_handler.py y chain_builder.py

from langchain_core.utils.function_calling import convert_to_openai_function
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
import httpx

# Decorator para reintentos automáticos
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=60),  # 2s, 4s, 8s...
    retry=retry_if_exception_type(httpx.HTTPStatusError),
)
def extract_metadata_with_retry(self, text: str):
    return self.extract_metadata(text)

# O aplicar a nivel de LLM:
self.llm = ChatOpenAI(
    model=settings.openai_model,
    temperature=0,
    api_key=settings.openai_api_key,
    max_retries=3,  # Reintentos automáticos
    timeout=30,
)
```

**Complejidad**: ⭐ Baja (1 parámetro)
**Costo**: Sin costo adicional
**Tiempo implementación**: 15 minutos

---

### **SOLUCIÓN 2: Rate Limiting con Delay Fijo (1 segundo)**

**Descripción**: Agregar delay de 1 segundo entre llamadas a OpenAI.

**Ventajas**:
- ✅ Simple de implementar
- ✅ Predecible (siempre espera X segundos)
- ✅ Garantiza que no tendrás 429

**Desventajas**:
- ❌ Ineficiente (esperas aunque no lo necesites)
- ❌ Más lento overall (siempre suma 1s por llamada)
- ❌ No se adapta si OpenAI está más lento
- ❌ 10 archivos = mínimo 10 segundos

**Implementación**:

```python
import time
from functools import wraps

def rate_limit_openai(delay_seconds=1.0):
    """Decorator que agrega delay entre llamadas a OpenAI"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            time.sleep(delay_seconds)
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Usar en metadata_handler.py:
@rate_limit_openai(delay_seconds=1.0)
def extract_metadata(self, text: str):
    # ...
```

**Complejidad**: ⭐ Baja
**Costo**: Tiempo (más lento)
**Tiempo implementación**: 10 minutos

---

### **SOLUCIÓN 3: Batch Processing + Async**

**Descripción**: Procesar archivos secuencialmente en lugar de paralelo, pero usar async para no bloquear.

**Ventajas**:
- ✅ No bloquea threads
- ✅ Escalable para múltiples usuarios
- ✅ Eficiente en recursos

**Desventajas**:
- ❌ Más complejo de implementar
- ❌ Requiere refactor significativo

**Implementación**:

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def process_documents_sequentially(documents):
    """Procesa documentos uno por uno de forma asincrónica"""
    results = []
    for doc in documents:
        result = await asyncio.sleep(1.0)  # Rate limit
        result = await process_document(doc)
        results.append(result)
    return results
```

**Complejidad**: ⭐⭐⭐ Media-Alta
**Costo**: Sin costo adicional
**Tiempo implementación**: 1-2 horas

---

### **SOLUCIÓN 4: Deshabilitar Metadata Extraction**

**Descripción**: Opción de toggle para desactivar la extracción de metadata que consume muchas llamadas a OpenAI.

**Ventajas**:
- ✅ Inmediato (sin 429)
- ✅ Reduce costos OpenAI
- ✅ Más rápido
- ✅ Usuario elige si quiere o no

**Desventajas**:
- ❌ Pierde información semántica
- ❌ Afecta calidad de búsqueda

**Implementación**:

```python
# En config/settings.py:
ENABLE_METADATA_EXTRACTION: bool = Field(
    default=False,  # Desactivar por defecto
    description="Enable metadata extraction (uses OpenAI calls)"
)

# En api/main.py:
async def initialize(
    collection_name: str,
    documents: List[Dict],
    force_recreate: bool = False,
    enable_metadata: bool = False  # Parameter
):
    # Solo extraer metadata si está habilitado
```

**Complejidad**: ⭐ Baja
**Costo**: Sin costo
**Tiempo implementación**: 20 minutos

---

### **SOLUCIÓN 5: Redis Cache para Metadata**

**Descripción**: Cachear metadata ya extraída para no repetir llamadas.

**Ventajas**:
- ✅ No re-procesa documentos iguales
- ✅ Reduce llamadas OpenAI
- ✅ Rápido para documentos conocidos

**Desventajas**:
- ❌ No ayuda con documentos nuevos
- ❌ Complejidad media

**Implementación**:

```python
from src.services.cache import RedisCache

class MetadataHandlerCached:
    def __init__(self):
        self.cache = RedisCache()
        self.handler = MetadataHandler()

    def extract_metadata(self, text: str) -> Dict:
        # Crear hash del texto
        cache_key = f"metadata:{hash(text)}"

        # Buscar en cache
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        # Si no está, extraer y cachear
        result = self.handler.extract_metadata(text)
        self.cache.set(cache_key, result, ttl=86400)  # 24 horas
        return result
```

**Complejidad**: ⭐⭐ Media
**Costo**: Sin costo adicional (Redis ya está)
**Tiempo implementación**: 45 minutos

---

### **SOLUCIÓN 6: Hybrid (Recomendado para Producción)**

**Descripción**: Combinar retry automático + disable metadata + cache.

**Ventajas**:
- ✅ Máxima resiliencia
- ✅ Bajo costo
- ✅ Rápido
- ✅ Escalable

**Implementación** (Orden de prioridad):

1. **Primero**: Retry automático en LLM (SOLUCIÓN 1)
2. **Segundo**: Deshabilitar metadata por defecto (SOLUCIÓN 4)
3. **Tercero**: Cachear cuando esté habilitada (SOLUCIÓN 5)

**Tiempo total implementación**: 2 horas

---

## 📊 Comparativa de Soluciones

| Solución | Eficiencia | Complejidad | Tiempo | Recomendación |
|----------|-----------|-----------|--------|------|
| **1. Retry Auto** | ⭐⭐⭐⭐⭐ | ⭐ | 15min | ✅ INMEDIATO |
| **2. Delay Fijo** | ⭐⭐ | ⭐ | 10min | ❌ Lento |
| **3. Async Batch** | ⭐⭐⭐⭐ | ⭐⭐⭐ | 2h | Futuro |
| **4. Deshabilitar Meta** | ⭐⭐⭐ | ⭐ | 20min | ✅ Combinable |
| **5. Redis Cache** | ⭐⭐⭐ | ⭐⭐ | 45min | ✅ Combinable |
| **6. Hybrid** | ⭐⭐⭐⭐⭐ | ⭐⭐ | 2h | ✅✅ ÓPTIMO |

---

## 🎯 Mi Recomendación

**Para ahora (inmediato)**:
```
SOLUCIÓN 1: Agregar max_retries=3 al ChatOpenAI
→ 15 minutos
→ Resuelve el problema automáticamente
→ Sin impacto en performance
```

**Para después (próxima iteración)**:
```
SOLUCIÓN 6: Hybrid approach
1. Retry automático ✅ (ya hecho)
2. + Deshabilitar metadata por defecto
3. + Cachear si está habilitada

→ 2 horas total
→ Sistema robusto y eficiente
→ Listo para producción
```

---

## ✅ Mi Recomendación Final

**Implementar AHORA**:
- SOLUCIÓN 1 (Retry automático) - 15 minutos

**Implementar en Phase 6B**:
- SOLUCIÓN 4 + 5 + 1 (Hybrid) - 2 horas

¿Cuál prefieres que implemente primero?

