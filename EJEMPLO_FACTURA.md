# 📋 Ejemplo de Datos Extraídos de Factura

## Factura de Gasolina - Neonet (Ejemplo real)

### ✅ Datos que el bot debe extraer:

```
📅 FECHA: 09/12/2025 (fecha actual por defecto, editable)

🏢 NIT PROVEEDOR: 4008360
   ✓ Este es el NIT del emisor (gasolinera)
   ✗ NO debe ser: 71224556 (tu empresa)

👤 NOMBRE PROVEEDOR: MARIO ROLANDO RODRIGUEZ POSADAS - ESTACION CITY GAS

🔢 SERIE: D74B9A54

📄 No. COMPROBANTE: 275203802

🏷️ TIPO DE GASTO: COMBUSTIBLE
   (opciones: ALIMENTACIÓN o COMBUSTIBLE)

💰 MONTO: Q313.34
```

---

## 🔍 Cómo el bot extrae los datos

### 1. NIT del Proveedor
El bot busca la palabra "NIT" en la factura y toma el número que NO sea 71224556

**En la factura se ve:**
```
NIT: 4008360
MARIO ROLANDO RODRIGUEZ POSADAS
```

**El bot extrae:** `4008360`

---

### 2. Nombre del Proveedor
Busca el texto cerca del NIT que no sean solo números

**En la factura se ve:**
```
MARIO ROLANDO RODRIGUEZ POSADAS
ESTACION CITY GAS
```

**El bot extrae:** `MARIO ROLANDO RODRIGUEZ POSADAS - ESTACION CITY GAS`

---

### 3. Serie
Busca la palabra "SERIE" y el código alfanumérico que sigue

**En la factura se ve:**
```
SERIE: D74B9A54
```

**El bot extrae:** `D74B9A54`

---

### 4. Número de Factura
Busca "NUMERO" o "No." y extrae los dígitos

**En la factura se ve:**
```
NÚMERO: 275203802
```

**El bot extrae:** `275203802`

---

### 5. Monto
Busca "TOTAL" y el monto con "Q"

**En la factura se ve:**
```
TOTAL         Q313.34
```

**El bot extrae:** `313.34`

---

## ⚠️ Casos donde necesitarás editar

### Problema: OCR lee mal un número
```
❌ El bot lee: NIT 480360 (falta un 0)
✅ Tú editas a: NIT 4008360
```

### Problema: No encuentra la serie
```
❌ El bot muestra: Serie: No encontrado
✅ Tú ingresas manualmente: D74B9A54
```

### Problema: Monto incorrecto
```
❌ El bot lee: Q31.34 (falta un 3)
✅ Tú corriges a: Q313.34
```

---

## 📊 Resultado en Excel

Después de confirmar, la factura se guarda así:

| No. | FECHA | NIT PROVEEDOR | SERIE | No. COMPROBANTE | TIPO DE GASTO | MONTO Q. |
|-----|-------|---------------|-------|-----------------|---------------|----------|
| 1 | 09/12/2025 | 4008360 | D74B9A54 | 275203802 | COMBUSTIBLE | 313.34 |

---

## 💡 Consejos para mejores resultados

1. **Buena iluminación**: Evita sombras sobre la factura
2. **Foto directa**: Lo más perpendicular posible
3. **Factura plana**: Sin arrugas ni dobleces
4. **Enfoque claro**: Texto legible en la imagen
5. **Contraste**: Fondo claro, texto oscuro

---

## 🎯 Flujo completo

```
1. /nueva
   ↓
2. Selecciona: COMBUSTIBLE
   ↓
3. Envía foto
   ↓
4. Bot extrae datos
   ↓
5. Revisas:
   ✅ Fecha: 09/12/2025 → OK
   ✅ NIT: 4008360 → OK
   ✅ Nombre: MARIO... → OK
   ✅ Serie: D74B9A54 → OK
   ❌ Número: 27520380 → EDITAR a 275203802
   ✅ Monto: Q313.34 → OK
   ↓
6. Editar → Número → 275203802
   ↓
7. Listo, Guardar
   ↓
8. ✅ Factura #1 registrada!
```

---

**Recuerda:** El OCR es una ayuda, siempre verifica los datos antes de confirmar! 🔍
