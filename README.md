# 🤖 Samantha - Bot de Viáticos para Telegram

Bot inteligente de Telegram para el control y gestión de viáticos empresariales con capacidades de OCR (reconocimiento óptico de caracteres) para extraer datos automáticamente de fotografías de facturas.

## ✨ Características

- 📸 **Extracción automática de datos** mediante OCR de Tesseract
- 💾 **Almacenamiento en SQLite** de todas las facturas
- 📊 **Exportación a Excel** con formato profesional
- 🎯 **Interfaz intuitiva** con botones interactivos
- 🔍 **Detección mejorada** de montos, series y datos de proveedores
- 🖼️ **Preprocesamiento de imagen** para mejor precisión del OCR
- 📝 **Edición manual** de datos si el OCR falla
- 🔄 **Reintentar fotografía** sin perder el progreso
- 🗑️ **Sistema mejorado de borrado** con ConversationHandler

## 🖥️ Compatibilidad

Compatible con:
- ✅ Windows 10/11
- ✅ Linux (Debian, Ubuntu, y derivados)
- ✅ Oracle Cloud (y otros servicios cloud con Linux)

## 📋 Requisitos

### Windows
- Python 3.8 o superior
- Tesseract OCR (se puede instalar con el script)
- Conexión a Internet

### Linux (Debian/Ubuntu)
- Python 3.8 o superior
- Tesseract OCR (se instala automáticamente)
- sudo (para instalación de dependencias del sistema)

### Token de Telegram
- Abre Telegram y busca `@BotFather`
- Envía `/newbot` y sigue las instrucciones
- Guarda el TOKEN que te proporciona

## 🚀 Instalación

### Windows

1. **Descarga el proyecto:**
   ```bash
   git clone https://github.com/VonDefiant/Samantha-Bot-Viaticos.git
   cd Samantha-Bot-Viaticos
   ```

2. **Ejecuta el instalador:**
   ```bash
   install.bat
   ```
   El instalador:
   - Verifica Python
   - Crea entorno virtual
   - Instala dependencias
   - Verifica Tesseract
   - Crea archivo `.env`

3. **Configura tu token:**
   - Edita el archivo `.env`
   - Agrega tu token de Telegram Bot
   ```env
   TELEGRAM_TOKEN=tu_token_aqui
   NIT_EMPRESA=71224556
   ```

4. **Inicia el bot:**
   ```bash
   start.bat
   ```

### Linux (Debian/Ubuntu/Oracle Cloud)

1. **Descarga el proyecto:**
   ```bash
   git clone https://github.com/VonDefiant/Samantha-Bot-Viaticos.git
   cd Samantha-Bot-Viaticos
   ```

2. **Da permisos a los scripts (si es necesario):**
   ```bash
   chmod +x install.sh start.sh stop.sh run_background.sh
   ```

3. **Ejecuta el instalador:**
   ```bash
   ./install.sh
   ```
   El instalador:
   - Verifica/instala Python 3
   - Verifica/instala Tesseract OCR + español
   - Crea entorno virtual
   - Instala dependencias Python
   - Crea archivo `.env`

4. **Configura tu token:**
   ```bash
   nano .env
   ```
   Agrega tu token de Telegram Bot:
   ```env
   TELEGRAM_TOKEN=tu_token_aqui
   NIT_EMPRESA=71224556
   ```

## 🎮 Uso

### Windows

**Iniciar el bot:**
```bash
start.bat
```

**Detener el bot:**
- Presiona `Ctrl+C` en la ventana del bot
- O ejecuta: `kill_bot.bat`

### Linux - Modo interactivo

**Iniciar el bot:**
```bash
./start.sh
```

**Detener el bot:**
- Presiona `Ctrl+C`
- O en otra terminal: `./stop.sh`

### Linux - Modo background (para servidores)

**Iniciar en segundo plano:**
```bash
./run_background.sh
```

**Ver logs en tiempo real:**
```bash
tail -f logs/bot_output.log
```

**Detener el bot:**
```bash
./stop.sh
```

## 📱 Comandos del Bot

El bot usa botones interactivos, pero también soporta comandos:

| Botón/Comando | Descripción |
|---------------|-------------|
| 📝 Nueva Factura / `/nueva` | Registrar nueva factura |
| 📊 Resumen / `/resumen` | Ver resumen de gastos |
| 📋 Ver Lista / `/lista` | Ver lista de facturas |
| 📥 Exportar Excel / `/exportar` | Exportar a Excel |
| 🗑️ Borrar Factura / `/borrar` | Eliminar una factura |
| ❓ Ayuda / `/help` | Ver ayuda |
| `/start` | Mostrar menú principal |
| `/cancelar` | Cancelar operación actual |

### Flujo de Registro de Factura

