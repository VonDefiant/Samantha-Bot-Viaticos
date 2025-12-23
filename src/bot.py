"""
Samantha - Bot de Telegram para Control de Viáticos
Lógica principal del bot con personalidad cálida y humana
"""

import os
import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

from .config import (
    TELEGRAM_TOKEN, TIPOS_GASTO, FACTURAS_FOLDER,
    TIPO_GASTO, PHOTO, CONFIRMAR, EDITAR_CAMPO, EDITAR_VALOR
)
from .database import Database
from .ocr import extraer_datos_factura
from .excel_export import generar_excel
from .utils import formatear_monto, truncar_texto, validar_monto

logger = logging.getLogger(__name__)


class SamanthaBot:
    """Bot de Viáticos Samantha"""

    def __init__(self):
        """Inicializar bot"""
        self.db = Database()
        logger.info("Bot Samantha inicializado")

    # ==================== COMANDOS BÁSICOS ====================

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start"""
        try:
            mensaje = (
                "¡Hola! 👋 Soy *Samantha*, tu asistente personal de viáticos 💼\n\n"
                "Estoy aquí para ayudarte a llevar un control ordenado de todas tus facturas. "
                "Solo envíame las fotos y yo me encargo del resto 📸✨\n\n"
                "*¿Qué puedo hacer por vos?*\n\n"
                "💵 /nueva - Registrar una nueva factura\n"
                "📊 /resumen - Ver cuánto has gastado\n"
                "📑 /lista - Ver tus facturas guardadas\n"
                "📥 /exportar - Generar tu Excel listo\n"
                "🗑️ /borrar - Eliminar una factura\n"
                "❓ /help - Si necesitas ayuda\n\n"
                "Cuando quieras agregar una factura, solo escribí */nueva* y yo te guío 😊"
            )
            await update.message.reply_text(mensaje, parse_mode='Markdown')
            logger.info(f"Usuario {update.effective_user.id} inició el bot")
        except Exception as e:
            logger.error(f"Error en comando /start: {e}", exc_info=True)
            await update.message.reply_text(
                "Ups! Hubo un error al iniciar. Por favor intenta de nuevo."
            )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /help"""
        try:
            mensaje = (
                "💡 *¿Cómo funciono?*\n\n"
                "Es súper fácil, mirá:\n\n"
                "1️⃣ Escribís /nueva y yo te pregunto qué tipo de gasto es\n"
                "2️⃣ Seleccionás si es Alimentación o Combustible\n"
                "3️⃣ Me enviás la foto de tu factura 📸\n"
                "4️⃣ Yo leo la factura y extraigo los datos automáticamente ✨\n"
                "5️⃣ Te muestro lo que encontré para que lo revises\n"
                "6️⃣ Si algo está mal, podés editarlo fácilmente\n"
                "7️⃣ Le das confirmar y ¡listo! Ya quedó guardado 🎉\n\n"
                "*Tips para mejores resultados:*\n"
                "• Tomá la foto con buena luz 💡\n"
                "• Que el texto se vea clarito\n"
                "• Evitá sombras y reflejos\n\n"
                "Cualquier cosa que necesites, acá estoy para ayudarte 😊"
            )
            await update.message.reply_text(mensaje, parse_mode='Markdown')
            logger.info(f"Usuario {update.effective_user.id} solicitó ayuda")
        except Exception as e:
            logger.error(f"Error en comando /help: {e}", exc_info=True)
            await update.message.reply_text("Error al mostrar ayuda. Intenta nuevamente.")

    # ==================== NUEVA FACTURA ====================

    async def nueva_factura(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Iniciar registro de nueva factura"""
        try:
            keyboard = [['🍔 ALIMENTACIÓN', '⛽ COMBUSTIBLE']]
            await update.message.reply_text(
                '¡Dale! Vamos a registrar tu factura 📝\n\n'
                'Primero contame, ¿qué tipo de gasto es?',
                reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
            )
            logger.info(f"Usuario {update.effective_user.id} inició nueva factura")
            return TIPO_GASTO
        except Exception as e:
            logger.error(f"Error al iniciar nueva factura: {e}", exc_info=True)
            await update.message.reply_text("Error al iniciar. Intenta /nueva nuevamente.")
            return ConversationHandler.END

    async def recibir_tipo_gasto(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Recibir tipo de gasto"""
        try:
            tipo = update.message.text.upper().replace('🍔 ', '').replace('⛽ ', '')

            if tipo not in TIPOS_GASTO:
                await update.message.reply_text(
                    'Mmm, no entendí bien 🤔\n'
                    'Por favor seleccioná una de las opciones: Alimentación o Combustible'
                )
                return TIPO_GASTO

            context.user_data['tipo_gasto'] = tipo
            logger.debug(f"Tipo de gasto seleccionado: {tipo}")

            await update.message.reply_text(
                f'Perfecto, es de *{tipo}* ✅\n\n'
                f'Ahora sí, enviame la foto de la factura 📸\n'
                f'Yo me encargo de leer todos los datos',
                reply_markup=ReplyKeyboardRemove(),
                parse_mode='Markdown'
            )
            return PHOTO
        except Exception as e:
            logger.error(f"Error al recibir tipo de gasto: {e}", exc_info=True)
            await update.message.reply_text("Error procesando tipo de gasto. Usa /cancelar e intenta de nuevo.")
            return ConversationHandler.END

    async def recibir_foto(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Recibir foto y procesar con OCR"""
        try:
            await update.message.reply_text('Recibido! 📸 Dejame analizar la factura...')

            # Crear carpeta si no existe
            os.makedirs(FACTURAS_FOLDER, exist_ok=True)

            # Guardar foto
            photo = update.message.photo[-1]
            file = await photo.get_file()
            filename = f"{FACTURAS_FOLDER}/factura_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            await file.download_to_drive(filename)

            context.user_data['foto_path'] = filename
            logger.info(f"Foto guardada: {filename}")

            # Extraer datos con OCR
            await update.message.reply_text('🔍 Extrayendo los datos...')
            datos = extraer_datos_factura(filename)

            if not datos:
                logger.warning(f"OCR falló para imagen: {filename}")
                await update.message.reply_text(
                    'Ay no... 😅 Tuve problemas para leer esta factura.\n\n'
                    'Podés intentar de nuevo con una foto más clara? '
                    'Asegurate que el texto se vea bien legible.\n\n'
                    'Usá /cancelar si querés empezar de nuevo.'
                )
                return ConversationHandler.END

            # Guardar datos extraídos
            context.user_data['datos_factura'] = datos

            # Formatear fecha actual
            fecha_hoy = datetime.now().strftime('%d/%m/%Y')
            context.user_data['datos_factura']['fecha'] = fecha_hoy

            # Mostrar datos extraídos
            return await self._mostrar_datos_extraidos(update, context, datos, fecha_hoy)

        except Exception as e:
            logger.error(f"Error al recibir foto: {e}", exc_info=True)
            await update.message.reply_text(
                "⚠️ Error al procesar la foto.\n"
                "Por favor intenta nuevamente o usa /cancelar para salir."
            )
            return ConversationHandler.END

    async def _mostrar_datos_extraidos(self, update, context, datos, fecha_hoy):
        """Mostrar datos extraídos al usuario"""
        try:
            # Verificar datos faltantes
            datos_faltantes = []
            if not datos['nit']:
                datos_faltantes.append('NIT')
            if not datos['serie']:
                datos_faltantes.append('Serie')
            if not datos['numero']:
                datos_faltantes.append('Número')
            if not datos['monto']:
                datos_faltantes.append('Monto')

            # Construir mensaje
            mensaje = "¡Listo! 🎉 Esto es lo que encontré:\n\n"
            mensaje += f"📅 *Fecha:* {fecha_hoy}\n"
            mensaje += f"🏢 *NIT Proveedor:* {datos['nit'] if datos['nit'] else '❌ No encontrado'}\n"
            mensaje += f"👤 *Proveedor:* {truncar_texto(datos['nombre'], 40) if datos['nombre'] else '❌ No encontrado'}\n"
            mensaje += f"🔢 *Serie:* {datos['serie'] if datos['serie'] else '❌ No encontrado'}\n"
            mensaje += f"📄 *Número:* {datos['numero'] if datos['numero'] else '❌ No encontrado'}\n"
            mensaje += f"💰 *Monto:* {formatear_monto(datos['monto']) if datos['monto'] else '❌ No encontrado'}\n"
            mensaje += f"🏷️ *Tipo:* {context.user_data['tipo_gasto']}\n\n"

            if datos_faltantes:
                mensaje += f"⚠️ No encontré: {', '.join(datos_faltantes)}\n"
                mensaje += "Pero no te preocupes, podés agregarlo vos después 😊\n\n"

            mensaje += "¿Todo bien o necesitás editar algo?"

            keyboard = [['✅ Confirmar', '✏️ Editar'], ['❌ Cancelar']]

            await update.message.reply_text(
                mensaje,
                reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
                parse_mode='Markdown'
            )

            return CONFIRMAR
        except Exception as e:
            logger.error(f"Error al mostrar datos extraídos: {e}", exc_info=True)
            raise

    async def confirmar_datos(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Confirmar o editar datos"""
        try:
            respuesta = update.message.text

            if respuesta == '❌ Cancelar':
                await update.message.reply_text(
                    'Ok, no hay problema! Operación cancelada 👍\n\n'
                    'Cuando quieras agregar una factura, solo escribí /nueva',
                    reply_markup=ReplyKeyboardRemove()
                )
                logger.info("Usuario canceló el registro de factura")
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
                    'Dale, ¿qué campo querés editar? 📝',
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return EDITAR_CAMPO

            elif respuesta == '✅ Confirmar':
                return await self.guardar_factura(update, context)

            return CONFIRMAR

        except Exception as e:
            logger.error(f"Error al confirmar datos: {e}", exc_info=True)
            await update.message.reply_text("Error al procesar confirmación.")
            return ConversationHandler.END

    async def editar_campo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Seleccionar campo a editar"""
        try:
            campo = update.message.text

            if campo == '✅ Listo, Guardar':
                return await self.guardar_factura(update, context)

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
                    f'Perfecto! El valor actual es:\n*{valor_actual}*\n\n'
                    f'Escribime el nuevo valor que querés:',
                    reply_markup=ReplyKeyboardRemove(),
                    parse_mode='Markdown'
                )
                return EDITAR_VALOR

            return EDITAR_CAMPO

        except Exception as e:
            logger.error(f"Error al editar campo: {e}", exc_info=True)
            await update.message.reply_text("Error al editar. Intenta nuevamente.")
            return EDITAR_CAMPO

    async def editar_valor(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Recibir nuevo valor del campo"""
        try:
            campo = context.user_data['campo_a_editar']
            nuevo_valor = update.message.text

            # Validar según el campo
            if campo == 'monto':
                try:
                    nuevo_valor = validar_monto(nuevo_valor)
                except ValueError:
                    await update.message.reply_text(
                        'Mmm, ese monto no me quedó claro 🤔\n'
                        'Intentá de nuevo, solo con números (ej: 150.50):'
                    )
                    return EDITAR_VALOR

            # Guardar nuevo valor
            if campo == 'tipo_gasto':
                if nuevo_valor.upper() not in TIPOS_GASTO:
                    await update.message.reply_text(
                        'Tiene que ser ALIMENTACIÓN o COMBUSTIBLE 😊\n'
                        'Intentá de nuevo:'
                    )
                    return EDITAR_VALOR
                context.user_data['tipo_gasto'] = nuevo_valor.upper()
            else:
                context.user_data['datos_factura'][campo] = nuevo_valor

            logger.debug(f"Campo {campo} actualizado a: {nuevo_valor}")

            # Volver al menú de edición
            keyboard = [
                ['📅 Fecha', '🏢 NIT'],
                ['👤 Nombre', '🔢 Serie'],
                ['📄 Número', '💰 Monto'],
                ['🏷️ Tipo de Gasto'],
                ['✅ Listo, Guardar']
            ]

            await update.message.reply_text(
                f'Listo! Ya lo actualicé ✨\n\n'
                f'¿Querés editar algo más o ya guardamos?',
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            return EDITAR_CAMPO

        except Exception as e:
            logger.error(f"Error al editar valor: {e}", exc_info=True)
            await update.message.reply_text("Error al guardar valor. Intenta nuevamente.")
            return EDITAR_VALOR

    async def guardar_factura(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Guardar factura en base de datos"""
        try:
            datos = context.user_data['datos_factura']
            tipo_gasto = context.user_data['tipo_gasto']
            foto = context.user_data['foto_path']

            # Insertar en base de datos
            factura_id = self.db.insertar_factura(
                fecha=datos.get('fecha'),
                nit=datos.get('nit'),
                nombre=datos.get('nombre'),
                serie=datos.get('serie'),
                numero=datos.get('numero'),
                tipo_gasto=tipo_gasto,
                monto=datos.get('monto'),
                foto_path=foto
            )

            logger.info(f"Factura #{factura_id} guardada exitosamente")

            await update.message.reply_text(
                f'¡Excelente! 🎉 Tu factura ya está guardada.\n\n'
                f'*Factura #{factura_id}*\n'
                f'📅 {datos.get("fecha")}\n'
                f'🏢 {datos.get("nit")}\n'
                f'👤 {truncar_texto(datos.get("nombre"), 30)}\n'
                f'💰 {formatear_monto(datos.get("monto"))}\n'
                f'🏷️ {tipo_gasto}\n\n'
                f'Cuando necesites tu Excel, solo escribí /exportar 📊',
                reply_markup=ReplyKeyboardRemove(),
                parse_mode='Markdown'
            )

            return ConversationHandler.END

        except Exception as e:
            logger.error(f"Error al guardar factura: {e}", exc_info=True)
            await update.message.reply_text(
                "⚠️ Error al guardar la factura en la base de datos.\n"
                "Por favor intenta nuevamente o contacta al administrador."
            )
            return ConversationHandler.END

    async def cancelar(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancelar operación"""
        await update.message.reply_text(
            'Ok! Operación cancelada 👌\n\n'
            'Cuando quieras, estoy aquí para ayudarte 😊',
            reply_markup=ReplyKeyboardRemove()
        )
        logger.info("Usuario canceló operación")
        return ConversationHandler.END

    # ==================== CONSULTAS ====================

    async def resumen(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ver resumen de gastos"""
        try:
            total, cantidad, por_tipo = self.db.obtener_resumen()

            if cantidad == 0:
                await update.message.reply_text(
                    'Todavía no tenés facturas guardadas 📭\n\n'
                    'Escribí /nueva para empezar a registrarlas!'
                )
                return

            mensaje = '📊 *Tu resumen de viáticos*\n\n'
            mensaje += f'💰 *Total gastado:* {formatear_monto(total)}\n'
            mensaje += f'📄 *Facturas registradas:* {cantidad}\n\n'

            if por_tipo:
                mensaje += '🏷️ *Desglose por tipo:*\n'
                for tipo, monto, cant in por_tipo:
                    emoji = '🍔' if tipo == 'ALIMENTACIÓN' else '⛽'
                    mensaje += f'{emoji} {tipo}: {formatear_monto(monto)} ({cant} facturas)\n'

            await update.message.reply_text(mensaje, parse_mode='Markdown')
            logger.info(f"Resumen solicitado: {cantidad} facturas, total {total}")

        except Exception as e:
            logger.error(f"Error al obtener resumen: {e}", exc_info=True)
            await update.message.reply_text("⚠️ Error al obtener resumen. Intenta nuevamente.")

    async def lista(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Listar todas las facturas"""
        try:
            facturas = self.db.obtener_facturas(limit=20)

            if not facturas:
                await update.message.reply_text(
                    'Aún no tenés facturas guardadas 📭\n\n'
                    'Escribí /nueva para agregar tu primera factura!'
                )
                return

            mensaje = '📋 *Tus últimas facturas*\n\n'
            for fac in facturas:
                emoji = '🍔' if fac[3] == 'ALIMENTACIÓN' else '⛽'
                nombre_corto = truncar_texto(fac[2], 25) if fac[2] else 'Sin nombre'
                mensaje += f'#{fac[0]} {emoji} | {fac[1]} | {nombre_corto} | {formatear_monto(fac[4])}\n'

            mensaje += f'\n💡 Para borrar alguna, usá: /borrar <número>'

            await update.message.reply_text(mensaje, parse_mode='Markdown')
            logger.info(f"Lista de facturas solicitada: {len(facturas)} facturas")

        except Exception as e:
            logger.error(f"Error al listar facturas: {e}", exc_info=True)
            await update.message.reply_text("⚠️ Error al obtener lista. Intenta nuevamente.")

    async def borrar(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Borrar factura"""
        try:
            factura_id = int(context.args[0]) if context.args else None

            if not factura_id:
                await update.message.reply_text(
                    'Necesito que me digas qué factura querés borrar 🤔\n\n'
                    '*Ejemplo:* /borrar 5\n\n'
                    'Usá /lista para ver los números de tus facturas.',
                    parse_mode='Markdown'
                )
                return

            eliminada = self.db.eliminar_factura(factura_id)

            if eliminada:
                await update.message.reply_text(
                    f'Listo! ✅ La factura #{factura_id} ya está eliminada.'
                )
                logger.info(f"Factura #{factura_id} eliminada")
            else:
                await update.message.reply_text(
                    f'Mmm... 🤔 No encontré ninguna factura con el número #{factura_id}\n\n'
                    f'Usá /lista para ver las facturas disponibles.'
                )

        except ValueError:
            await update.message.reply_text(
                'Ese número no es válido 😅\n\n'
                'Tiene que ser un número, por ejemplo: /borrar 5'
            )
        except Exception as e:
            logger.error(f"Error al borrar factura: {e}", exc_info=True)
            await update.message.reply_text("⚠️ Error al eliminar factura. Intenta nuevamente.")

    # ==================== EXPORTAR ====================

    async def exportar(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Exportar facturas a Excel"""
        try:
            await update.message.reply_text(
                'Dale! Ya estoy preparando tu Excel 📊\n'
                'Esto tomará solo unos segundos...'
            )

            facturas = self.db.obtener_todas_facturas()

            if not facturas:
                await update.message.reply_text(
                    'Todavía no tenés facturas para exportar 📭\n\n'
                    'Agregá algunas con /nueva y después volvé acá 😊'
                )
                return

            # Generar Excel
            filepath, filename = generar_excel(facturas)

            # Calcular total
            total = sum([f[5] for f in facturas if f[5]])

            # Enviar archivo
            with open(filepath, 'rb') as file:
                await update.message.reply_document(
                    document=file,
                    filename=filename,
                    caption=(
                        f'¡Listo! 🎉 Aquí está tu Excel\n\n'
                        f'📄 *{len(facturas)} facturas* registradas\n'
                        f'💰 *Total:* {formatear_monto(total)}\n\n'
                        f'Ya podés usarlo para tus reportes de viáticos 😊'
                    ),
                    parse_mode='Markdown'
                )

            logger.info(f"Excel exportado: {filename} con {len(facturas)} facturas")

        except Exception as e:
            logger.error(f"Error al exportar: {e}", exc_info=True)
            await update.message.reply_text(
                "⚠️ Error al generar el Excel.\n"
                "Por favor intenta nuevamente o contacta al administrador."
            )

    # ==================== SETUP ====================

    def setup_handlers(self, app: Application):
        """Configurar handlers del bot"""
        # ConversationHandler para nueva factura
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('nueva', self.nueva_factura)],
            states={
                TIPO_GASTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.recibir_tipo_gasto)],
                PHOTO: [MessageHandler(filters.PHOTO, self.recibir_foto)],
                CONFIRMAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.confirmar_datos)],
                EDITAR_CAMPO: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.editar_campo)],
                EDITAR_VALOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.editar_valor)]
            },
            fallbacks=[CommandHandler('cancelar', self.cancelar)]
        )

        # Agregar handlers
        app.add_handler(CommandHandler('start', self.start))
        app.add_handler(CommandHandler('help', self.help_command))
        app.add_handler(conv_handler)
        app.add_handler(CommandHandler('resumen', self.resumen))
        app.add_handler(CommandHandler('lista', self.lista))
        app.add_handler(CommandHandler('borrar', self.borrar))
        app.add_handler(CommandHandler('exportar', self.exportar))

        logger.info("Handlers configurados correctamente")

    def run(self):
        """Ejecutar el bot"""
        logger.info("=" * 60)
        logger.info("🤖 Samantha - Bot de Viáticos")
        logger.info("Iniciando bot...")
        logger.info("=" * 60)

        # Crear aplicación
        app = Application.builder().token(TELEGRAM_TOKEN).build()

        # Configurar handlers
        self.setup_handlers(app)

        # Iniciar bot
        logger.info("✨ Bot iniciado correctamente")
        logger.info("Presiona Ctrl+C para detener")

        app.run_polling()
