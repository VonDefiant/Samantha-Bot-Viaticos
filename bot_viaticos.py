#!/usr/bin/env python3
"""
Bot de Telegram para Control de Viáticos
Extrae datos de facturas usando OCR y exporta a Excel
"""

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import sqlite3
from datetime import datetime
import os
import re
import pytesseract
from PIL import Image
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment, Border, Side

# ==================== CONFIGURACIÓN ====================
TOKEN = 'TU_TOKEN_AQUI'  # Reemplazar con tu token de BotFather
NIT_EMPRESA = '71224556'  # NIT de Research & Planning Guatemala

# Estados de la conversación
TIPO_GASTO, PHOTO, CONFIRMAR, EDITAR_CAMPO, EDITAR_VALOR = range(5)

# ==================== BASE DE DATOS ====================
def init_db():
    """Inicializar base de datos SQLite"""
    conn = sqlite3.connect('viaticos.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS facturas
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  fecha TEXT,
                  nit_proveedor TEXT,
                  nombre_proveedor TEXT,
                  serie TEXT,
                  numero TEXT,
                  tipo_gasto TEXT,
                  monto REAL,
                  foto_path TEXT,
                  created_at TEXT)''')
    conn.commit()
    conn.close()

# ==================== FUNCIONES OCR ====================
def extraer_datos_factura(image_path):
    """
    Extrae datos de la factura usando OCR
    Returns: dict con nit, nombre, serie, numero, monto
    """
    try:
        # Abrir imagen y hacer OCR
        img = Image.open(image_path)
        texto = pytesseract.image_to_string(img, lang='spa')
        
        datos = {
            'nit': None,
            'nombre': None,
            'serie': None,
            'numero': None,
            'monto': None
        }
        
        lineas = texto.split('\n')
        
        # Buscar NIT del emisor (no debe ser el de la empresa)
        for i, linea in enumerate(lineas):
            # Buscar NIT seguido de números
            if 'NIT' in linea.upper():
                # Buscar números en la misma línea o líneas siguientes
                for j in range(i, min(i+3, len(lineas))):
                    numeros = re.findall(r'\d+', lineas[j])
                    for num in numeros:
                        if len(num) >= 6 and num != NIT_EMPRESA:
                            datos['nit'] = num
                            break
                    if datos['nit']:
                        # Buscar nombre del emisor en líneas cercanas
                        for k in range(max(0, i-2), min(i+5, len(lineas))):
                            if lineas[k].strip() and not re.match(r'^\d+$', lineas[k].strip()):
                                # Evitar líneas con solo números o muy cortas
                                if len(lineas[k].strip()) > 10 and 'NIT' not in lineas[k].upper():
                                    datos['nombre'] = lineas[k].strip()
                                    break
                        break
        
        # Buscar SERIE
        for linea in lineas:
            if 'SERIE' in linea.upper():
                # Buscar código alfanumérico después de SERIE
                match = re.search(r'SERIE[:\s]*([A-Z0-9]+)', linea.upper())
                if match:
                    datos['serie'] = match.group(1)
                else:
                    # Buscar en la siguiente línea
                    idx = lineas.index(linea)
                    if idx + 1 < len(lineas):
                        match = re.search(r'([A-Z0-9]{8,})', lineas[idx + 1].upper())
                        if match:
                            datos['serie'] = match.group(1)
        
        # Buscar NÚMERO de factura
        for linea in lineas:
            if 'NUMERO' in linea.upper() or 'NÚMERO' in linea.upper():
                # Buscar número después de NUMERO
                match = re.search(r'N[UÚ]MERO[:\s]*(\d+)', linea.upper())
                if match:
                    datos['numero'] = match.group(1)
                else:
                    # Buscar en la siguiente línea
                    idx = lineas.index(linea)
                    if idx + 1 < len(lineas):
                        numeros = re.findall(r'\d{6,}', lineas[idx + 1])
                        if numeros:
                            datos['numero'] = numeros[0]
        
        # Buscar MONTO (buscar TOTAL y Q)
        for linea in lineas:
            if 'TOTAL' in linea.upper() and 'Q' in linea:
                # Buscar patrón Q seguido de números
                match = re.search(r'Q\s*[\d,]+\.?\d*', linea)
                if match:
                    monto_str = match.group().replace('Q', '').replace(',', '').replace(' ', '')
                    try:
                        datos['monto'] = float(monto_str)
                    except:
                        pass
        
        # Si no encontró monto, buscar cualquier cantidad con Q
        if not datos['monto']:
            for linea in reversed(lineas):
                if 'Q' in linea:
                    match = re.search(r'Q\s*(\d+[\.,]?\d*)', linea)
                    if match:
                        try:
                            monto_str = match.group(1).replace(',', '.')
                            datos['monto'] = float(monto_str)
                            break
                        except:
                            pass
        
        return datos
        
    except Exception as e:
        print(f"Error en OCR: {e}")
        return None

# ==================== COMANDOS DEL BOT ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    mensaje = (
        "¡Hola! Soy *Samantha* 👋😊\n\n"
        "Estoy aquí para ayudarte a llevar el control de tus viáticos de forma súper fácil. "
        "Solo necesito que me envíes las fotos de tus facturas y yo me encargo del resto.\n\n"
        "🌟 *¿Qué puedo hacer por vos?*\n\n"
        "💵 /nueva - Registrar una nueva factura\n"
        "📊 /resumen - Ver cuánto has gastado\n"
        "📁 /exportar - Crear tu reporte en Excel\n"
        "📋 /lista - Ver tus facturas guardadas\n"
        "🗑️ /borrar - Eliminar una factura\n"
        "❓ /help - Si necesitás ayuda\n\n"
        "¿Listo para empezar? ¡Mandame /nueva y registremos tu primera factura! 🚀"
    )
    await update.message.reply_text(mensaje, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /help"""
    mensaje = (
        "📖 *¿Cómo te puedo ayudar?*\n\n"
        "Mirá, es bien sencillo:\n\n"
        "1️⃣ Mandame /nueva cuando quieras registrar una factura\n"
        "2️⃣ Yo te pregunto si es de *Alimentación* o *Combustible*\n"
        "3️⃣ Me enviás la foto de la factura 📸\n"
        "4️⃣ Yo leo todos los datos automáticamente (magia de tecnología ✨)\n"
        "5️⃣ Te muestro lo que encontré para que lo revises\n"
        "6️⃣ Si todo está bien, confirmás. Si algo está mal, lo editamos juntos\n"
        "7️⃣ ¡Y listo! Cuando quieras, /exportar y te mando tu Excel 📊\n\n"
        "💡 *Tip importante:* El NIT debe ser del proveedor (la gasolinera, el restaurante, etc.), "
        "no el de tu empresa. Pero no te preocupes, yo filtro automáticamente el 71224556.\n\n"
        "¿Alguna duda? ¡Preguntame lo que sea! 😊"
    )
    await update.message.reply_text(mensaje, parse_mode='Markdown')

# ==================== NUEVA FACTURA ====================
async def nueva_factura(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Iniciar registro de nueva factura"""
    keyboard = [['ALIMENTACIÓN', 'COMBUSTIBLE']]
    
    await update.message.reply_text(
        '¡Perfecto! Vamos a registrar tu factura 😊\n\n'
        '¿De qué tipo es este gasto?',
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return TIPO_GASTO

async def recibir_tipo_gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibir tipo de gasto"""
    tipo = update.message.text.upper()
    
    if tipo not in ['ALIMENTACIÓN', 'COMBUSTIBLE']:
        await update.message.reply_text(
            'Mmm, creo que no entendí bien 😅\n'
            'Por favor seleccioná *ALIMENTACIÓN* o *COMBUSTIBLE*',
            parse_mode='Markdown'
        )
        return TIPO_GASTO
    
    context.user_data['tipo_gasto'] = tipo
    
    await update.message.reply_text(
        f'¡Entendido! Es un gasto de *{tipo}* ✅\n\n'
        f'Ahora mandame una foto clara de la factura 📸\n'
        f'_(Con buena luz sale mejor, eh)_ 😉',
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='Markdown'
    )
    return PHOTO

async def recibir_foto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibir foto y procesar con OCR"""
    await update.message.reply_text('¡Foto recibida! 📸 Déjame leer los datos... ⏳')
    
    # Crear carpeta si no existe
    os.makedirs('facturas', exist_ok=True)
    
    # Guardar foto
    photo = update.message.photo[-1]
    file = await photo.get_file()
    filename = f"facturas/factura_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    await file.download_to_drive(filename)
    
    context.user_data['foto_path'] = filename
    
    # Extraer datos con OCR
    datos = extraer_datos_factura(filename)
    
    if not datos:
        await update.message.reply_text(
            'Uy, no pude leer bien la factura 😔\n\n'
            'Puede ser que la foto esté muy borrosa o con poca luz.\n'
            '¿Podrías intentar de nuevo con mejor iluminación?\n\n'
            'Usa /cancelar si preferís dejarlo para después.'
        )
        return ConversationHandler.END
    
    # Guardar datos extraídos
    context.user_data['datos_factura'] = datos
    
    # Formatear fecha actual
    fecha_hoy = datetime.now().strftime('%d/%m/%Y')
    context.user_data['datos_factura']['fecha'] = fecha_hoy
    
    # Mostrar datos extraídos
    mensaje = "¡Listo! Esto es lo que encontré: 🔍\n\n"
    mensaje += f"📅 *Fecha:* {fecha_hoy}\n"
    mensaje += f"🏢 *NIT Proveedor:* {datos['nit'] or '❓ No encontrado'}\n"
    mensaje += f"👤 *Nombre:* {datos['nombre'] or '❓ No encontrado'}\n"
    mensaje += f"🔢 *Serie:* {datos['serie'] or '❓ No encontrado'}\n"
    mensaje += f"📄 *Número:* {datos['numero'] or '❓ No encontrado'}\n"
    mensaje += f"💰 *Monto:* Q{datos['monto'] if datos['monto'] else '❓ No encontrado'}\n"
    mensaje += f"🏷️ *Tipo:* {context.user_data['tipo_gasto']}\n\n"
    mensaje += "¿Todo correcto? Si algo está mal, podemos editarlo 😊"
    
    keyboard = [['✅ Confirmar', '✏️ Editar', '❌ Cancelar']]
    
    await update.message.reply_text(
        mensaje,
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
        parse_mode='Markdown'
    )
    
    return CONFIRMAR

async def confirmar_datos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirmar o editar datos"""
    respuesta = update.message.text
    
    if respuesta == '❌ Cancelar':
        await update.message.reply_text(
            'No hay problema, lo dejamos para después 👌\n'
            'Cuando quieras registrar una factura, solo mandame /nueva',
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    elif respuesta == '✏️ Editar':
        keyboard = [
            ['📅 Fecha', '🏢 NIT'],
            ['👤 Nombre', '🔢 Serie'],
            ['📄 Número', '💰 Monto'],
            ['🏷️ Tipo de Gasto'],
            ['✅ Listo, Guardar']
        ]
        
        await update.message.reply_text(
            '¡Dale! ¿Qué campo querés corregir? 🔧',
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return EDITAR_CAMPO
    
    elif respuesta == '✅ Confirmar':
        # Guardar en base de datos
        return await guardar_factura(update, context)
    
    return CONFIRMAR

async def editar_campo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Seleccionar campo a editar"""
    campo = update.message.text
    
    if campo == '✅ Listo, Guardar':
        return await guardar_factura(update, context)
    
    # Mapeo de campos
    mapeo = {
        '📅 Fecha': 'fecha',
        '🏢 NIT': 'nit',
        '👤 Nombre': 'nombre',
        '🔢 Serie': 'serie',
        '📄 Número': 'numero',
        '💰 Monto': 'monto',
        '🏷️ Tipo de Gasto': 'tipo_gasto'
    }
    
    if campo in mapeo:
        context.user_data['campo_a_editar'] = mapeo[campo]
        
        valor_actual = (context.user_data['datos_factura'].get(mapeo[campo]) 
                       if mapeo[campo] != 'tipo_gasto' 
                       else context.user_data.get('tipo_gasto'))
        
        await update.message.reply_text(
            f'Perfecto, vamos a corregir este campo ✏️\n\n'
            f'Valor actual: *{valor_actual}*\n\n'
            f'Mandame el valor correcto:',
            reply_markup=ReplyKeyboardRemove(),
            parse_mode='Markdown'
        )
        return EDITAR_VALOR
    
    return EDITAR_CAMPO

async def editar_valor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibir nuevo valor del campo"""
    campo = context.user_data['campo_a_editar']
    nuevo_valor = update.message.text
    
    # Validar según el campo
    if campo == 'monto':
        try:
            nuevo_valor = float(nuevo_valor.replace('Q', '').replace(',', '').strip())
        except:
            await update.message.reply_text(
                'Mmm, ese monto no me cuadra 🤔\n'
                'Mandame solo números, por ejemplo: 150.50'
            )
            return EDITAR_VALOR
    
    # Guardar nuevo valor
    if campo == 'tipo_gasto':
        if nuevo_valor.upper() not in ['ALIMENTACIÓN', 'COMBUSTIBLE']:
            await update.message.reply_text(
                'Uy, ese tipo de gasto no lo reconozco 😅\n'
                'Debe ser *ALIMENTACIÓN* o *COMBUSTIBLE*',
                parse_mode='Markdown'
            )
            return EDITAR_VALOR
        context.user_data['tipo_gasto'] = nuevo_valor.upper()
    else:
        context.user_data['datos_factura'][campo] = nuevo_valor
    
    # Volver al menú de edición
    keyboard = [
        ['📅 Fecha', '🏢 NIT'],
        ['👤 Nombre', '🔢 Serie'],
        ['📄 Número', '💰 Monto'],
        ['🏷️ Tipo de Gasto'],
        ['✅ Listo, Guardar']
    ]
    
    await update.message.reply_text(
        f'¡Listo! Campo actualizado correctamente ✅\n\n'
        f'¿Querés editar algo más o guardamos así?',
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return EDITAR_CAMPO

async def guardar_factura(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Guardar factura en base de datos"""
    datos = context.user_data['datos_factura']
    tipo_gasto = context.user_data['tipo_gasto']
    foto = context.user_data['foto_path']
    
    conn = sqlite3.connect('viaticos.db')
    c = conn.cursor()
    c.execute('''INSERT INTO facturas 
                 (fecha, nit_proveedor, nombre_proveedor, serie, numero, tipo_gasto, monto, foto_path, created_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (datos.get('fecha'),
               datos.get('nit'),
               datos.get('nombre'),
               datos.get('serie'),
               datos.get('numero'),
               tipo_gasto,
               datos.get('monto'),
               foto,
               datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    factura_id = c.lastrowid
    conn.close()
    
    await update.message.reply_text(
        f'¡Excelente! Factura *#{factura_id}* guardada con éxito 🎉\n\n'
        f'📅 {datos.get("fecha")}\n'
        f'🏢 NIT: {datos.get("nit")}\n'
        f'👤 {datos.get("nombre")}\n'
        f'💰 Q{datos.get("monto")}\n'
        f'🏷️ {tipo_gasto}\n\n'
        f'Ya está todo registrado. ¿Querés agregar otra factura? Solo mandame /nueva 😊',
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='Markdown'
    )
    
    return ConversationHandler.END

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancelar operación"""
    await update.message.reply_text(
        'Okay, no hay problema 👌\n'
        'Cuando quieras volver a intentar, solo mandame /nueva',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# ==================== CONSULTAS ====================
async def resumen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ver resumen de gastos"""
    conn = sqlite3.connect('viaticos.db')
    c = conn.cursor()
    
    # Total general
    c.execute('SELECT SUM(monto), COUNT(*) FROM facturas')
    total, cantidad = c.fetchone()
    total = total or 0
    cantidad = cantidad or 0
    
    # Por tipo de gasto
    c.execute('SELECT tipo_gasto, SUM(monto), COUNT(*) FROM facturas GROUP BY tipo_gasto')
    por_tipo = c.fetchall()
    
    conn.close()
    
    if cantidad == 0:
        await update.message.reply_text(
            'Todavía no tenés facturas registradas 📭\n\n'
            '¡Empecemos! Mandame /nueva para agregar tu primera factura 🚀'
        )
        return
    
    mensaje = '📊 *Resumen de tus Viáticos*\n\n'
    mensaje += f'Has gastado un total de: *Q{total:.2f}*\n'
    mensaje += f'Facturas registradas: *{cantidad}*\n\n'
    mensaje += '💸 *Desglose por categoría:*\n'
    
    for tipo, monto, cant in por_tipo:
        emoji = '🍔' if tipo == 'ALIMENTACIÓN' else '⛽'
        mensaje += f'{emoji} {tipo}: Q{monto:.2f} ({cant} facturas)\n'
    
    mensaje += '\n_¿Querés el reporte completo? Usa /exportar_ 📄'
    
    await update.message.reply_text(mensaje, parse_mode='Markdown')

async def lista(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Listar todas las facturas"""
    conn = sqlite3.connect('viaticos.db')
    c = conn.cursor()
    c.execute('SELECT id, fecha, nombre_proveedor, tipo_gasto, monto FROM facturas ORDER BY id DESC LIMIT 20')
    facturas = c.fetchall()
    conn.close()
    
    if not facturas:
        await update.message.reply_text(
            'Aún no tenés facturas guardadas 📭\n\n'
            'Cuando registres una con /nueva, la vas a ver acá listada 😊'
        )
        return
    
    mensaje = '📋 *Tus últimas facturas:*\n\n'
    for fac in facturas:
        emoji = '🍔' if fac[3] == 'ALIMENTACIÓN' else '⛽'
        nombre_corto = fac[2][:25] + '...' if len(fac[2]) > 25 else fac[2]
        mensaje += f'{emoji} *#{fac[0]}* - {fac[1]}\n'
        mensaje += f'   {nombre_corto}\n'
        mensaje += f'   Q{fac[4]:.2f}\n\n'
    
    mensaje += '_Para eliminar una factura: /borrar <número>_\n'
    mensaje += '_Ejemplo: /borrar 5_'
    
    await update.message.reply_text(mensaje, parse_mode='Markdown')

async def borrar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Borrar factura"""
    try:
        # Obtener ID del comando
        factura_id = int(context.args[0]) if context.args else None
        
        if not factura_id:
            await update.message.reply_text(
                'Para borrar una factura necesito que me digas cuál 🤔\n\n'
                '*Uso:* /borrar <número>\n'
                '*Ejemplo:* /borrar 5\n\n'
                'Usá /lista para ver los números de tus facturas',
                parse_mode='Markdown'
            )
            return
        
        conn = sqlite3.connect('viaticos.db')
        c = conn.cursor()
        c.execute('DELETE FROM facturas WHERE id = ?', (factura_id,))
        conn.commit()
        
        if c.rowcount > 0:
            await update.message.reply_text(
                f'Listo, factura *#{factura_id}* eliminada ✅\n\n'
                '_(No te preocupes, siempre podés agregar más)_ 😊',
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f'Mmm, no encontré ninguna factura con el número *#{factura_id}* 🤔\n\n'
                'Usá /lista para ver tus facturas guardadas',
                parse_mode='Markdown'
            )
        
        conn.close()
        
    except ValueError:
        await update.message.reply_text(
            'Uy, ese número no es válido 😅\n\n'
            'El número debe ser solo dígitos, ejemplo: /borrar 5'
        )

# ==================== EXPORTAR A EXCEL ====================
async def exportar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Exportar facturas a Excel con el formato correcto"""
    await update.message.reply_text('Dale, dame un segundito que te preparo el Excel... 📊✨')
    
    conn = sqlite3.connect('viaticos.db')
    c = conn.cursor()
    c.execute('''SELECT fecha, nit_proveedor, serie, numero, tipo_gasto, monto 
                 FROM facturas ORDER BY fecha''')
    facturas = c.fetchall()
    conn.close()
    
    if not facturas:
        await update.message.reply_text(
            'Todavía no tenés facturas para exportar 📭\n\n'
            'Cuando agregues algunas con /nueva, acá vas a poder generar tu Excel 😊'
        )
        return
    
    # Crear Excel con pandas
    df = pd.DataFrame(facturas, columns=[
        'FECHA', 'NIT PROVEEDOR', 'SERIE', 'No. COMPROBANTE', 'TIPO DE GASTO', 'MONTO Q.'
    ])
    
    # Calcular número del mes actual
    mes_actual = datetime.now().month
    anio_actual = datetime.now().year
    
    filename = f'viaticos_{mes_actual}_{anio_actual}.xlsx'
    filepath = os.path.join('facturas', filename)
    
    # Guardar Excel
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        # Escribir DataFrame empezando en fila 7 (como en tu plantilla)
        df.to_excel(writer, sheet_name='Sheet1', startrow=6, index=False)
        
        # Obtener workbook y sheet
        workbook = writer.book
        sheet = writer.sheets['Sheet1']
        
        # Agregar encabezados de la plantilla
        sheet['G2'] = 'PROYECTO :'
        sheet['G3'] = 'NOMBRE SUPERVISOR'
        sheet['G4'] = 'CODIGO MAESTRO'
        sheet['G5'] = 'PUESTO'
        sheet['H5'] = 'SUPERVISOR JR'
        sheet['G6'] = 'MES'
        sheet['H6'] = datetime.now().strftime('%B').upper()
        sheet['I6'] = 'FECHA'
        sheet['J6'] = datetime.now().strftime('%Y-%m-%d')
        
        # Formatear headers (fila 7)
        header_font = Font(bold=True)
        header_alignment = Alignment(horizontal='center', vertical='center')
        
        for cell in sheet[7]:
            cell.font = header_font
            cell.alignment = header_alignment
        
        # Ajustar anchos de columna
        sheet.column_dimensions['A'].width = 8
        sheet.column_dimensions['B'].width = 12
        sheet.column_dimensions['C'].width = 12
        sheet.column_dimensions['D'].width = 18
        sheet.column_dimensions['E'].width = 15
        sheet.column_dimensions['F'].width = 18
        sheet.column_dimensions['G'].width = 18
        sheet.column_dimensions['H'].width = 12
        
        # Agregar numeración en columna A
        for idx, row in enumerate(range(8, 8 + len(df)), start=1):
            sheet[f'A{row}'] = idx
    
    # Enviar archivo
    await update.message.reply_document(
        document=open(filepath, 'rb'),
        filename=filename,
        caption=f'¡Aquí está! 🎉\n\n'
                f'Tu reporte con *{len(facturas)} facturas* listo para usar.\n'
                f'Ya lo podés abrir en Excel y es tuyo 😊',
        parse_mode='Markdown'
    )

# ==================== MAIN ====================
def main():
    """Función principal"""
    # Inicializar base de datos
    init_db()
    
    # Crear aplicación
    app = Application.builder().token(TOKEN).build()
    
    # ConversationHandler para nueva factura
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('nueva', nueva_factura)],
        states={
            TIPO_GASTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_tipo_gasto)],
            PHOTO: [MessageHandler(filters.PHOTO, recibir_foto)],
            CONFIRMAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirmar_datos)],
            EDITAR_CAMPO: [MessageHandler(filters.TEXT & ~filters.COMMAND, editar_campo)],
            EDITAR_VALOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, editar_valor)]
        },
        fallbacks=[CommandHandler('cancelar', cancelar)]
    )
    
    # Agregar handlers
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler('resumen', resumen))
    app.add_handler(CommandHandler('lista', lista))
    app.add_handler(CommandHandler('borrar', borrar))
    app.add_handler(CommandHandler('exportar', exportar))
    
    # Iniciar bot
    print('✨ Samantha está lista para ayudarte con tus viáticos!')
    print('Presiona Ctrl+C para detener')
    app.run_polling()

if __name__ == '__main__':
    main()
