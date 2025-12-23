# 🤖 Samantha - Bot de Viáticos

**Samantha** es tu asistente personal de viáticos para Telegram. Con personalidad cálida y humana, te ayuda a llevar un control ordenado de todas tus facturas usando OCR (reconocimiento óptico de caracteres) y generación automática de reportes Excel.

## ✨ Características

- 📸 **OCR Automático**: Solo envía la foto de tu factura y Samantha extrae todos los datos automáticamente
- 💼 **Gestión Completa**: Registra, consulta, edita y elimina facturas fácilmente
- 📊 **Reportes Excel**: Genera archivos Excel listos para tus reportes de viáticos
- 🗄️ **Base de Datos SQLite**: Almacenamiento local seguro y confiable
- 🔒 **Variables de Entorno**: Configuración segura con archivos .env
- 📝 **Logging Completo**: Sistema de logs para seguimiento y depuración
- 🏗️ **Arquitectura Modular**: Código organizado y fácil de mantener

## 🚀 Instalación

### Requisitos Previos

1. **Python 3.8 o superior**
   - Descargar desde: https://www.python.org/downloads/
   - **IMPORTANTE**: Durante la instalación, marca "Add Python to PATH"

2. **Tesseract OCR**
   - Descargar desde: https://github.com/UB-Mannheim/tesseract/wiki
   - Después de instalar, agregar al PATH del sistema
   - Ruta típica: `C:\Program Files\Tesseract-OCR`

3. **Token de Telegram Bot**
   - Abre Telegram y busca `@BotFather`
   - Envía `/newbot` y sigue las instrucciones
   - Guarda el TOKEN que te proporciona

### Instalación en Windows

1. **Clonar o descargar el repositorio**
   ```bash
   git clone https://github.com/VonDefiant/Samantha-Bot-Viaticos.git
   cd Samantha-Bot-Viaticos
   ```

2. **Ejecutar el instalador**
   ```bash
   install.bat
   ```
   Este script hará:
   - Verificar Python
   - Crear entorno virtual
   - Instalar dependencias
   - Verificar Tesseract
   - Crear archivo `.env`

3. **Configurar el TOKEN**
   - Abre el archivo `.env` con un editor de texto
   - Reemplaza `tu_token_aqui` con tu TOKEN de BotFather
   ```env
   TELEGRAM_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   NIT_EMPRESA=71224556
   ```

4. **Iniciar el bot**
   ```bash
   start.bat
   ```

### Instalación en Linux/Mac

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/VonDefiant/Samantha-Bot-Viaticos.git
   cd Samantha-Bot-Viaticos
   ```

2. **Crear entorno virtual**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Instalar Tesseract**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install tesseract-ocr tesseract-ocr-spa

   # macOS
   brew install tesseract tesseract-lang
   ```

5. **Configurar .env**
   ```bash
   cp .env.example .env
   nano .env  # Editar y agregar tu TOKEN
   ```

6. **Iniciar el bot**
   ```bash
   python main.py
   ```

## 📖 Uso

### Comandos Disponibles

| Comando | Descripción |
|---------|-------------|
| `/start` | Inicia el bot y muestra el menú principal |
| `/nueva` | Registra una nueva factura |
| `/resumen` | Muestra resumen de gastos |
| `/lista` | Lista las últimas 20 facturas |
| `/exportar` | Genera y envía archivo Excel |
| `/borrar <id>` | Elimina una factura por su ID |
| `/help` | Muestra ayuda detallada |
| `/cancelar` | Cancela la operación actual |

### Flujo de Registro de Factura

1. Envía `/nueva`
2. Selecciona tipo de gasto (Alimentación o Combustible)
3. Envía la foto de la factura
4. Samantha extrae los datos automáticamente
5. Revisa los datos extraídos
6. Edita si es necesario o confirma
7. ¡Listo! Factura guardada

### Tips para Mejor OCR

- 📸 Toma la foto con buena iluminación
- 📏 Mantén la factura plana y sin arrugas
- 🔍 Asegúrate que el texto sea legible
- ❌ Evita sombras y reflejos
- ✅ Enfoca bien la cámara

## 🏗️ Estructura del Proyecto

```
Samantha-Bot-Viaticos/
│
├── src/                      # Código fuente modular
│   ├── __init__.py          # Inicialización del paquete
│   ├── config.py            # Configuración y variables
│   ├── database.py          # Gestión de base de datos
│   ├── ocr.py               # Procesamiento OCR
│   ├── excel_export.py      # Exportación a Excel
│   ├── utils.py             # Utilidades y logging
│   └── bot.py               # Lógica principal del bot
│
├── main.py                  # Punto de entrada
├── requirements.txt         # Dependencias Python
├── .env.example             # Ejemplo de configuración
├── .gitignore              # Archivos ignorados por Git
│
├── install.bat             # Instalador para Windows
├── start.bat               # Iniciador para Windows
│
├── facturas/               # Carpeta de facturas (git ignored)
├── logs/                   # Carpeta de logs (git ignored)
└── README.md              # Este archivo
```

## 🔧 Configuración Avanzada

### Variables de Entorno (.env)

```env
# Token de Telegram Bot
TELEGRAM_TOKEN=tu_token_aqui

# NIT de tu empresa (para filtrar en OCR)
NIT_EMPRESA=71224556
```

### Niveles de Logging

Puedes ajustar el nivel de logging en `main.py`:

```python
configurar_logging(nivel=logging.DEBUG)  # DEBUG, INFO, WARNING, ERROR
```

## 🐛 Solución de Problemas

### El bot no inicia

1. Verifica que el archivo `.env` existe y contiene el TOKEN correcto
2. Revisa los logs en la carpeta `logs/`
3. Asegúrate que todas las dependencias están instaladas

### OCR no funciona

1. Verifica que Tesseract está instalado: `tesseract --version`
2. Asegúrate que Tesseract está en el PATH del sistema
3. Revisa que las fotos tengan buena calidad y iluminación

### Error al generar Excel

1. Verifica que la carpeta `facturas/` existe
2. Asegúrate que tienes permisos de escritura
3. Revisa los logs para ver el error específico

## 📝 Base de Datos

Samantha usa SQLite para almacenar las facturas. La base de datos se crea automáticamente en `viaticos.db`.

### Esquema de la tabla `facturas`:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | INTEGER | ID único (autoincremental) |
| fecha | TEXT | Fecha de la factura |
| nit_proveedor | TEXT | NIT del proveedor |
| nombre_proveedor | TEXT | Nombre del proveedor |
| serie | TEXT | Serie de la factura |
| numero | TEXT | Número de la factura |
| tipo_gasto | TEXT | ALIMENTACIÓN o COMBUSTIBLE |
| monto | REAL | Monto en quetzales |
| foto_path | TEXT | Ruta de la foto |
| created_at | TEXT | Fecha de registro |

## 🤝 Contribuir

Las contribuciones son bienvenidas. Para cambios importantes:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

## 👨‍💻 Autor

Creado con ❤️ para facilitar el control de viáticos

## 🙏 Agradecimientos

- python-telegram-bot por la excelente biblioteca
- Tesseract OCR por el motor de reconocimiento de texto
- Todos los que contribuyan al proyecto

---

**¿Preguntas o problemas?** Abre un issue en GitHub o contacta al administrador.
