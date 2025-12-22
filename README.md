# 🤖 Samantha - Tu Asistente de Viáticos en Telegram

Bot de Telegram con personalidad amigable que extrae automáticamente datos de facturas usando OCR y exporta a Excel con el formato de Research & Planning Guatemala.

**Samantha** es tu asistente personal que hace que llevar el control de viáticos sea fácil y hasta divertido. Solo enviá fotos de tus facturas y ella se encarga de todo lo demás 😊

## 📋 Características

- ✅ Extracción automática de datos con OCR
- ✅ Validación de NIT (excluye NIT de la empresa: 71224556)
- ✅ Edición de datos antes de guardar
- ✅ Categorías: ALIMENTACIÓN y COMBUSTIBLE
- ✅ Exportación a Excel con formato específico
- ✅ Base de datos SQLite local
- ✅ Consultas y resúmenes

## 🔧 Instalación

### 1. Instalar Tesseract OCR

**En Windows:**
- Descarga e instala desde: https://github.com/UB-Mannheim/tesseract/wiki
- Agrega Tesseract al PATH del sistema
- O especifica la ruta en el código:
  ```python
  pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
  ```

**En Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-spa  # Idioma español
```

**En macOS:**
```bash
brew install tesseract
brew install tesseract-lang  # Idiomas adicionales
```

### 2. Instalar dependencias de Python

```bash
pip install -r requirements.txt
```

### 3. Crear el bot en Telegram

1. Abre Telegram y busca: **@BotFather**
2. Envía el comando: `/newbot`
3. Sigue las instrucciones:
   - Nombre del bot: `Control de Viáticos` (o el que quieras)
   - Username: `mi_viaticos_bot` (debe terminar en "bot")
4. Copia el **TOKEN** que te proporciona BotFather
5. Pégalo en el archivo `bot_viaticos.py` en la línea:
   ```python
   TOKEN = 'TU_TOKEN_AQUI'  # <- Aquí pega tu token
   ```

## 🚀 Ejecución

```bash
python bot_viaticos.py
```

Samantha te saludará con:
```
✨ Samantha está lista para ayudarte con tus viáticos!
Presiona Ctrl+C para detener
```

## 📱 Uso del Bot

### Comandos Disponibles

- `/start` - Iniciar el bot y ver comandos
- `/nueva` - Registrar nueva factura
- `/resumen` - Ver resumen de gastos
- `/lista` - Ver últimas 20 facturas
- `/exportar` - Exportar a Excel
- `/borrar <id>` - Eliminar factura por ID
- `/help` - Ayuda

### Flujo de Trabajo

1. **Envía** `/nueva`
2. **Samantha te pregunta:** ¿Es ALIMENTACIÓN o COMBUSTIBLE?
3. **Enviás** foto de la factura
4. **Samantha lee** automáticamente todos los datos
5. **Revisás** lo que encontró:
   - 📅 Fecha (automática)
   - 🏢 NIT Proveedor
   - 👤 Nombre del Proveedor
   - 🔢 Serie
   - 📄 Número de Factura
   - 💰 Monto
6. **Confirmás** o **Editás** si algo no está correcto
7. **¡Listo!** Samantha guarda tu factura con mucho cariño 😊

### Exportar a Excel

1. Envía `/exportar`
2. El bot generará un archivo Excel con formato:
   ```
   viaticos_12_2025.xlsx
   ```
3. El archivo incluye:
   - Headers del formato de R&P Guatemala
   - Todas las facturas con sus datos
   - Numeración automática
   - Formato profesional

### Consultar Resumen

```
/resumen
```

Muestra:
- 💰 Total gastado
- 📄 Cantidad de facturas
- 🏷️ Desglose por tipo de gasto

### Eliminar Factura

```
/borrar 5
```

Elimina la factura con ID 5 (usa `/lista` para ver los IDs)

## 📊 Estructura de Datos

### Base de Datos (SQLite)

Tabla `facturas`:
- `id` - ID único
- `fecha` - Fecha en formato DD/MM/YYYY
- `nit_proveedor` - NIT del emisor de la factura
- `nombre_proveedor` - Nombre del proveedor
- `serie` - Serie de la factura
- `numero` - Número de la factura
- `tipo_gasto` - ALIMENTACIÓN o COMBUSTIBLE
- `monto` - Monto en Quetzales
- `foto_path` - Ruta de la foto guardada
- `created_at` - Timestamp de creación

### Formato de Excel

Columnas exportadas:
1. `No.` - Numeración automática
2. `FECHA` - Fecha de la factura
3. `NIT PROVEEDOR` - NIT del proveedor
4. `SERIE` - Serie de la factura
5. `No. COMPROBANTE` - Número de factura
6. `TIPO DE GASTO` - ALIMENTACIÓN o COMBUSTIBLE
7. `MONTO Q.` - Monto en Quetzales

## 🔍 Validaciones

El bot realiza las siguientes validaciones:

1. ✅ **NIT**: No debe ser 71224556 (NIT de la empresa)
2. ✅ **Tipo de Gasto**: Solo acepta ALIMENTACIÓN o COMBUSTIBLE
3. ✅ **Monto**: Debe ser un número válido
4. ✅ **Datos Editables**: Permite corregir cualquier campo

## 📂 Estructura de Archivos

```
.
├── bot_viaticos.py         # Código principal del bot
├── requirements.txt        # Dependencias de Python
├── README.md              # Este archivo
├── viaticos.db            # Base de datos SQLite (se crea automáticamente)
└── facturas/              # Carpeta con fotos y Excel (se crea automáticamente)
    ├── factura_20251222_143052.jpg
    ├── factura_20251222_150315.jpg
    └── viaticos_12_2025.xlsx
