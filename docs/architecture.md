# Arquitectura y Diseño Técnico: Intelligent QA (MVP)

## 1. Visión General y Objetivos
El proyecto **Intelligent QA** implementa una solución de Aseguramiento de Calidad asistida por IA generativa (Google Gemini `gemini-3.8-flash`) para mitigar dos problemáticas habituales en ingeniería de software:
- La baja calidad, ambigüedad o inconsistencia en especificaciones funcionales de requisitos (ISO/IEC/IEEE 29148 e IEEE 830).
- La falta de documentación y pruebas automatizadas en sistemas legados (Java y Python).

---

## 2. Decisiones Arquitectónicas Clave (ADRs)

### ADR-01: Externalización Absoluta de Prompts
- **Decisión:** Prohibir cadenas de prompts hardcodeadas en Python. Todos los templates residen en `data/prompts/` y se cargan mediante `src.core.config.PromptLoader`.
- **Justificación:** Permite el ajuste fino de directrices e ingeniería de prompts sin alterar el ciclo de vida del código ni requerir redespliegues. Si falta alguna plantilla, el backend aborta su arranque (*fail-fast*).

### ADR-02: Guardrail Fail-Closed y Mensaje Estandarizado
- **Decisión:** Implementar un clasificador previo que verifique sintaxis determinista (`ast.parse` para Python, patrones estructurales para Java) y semántica LLM antes de invocar agentes.
- **Justificación:** Si un archivo es mixto, informal o ajeno a Java/Python, se bloquea con el mensaje unificado:
  > *"La documentación adjunta no es un requisito ni un fichero de código fuente de Java o Python."*

### ADR-03: Orquestación con Grafos de Estado (LangGraph)
- **Decisión:** Utilizar `StateGraph` de LangGraph en lugar de cadenas rígidas (Chains) o bucles abiertos ReAct no restringidos.
- **Justificación:** Proporciona control determinista sobre el flujo de ejecución, enrutamiento condicional estricto por acción (`add_conditional_edges`), aislamiento de fallos en nodos de error dedicados y trazabilidad del estado.

---

## 3. Diagrama de Flujo del Sistema
[ Fichero Subido (.java, .py, .md, .txt) ]
                                     │
                                     ▼
                 ┌───────────────────────────────────────┐
                 │     Guardrail / FileClassifier        │
                 └───────────────────┬───────────────────┘
                                     │
               ┌─────────────────────┴─────────────────────┐
               │                                           │
     [ Clasificación Válida ]                     [ Clasificación INVALID ]
               │                                           │
     ┌─────────┴─────────┐                                 ▼
     ▼                   ▼                      Mensaje Mandatario:
REQUIREMENT         CÓDIGO (JAVA/PY)             "La documentación adjunta no es
│                   │                       un requisito ni un fichero de
▼                   ▼                       código fuente de Java o Python."
[RequirementsAgent]   [CodeAgent]
(LangGraph State)    (LangGraph State)
├── Inconsistencias   ├── Ing. Inversa
├── ISO/IEEE 29148    └── JUnit / Pytest
└── Casos de Prueba

---

## 4. Trazabilidad y Observabilidad
El módulo `src.core.logger.py` implementa `StructuredLogger` y el gestor de contexto `measure_execution_time`. Registra en formato JSON estructurado:
- Metadatos de subida (nombre, tamaño en bytes, extensión).
- Veredicto de clasificación y nivel de certeza.
- Tiempo exacto de cómputo por herramienta/agente.
- Trazas de excepciones sin exponer información sensible.