1. Presiona **📝 Nueva Factura**
2. Selecciona tipo de gasto (🍔 Alimentación o ⛽ Combustible)
3. Envía la foto de la factura 📸
4. Samantha extrae los datos automáticamente 🔍
5. Revisa los datos extraídos
6. Opciones disponibles:
   - **✅ Aceptar**: Guardar la factura
   - **📸 Reintentar Foto**: Tomar nueva foto
   - **✏️ Editar**: Modificar los datos manualmente
   - **❌ Cancelar**: Cancelar el proceso
7. ¡Listo! Factura guardada 🎉

### Tips para Mejor OCR

- 📸 Toma la foto con buena iluminación
- 📏 Mantén la factura plana y sin arrugas
- 🔍 Asegúrate que el texto sea legible
- ❌ Evita sombras y reflejos
- ✅ Enfoca bien la cámara
- 💡 Si el OCR falla, puedes reintentar la foto o editar manualmente

## 📂 Estructura del Proyecto

```
Samantha-Bot-Viaticos/
│
├── src/                      # Código fuente modular
│   ├── __init__.py          # Inicialización del paquete
│   ├── config.py            # Configuración y variables
│   ├── database.py          # Gestión de base de datos SQLite
│   ├── ocr.py               # Procesamiento OCR mejorado
│   ├── excel_export.py      # Exportación a Excel
│   ├── utils.py             # Utilidades y logging
│   └── bot.py               # Lógica principal del bot
│
├── main.py                  # Punto de entrada
├── requirements.txt         # Dependencias Python
├── .env.example             # Plantilla de configuración
├── .env                     # Configuración (NO subir a git)
├── .gitignore              # Archivos ignorados por Git
│
├── install.bat             # Instalador Windows
├── start.bat               # Inicio Windows
├── kill_bot.bat            # Detener Windows
│
├── install.sh              # Instalador Linux
├── start.sh                # Inicio Linux
├── stop.sh                 # Detener Linux
├── run_background.sh       # Inicio en background Linux
│
├── facturas/               # Imágenes y Excel (git ignored)
├── logs/                   # Logs del bot (git ignored)
├── viaticos.db             # Base de datos SQLite (git ignored)
└── README.md               # Este archivo
```

## 🔧 Configuración en Oracle Cloud

Si vas a usar Oracle Cloud u otro servidor Linux:

1. **Conéctate a tu instancia:**
   ```bash
   ssh usuario@ip-del-servidor
   ```

2. **Instala git si no lo tienes:**
   ```bash
   sudo apt-get update
   sudo apt-get install git
   ```

3. **Clona el repositorio:**
   ```bash
   git clone https://github.com/VonDefiant/Samantha-Bot-Viaticos.git
   cd Samantha-Bot-Viaticos
   ```

4. **Ejecuta la instalación:**
   ```bash
   chmod +x *.sh
   ./install.sh
   ```

5. **Configura el token:**
   ```bash
   nano .env
   ```

6. **Inicia en modo background:**
   ```bash
   ./run_background.sh
   ```

7. **Verifica que está corriendo:**
   ```bash
   tail -f logs/bot_output.log
   ```

8. **Para desconectar sin detener el bot:**
   - Presiona `Ctrl+C` para salir de tail
   - Cierra la sesión SSH normalmente
   - El bot seguirá corriendo en segundo plano

## 🐛 Solución de Problemas

### Windows

**Error: "Conflict: terminated by other getUpdates request"**
- Ejecuta `kill_bot.bat`
- O cierra todos los procesos de Python en el Administrador de Tareas

**Error: "Tesseract not found"**
- Descarga e instala Tesseract desde: https://github.com/UB-Mannheim/tesseract/wiki
- Asegúrate de agregar Tesseract al PATH

**El bot no inicia:**
1. Verifica que `.env` existe y tiene el token correcto
2. Revisa los logs en la carpeta `logs/`
3. Reinstala ejecutando `install.bat` nuevamente

### Linux

**Error: "Permission denied"**
```bash
chmod +x install.sh start.sh stop.sh run_background.sh
```

**El bot no inicia:**
```bash
# Ver logs
cat logs/bot_output.log

# Verificar procesos
ps aux | grep python

# Verificar que tesseract está instalado
tesseract --version
```

**Reinstalar Tesseract:**
```bash
sudo apt-get install --reinstall tesseract-ocr tesseract-ocr-spa
```

**Ver si el bot está corriendo:**
```bash
ps aux | grep "python.*main.py"
```

**OCR no funciona:**
1. Verifica Tesseract: `tesseract --version`
2. Verifica idioma español: `tesseract --list-langs | grep spa`
3. Instala el paquete español si falta: `sudo apt-get install tesseract-ocr-spa`

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

**Javier Gómez**

Creado con ❤️ para facilitar el control de viáticos empresariales

## 🙏 Agradecimientos

- python-telegram-bot por la excelente biblioteca
- Tesseract OCR por el motor de reconocimiento de texto
- Todos los que contribuyan al proyecto

---

**¿Preguntas o problemas?** Abre un issue en GitHub o contacta al administrador.