```

## 🛠️ Personalización

### Cambiar NIT de la empresa

En `bot_viaticos.py`, línea 22:
```python
NIT_EMPRESA = '71224556'  # Cambia este valor
```

### Agregar más tipos de gasto

Modifica la función `nueva_factura()`:
```python
keyboard = [['ALIMENTACIÓN', 'COMBUSTIBLE', 'HOSPEDAJE']]  # Agrega más
```

Y ajusta las validaciones en `recibir_categoria()`.

### Mejorar OCR

Si el OCR no funciona bien, puedes:
1. Mejorar la calidad de las fotos
2. Ajustar los patrones regex en `extraer_datos_factura()`
3. Usar una API de OCR más potente (Google Vision, AWS Textract)

## ⚠️ Troubleshooting

### Error: "Tesseract not found"
- Asegúrate de tener Tesseract instalado
- Verifica que esté en el PATH del sistema
- O especifica la ruta manualmente en el código

### Error: "Invalid token"
- Verifica que el TOKEN esté correcto
- No debe tener espacios ni comillas extras
- Debe ser el token completo de BotFather

### Error: "Permission denied" al guardar fotos
- Asegúrate de tener permisos de escritura en la carpeta
- El bot crea automáticamente la carpeta `facturas/`

### OCR extrae datos incorrectos
- Toma fotos con buena iluminación
- Asegúrate que el texto esté legible
- Usa la opción "Editar" para corregir manualmente

## 📞 Soporte

Si tienes problemas:
1. Revisa los logs en la consola
2. Verifica que todas las dependencias estén instaladas
3. Asegúrate que Tesseract esté funcionando: `tesseract --version`

## 📝 Notas

- Las fotos se guardan en `facturas/`
- La base de datos es local (`viaticos.db`)
- Los datos no se comparten con terceros
- Puedes hacer backup de `viaticos.db` para conservar tus datos

## 🎯 Próximas Mejoras

- [ ] Respaldo automático en Google Drive
- [ ] Reportes por mes
- [ ] Gráficas de gastos
- [ ] Reconocimiento de proveedores frecuentes
- [ ] Alertas de presupuesto

---

**Desarrollado para Research & Planning Guatemala**
Automatización de control de viáticos con Telegram Bot
