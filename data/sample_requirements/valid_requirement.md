# Especificación de Requisitos de Software: Servicio de Transferencias Bancarias Inmediatas

## 1. Identificación y Control del Documento
- **Módulo:** Core Bancario - Transferencias STP (Straight-Through Processing)
- **Versión:** 1.0.0
- **Estándar:** ISO/IEC/IEEE 29148:2018

## 2. Requisitos Funcionales

### [REQ-TRF-001] Validación de Fondos Disponibles
- **Actor:** Sistema Core Bancario
- **Disparador:** Recepción de solicitud de transferencia entrante.
- **Descripción:** El sistema debe verificar que el saldo disponible en la cuenta origen sea mayor o igual a la suma del monto a transferir más la comisión por transferencia inmediata antes de autorizar la transacción.
- **Precondiciones:** La cuenta bancaria de origen debe encontrarse en estado ACTIVA y no poseer bloqueos judiciales.
- **Entradas:** 
  - `cuenta_origen`: Identificador IBAN válido (24 caracteres alfanuméricos).
  - `monto_transferencia`: Decimal mayor que 0.00 con hasta 2 cifras decimales.
- **Cálculo de Comisión:** 
  - Comisión fija de 1.50 EUR para montos inferiores o iguales a 500.00 EUR.
  - Comisión fija de 3.00 EUR para montos superiores a 500.00 EUR.
- **Salidas:**
  - Si los fondos son suficientes: Emitir evento `FONDOS_RESERVADOS` con el monto total debitado temporalmente.
  - Si los fondos son insuficientes: Rechazar la transacción retornando código `ERR_SALDO_INSUFICIENTE` y mantener el saldo intacto.

### [REQ-TRF-002] Límite Operativo Diario
- **Actor:** Sistema de Gestión de Riesgo
- **Descripción:** El sistema debe denegar cualquier transferencia inmediata si la suma acumulada de las transferencias emitidas por el cliente en las últimas 24 horas calendario supera el umbral máximo de 10,000.00 EUR.
- **Tratamiento de Excepciones:** Retornar código `ERR_LIMITE_DIARIO_EXCEDIDO` con el monto restante disponible para transferir en el día.

### [REQ-TRF-003] Notificación de Confirmación
- **Actor:** Servicio de Mensajería
- **Descripción:** Una vez completada la transferencia con éxito en la cámara de compensación, el sistema debe remitir un mensaje SMS y un correo electrónico al titular de la cuenta origen en un tiempo no superior a 3 segundos tras la confirmación.