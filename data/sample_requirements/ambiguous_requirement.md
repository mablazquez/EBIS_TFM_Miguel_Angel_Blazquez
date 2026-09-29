# Documento Funcional: Módulo de Facturación y Descuentos para Clientes

## Descripción General
El sistema debe ser súper rápido y permitir a los administradores aplicar descuentos a las facturas de forma intuitiva y adecuada según el perfil del cliente.

## Reglas de Descuento
1. A los clientes frecuentes se les debe otorgar un descuento muy bueno cuando compren bastante cantidad.
2. Si el cliente tiene una cuenta VIP, el descuento debe ser del 15% sobre el total. Sin embargo, para clientes VIP con compras grandes, el descuento aplicable será del 10% para proteger el margen de la empresa.
3. El monto máximo de una factura para aplicar descuento es de 5,000 EUR. En caso de clientes corporativos, las facturas pueden superar los 5,000 EUR y recibirán un descuento preferencial determinado oportunamente por el departamento de finanzas.
4. El procesamiento de la factura no debería tardar mucho tiempo para no degradar la experiencia de usuario.
5. Cuando el cliente no tenga fondos suficientes, el sistema intentará cobrar un par de veces más antes de cancelar todo.