# 🚀 INICIO RÁPIDO - Samantha (Bot de Viáticos)

## ⚡ 3 Pasos para que Samantha te ayude

### 1️⃣ Instalar Tesseract OCR

**Windows:**
1. Descargar: https://github.com/UB-Mannheim/tesseract/wiki
2. Instalar (siguiente, siguiente, siguiente...)
3. Agregar al PATH o editar `bot_viaticos.py` línea 12:
   ```python
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

### 2️⃣ Instalar Python y dependencias

```bash
# Opción A: Script automático (Windows)
install.bat

# Opción B: Manual
pip install -r requirements.txt
```

### 3️⃣ Crear bot en Telegram

1. Abrir Telegram → Buscar: `@BotFather`
2. Enviar: `/newbot`
3. Nombre: `Samantha - Viáticos` (o el que prefieras)
4. Username: `tu_samantha_viaticos_bot`
5. **COPIAR EL TOKEN** que te da
6. Pegar en `bot_viaticos.py` línea 20:
   ```python
   TOKEN = 'aqui_pega_tu_token'
   ```

---

## ▶️ Ejecutar

```bash
python bot_viaticos.py
```

---

## 📱 Usar el bot

1. Abrir Telegram → Buscar tu bot
2. Enviar: `/start`
3. Enviar: `/nueva`
4. Seguir las instrucciones

---

## 🔧 Verificar instalación

### Probar Tesseract:
```bash
tesseract --version
```

### Probar OCR con una factura:
```bash
python test_ocr.py ruta_a_tu_factura.jpg
```

---

## ⚠️ Problemas comunes

### "Tesseract not found"
- Instalar Tesseract OCR
- Agregar al PATH del sistema
- O especificar ruta en bot_viaticos.py

### "Invalid token"
- Verificar que pegaste el token completo
- Sin espacios ni comillas extras

### OCR no funciona bien
- Tomar fotos con buena luz
- Texto legible y claro
- Usar opción "Editar" para corregir

---

## 📊 Comandos del bot

- `/nueva` - Nueva factura
- `/resumen` - Ver totales
- `/lista` - Ver facturas
- `/exportar` - Crear Excel
- `/borrar <id>` - Eliminar

---

## 💡 Tips

1. **Fotos claras**: Buena iluminación, sin sombras
2. **Revisar datos**: Siempre verifica antes de confirmar
3. **Editar**: Si algo está mal, usa la opción "Editar"
4. **Exportar seguido**: Haz exports regulares como backup

---

## 📞 Ayuda adicional

- Lee el **README.md** para más detalles
- Usa `python test_ocr.py` para probar el OCR
- Revisa los logs en la consola si hay errores

---

**¡Listo para usar!** 🎉
