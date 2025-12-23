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
    TIPO_GASTO, PHOTO, CONFIRMAR, EDITAR_CAMPO, EDITAR_VALOR, BORRAR_ID
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
        """Comando /start - Menú principal con botones"""
        try:
            mensaje = (
                "¡Hola! 👋 Soy *Samantha*, tu asistente personal de viáticos 💼\n\n"
                "Estoy aquí para ayudarte a llevar un control ordenado de todas tus facturas. "
                "Solo envíame las fotos y yo me encargo del resto 📸✨\n\n"
                "*¿Qué quieres hacer?*\n"
                "Selecciona una opción del menú:"
            )

            # Menú principal con botones
            keyboard = [
                ['📝 Nueva Factura', '📊 Resumen'],
                ['📋 Ver Lista', '📥 Exportar Excel'],
                ['🗑️ Borrar Factura', '❓ Ayuda']
            ]

            await update.message.reply_text(
                mensaje,
                parse_mode='Markdown',
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
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
                "Es súper fácil, mira:\n\n"
                "1️⃣ Presionas *Nueva Factura* y yo te pregunto qué tipo de gasto es\n"
                "2️⃣ Seleccionas si es Alimentación o Combustible\n"
                "3️⃣ Me envías la foto de tu factura 📸\n"
                "4️⃣ Yo leo la factura y extraigo los datos automáticamente ✨\n"
                "5️⃣ Te muestro lo que encontré para que lo revises\n"
                "6️⃣ Si algo está mal, puedes editarlo fácilmente\n"
                "7️⃣ Le das confirmar y ¡listo! Ya quedó guardado 🎉\n\n"
                "*Tips para mejores resultados:*\n"
                "• Toma la foto con buena luz 💡\n"
                "• Que el texto se vea clarito\n"
                "• Evita sombras y reflejos\n\n"
                "Cualquier cosa que necesites, aquí estoy para ayudarte 😊"
            )

            # Botón para volver al menú
            keyboard = [['🏠 Menú Principal']]

            await update.message.reply_text(
                mensaje,
                parse_mode='Markdown',
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            logger.info(f"Usuario {update.effective_user.id} solicitó ayuda")
        except Exception as e:
            logger.error(f"Error en comando /help: {e}", exc_info=True)
            await update.message.reply_text("Error al mostrar ayuda. Intenta nuevamente.")

    # ==================== NUEVA FACTURA ====================

    async def nueva_factura(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Iniciar registro de nueva factura"""
        try:
            keyboard = [['🍔 ALIMENTACIÓN', '⛽ COMBUSTIBLE'], ['❌ Cancelar']]
            await update.message.reply_text(
                '¡Perfecto! Vamos a registrar tu factura 📝\n\n'
                'Primero dime, ¿qué tipo de gasto es?',
                reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
            )
            logger.info(f"Usuario {update.effective_user.id} inició nueva factura")
            return TIPO_GASTO
        except Exception as e:
            logger.error(f"Error al iniciar nueva factura: {e}", exc_info=True)
            await update.message.reply_text("Error al iniciar. Intenta nuevamente desde el menú.")
            return ConversationHandler.END

    async def recibir_tipo_gasto(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Recibir tipo de gasto"""
        try:
            tipo = update.message.text.upper().replace('🍔 ', '').replace('⛽ ', '')

            # Verificar si es cancelar
            if tipo == 'CANCELAR':
                return await self.cancelar(update, context)

            if tipo not in TIPOS_GASTO:
                keyboard = [['🍔 ALIMENTACIÓN', '⛽ COMBUSTIBLE'], ['❌ Cancelar']]
                await update.message.reply_text(
                    'Mmm, no entendí bien 🤔\n'
                    'Por favor selecciona una de las opciones: Alimentación o Combustible',
                    reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
                )
                return TIPO_GASTO

            context.user_data['tipo_gasto'] = tipo
            logger.debug(f"Tipo de gasto seleccionado: {tipo}")

            await update.message.reply_text(
                f'Perfecto, es de *{tipo}* ✅\n\n'
                f'Ahora sí, envíame la foto de la factura 📸\n'
                f'Yo me encargo de leer todos los datos',
                reply_markup=ReplyKeyboardRemove(),
                parse_mode='Markdown'
            )
            return PHOTO
        except Exception as e:
            logger.error(f"Error al recibir tipo de gasto: {e}", exc_info=True)
            await update.message.reply_text("Error procesando tipo de gasto. Intenta de nuevo desde el menú.")
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
                keyboard = [['🔄 Intentar de nuevo', '❌ Cancelar']]
                await update.message.reply_text(
                    'Ay no... 😅 Tuve problemas para leer esta factura.\n\n'
                    '¿Puedes intentar de nuevo con una foto más clara? '
                    'Asegúrate que el texto se vea bien legible.',
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
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
                mensaje += "Pero no te preocupes, puedes agregarlo tú después 😊\n\n"

            mensaje += "¿Todo bien o necesitas hacer algo?"

            keyboard = [
                ['✅ Aceptar', '📸 Reintentar Foto'],
                ['✏️ Editar', '❌ Cancelar']
            ]

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
                return await self.cancelar(update, context)

            elif respuesta == '📸 Reintentar Foto':
                await update.message.reply_text(
                    'Ok! Envíame una nueva foto de la factura 📸\n'
                    'Intenta que tenga buena iluminación y que el texto se vea claro 💡',
                    reply_markup=ReplyKeyboardRemove()
                )
                return PHOTO

            elif respuesta == '✏️ Editar':
                keyboard = [
                    ['📅 Fecha', '🏢 NIT'],
                    ['👤 Nombre', '🔢 Serie'],
                    ['📄 Número', '💰 Monto'],
                    ['🏷️ Tipo de Gasto'],
                    ['✅ Listo, Guardar']
                ]
                await update.message.reply_text(
                    'Dale, ¿qué campo quieres editar? 📝',
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return EDITAR_CAMPO

            elif respuesta == '✅ Aceptar':
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
                    f'Escríbeme el nuevo valor que quieres:',
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
                        'Intenta de nuevo, solo con números (ej: 150.50):'
                    )
                    return EDITAR_VALOR

            # Guardar nuevo valor
            if campo == 'tipo_gasto':
                if nuevo_valor.upper() not in TIPOS_GASTO:
                    await update.message.reply_text(
                        'Tiene que ser ALIMENTACIÓN o COMBUSTIBLE 😊\n'
                        'Intenta de nuevo:'
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
                f'¿Quieres editar algo más o ya guardamos?',
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

            # Menú principal de nuevo
            keyboard = [
                ['📝 Nueva Factura', '📊 Resumen'],
                ['📋 Ver Lista', '📥 Exportar Excel'],
                ['🗑️ Borrar Factura', '❓ Ayuda']
            ]

            await update.message.reply_text(
                f'¡Excelente! 🎉 Tu factura ya está guardada.\n\n'
                f'*Factura #{factura_id}*\n'
                f'📅 {datos.get("fecha")}\n'
                f'🏢 {datos.get("nit")}\n'
                f'👤 {truncar_texto(datos.get("nombre"), 30)}\n'
                f'💰 {formatear_monto(datos.get("monto"))}\n'
                f'🏷️ {tipo_gasto}\n\n'
                f'¿Qué quieres hacer ahora?',
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
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
        # Menú principal
        keyboard = [
            ['📝 Nueva Factura', '📊 Resumen'],
            ['📋 Ver Lista', '📥 Exportar Excel'],
            ['🗑️ Borrar Factura', '❓ Ayuda']
        ]

        await update.message.reply_text(
            'Ok! Operación cancelada 👌\n\n'
            'Cuando quieras, estoy aquí para ayudarte 😊',
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        logger.info("Usuario canceló operación")
        return ConversationHandler.END

    # ==================== CONSULTAS ====================

    async def resumen(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ver resumen de gastos"""
        try:
            total, cantidad, por_tipo = self.db.obtener_resumen()

            # Menú principal
            keyboard = [
                ['📝 Nueva Factura', '📊 Resumen'],
                ['📋 Ver Lista', '📥 Exportar Excel'],
                ['🗑️ Borrar Factura', '❓ Ayuda']
            ]

            if cantidad == 0:
                await update.message.reply_text(
                    'Todavía no tienes facturas guardadas 📭\n\n'
                    'Presiona *Nueva Factura* para empezar a registrarlas!',
                    parse_mode='Markdown',
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
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

            await update.message.reply_text(
                mensaje,
                parse_mode='Markdown',
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            logger.info(f"Resumen solicitado: {cantidad} facturas, total {total}")

        except Exception as e:
            logger.error(f"Error al obtener resumen: {e}", exc_info=True)
            await update.message.reply_text("⚠️ Error al obtener resumen. Intenta nuevamente.")

    async def lista(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Listar todas las facturas"""
        try:
            facturas = self.db.obtener_facturas(limit=20)

            # Menú principal
            keyboard = [
                ['📝 Nueva Factura', '📊 Resumen'],
                ['📋 Ver Lista', '📥 Exportar Excel'],
                ['🗑️ Borrar Factura', '❓ Ayuda']
            ]

            if not facturas:
                await update.message.reply_text(
                    'Aún no tienes facturas guardadas 📭\n\n'
                    'Presiona *Nueva Factura* para agregar tu primera factura!',
                    parse_mode='Markdown',
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return

            mensaje = '📋 *Tus últimas facturas*\n\n'
            for fac in facturas:
                emoji = '🍔' if fac[3] == 'ALIMENTACIÓN' else '⛽'
                nombre_corto = truncar_texto(fac[2], 25) if fac[2] else 'Sin nombre'
                mensaje += f'#{fac[0]} {emoji} | {fac[1]} | {nombre_corto} | {formatear_monto(fac[4])}\n'

            mensaje += f'\n💡 Para borrar alguna, usa *Borrar Factura* y escribe el número'

            await update.message.reply_text(
                mensaje,
                parse_mode='Markdown',
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            logger.info(f"Lista de facturas solicitada: {len(facturas)} facturas")

        except Exception as e:
            logger.error(f"Error al listar facturas: {e}", exc_info=True)
            await update.message.reply_text("⚠️ Error al obtener lista. Intenta nuevamente.")

    async def borrar(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Iniciar proceso de borrar factura"""
        try:
            # Botón para cancelar
            keyboard = [['❌ Cancelar']]

            await update.message.reply_text(
                'Perfecto! Vamos a borrar una factura 🗑️\n\n'
                'Escribe el *número de la factura* que quieres eliminar\n\n'
                '💡 Puedes usar *Ver Lista* primero para ver los números de tus facturas.',
                parse_mode='Markdown',
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            logger.info(f"Usuario {update.effective_user.id} inició proceso de borrado")
            return BORRAR_ID

        except Exception as e:
            logger.error(f"Error al iniciar borrado: {e}", exc_info=True)
            await update.message.reply_text("Error al iniciar. Intenta nuevamente desde el menú.")
            return ConversationHandler.END

    async def borrar_recibir_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Recibir ID de factura a borrar"""
        try:
            # Menú principal
            keyboard = [
                ['📝 Nueva Factura', '📊 Resumen'],
                ['📋 Ver Lista', '📥 Exportar Excel'],
                ['🗑️ Borrar Factura', '❓ Ayuda']
            ]

            # Verificar si canceló
            if update.message.text == '❌ Cancelar':
                await update.message.reply_text(
                    'Ok! Operación cancelada 👌\n\n'
                    'No se eliminó ninguna factura.',
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return ConversationHandler.END

            # Intentar convertir a número
            try:
                factura_id = int(update.message.text.strip())
            except ValueError:
                await update.message.reply_text(
                    'Ese número no es válido 😅\n\n'
                    'Tiene que ser un número, por ejemplo: 5\n\n'
                    'Inténtalo de nuevo o presiona *Cancelar*:',
                    parse_mode='Markdown'
                )
                return BORRAR_ID

            # Intentar eliminar
            eliminada = self.db.eliminar_factura(factura_id)

            if eliminada:
                await update.message.reply_text(
                    f'Listo! ✅ La factura #{factura_id} ya está eliminada.',
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                logger.info(f"Factura #{factura_id} eliminada exitosamente")
            else:
                await update.message.reply_text(
                    f'Mmm... 🤔 No encontré ninguna factura con el número #{factura_id}\n\n'
                    f'Usa *Ver Lista* para ver las facturas disponibles.',
                    parse_mode='Markdown',
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )

            return ConversationHandler.END

        except Exception as e:
            logger.error(f"Error al borrar factura: {e}", exc_info=True)
            await update.message.reply_text(
                "⚠️ Error al eliminar factura. Intenta nuevamente desde el menú.",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            return ConversationHandler.END

    # ==================== EXPORTAR ====================

    async def exportar(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Exportar facturas a Excel"""
        try:
            await update.message.reply_text(
                'Dale! Ya estoy preparando tu Excel 📊\n'
                'Esto tomará solo unos segundos...'
            )

            facturas = self.db.obtener_todas_facturas()

            # Menú principal
            keyboard = [
                ['📝 Nueva Factura', '📊 Resumen'],
                ['📋 Ver Lista', '📥 Exportar Excel'],
                ['🗑️ Borrar Factura', '❓ Ayuda']
            ]

            if not facturas:
                await update.message.reply_text(
                    'Todavía no tienes facturas para exportar 📭\n\n'
                    'Agrega algunas con *Nueva Factura* y después vuelve aquí 😊',
                    parse_mode='Markdown',
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
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
                        f'Ya puedes usarlo para tus reportes de viáticos 😊'
                    ),
                    parse_mode='Markdown',
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )

            logger.info(f"Excel exportado: {filename} con {len(facturas)} facturas")

        except Exception as e:
            logger.error(f"Error al exportar: {e}", exc_info=True)
            await update.message.reply_text(
                "⚠️ Error al generar el Excel.\n"
                "Por favor intenta nuevamente o contacta al administrador."
            )

    # ==================== MANEJO DE BOTONES DEL MENÚ ====================

    async def manejar_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar selección de botones del menú principal"""
        texto = update.message.text

        # Mapeo de botones a comandos
        # Nota: "Nueva Factura" y "Borrar Factura" son manejados por ConversationHandlers
        if texto == '📊 Resumen':
            return await self.resumen(update, context)
        elif texto == '📋 Ver Lista':
            return await self.lista(update, context)
        elif texto == '📥 Exportar Excel':
            return await self.exportar(update, context)
        elif texto == '❓ Ayuda' or texto == '🏠 Menú Principal':
            # Si es ayuda o volver al menú, mostrar start
            if texto == '🏠 Menú Principal':
                return await self.start(update, context)
            else:
                return await self.help_command(update, context)
        else:
            # Si no reconoce el comando, mostrar menú
            keyboard = [
                ['📝 Nueva Factura', '📊 Resumen'],
                ['📋 Ver Lista', '📥 Exportar Excel'],
                ['🗑️ Borrar Factura', '❓ Ayuda']
            ]
            await update.message.reply_text(
                'No entendí ese comando 🤔\n'
                'Por favor selecciona una opción del menú:',
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )

    # ==================== ERROR HANDLER ====================

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar errores del bot"""
        logger.error(f"Error en update {update}: {context.error}", exc_info=context.error)

        # Manejar error de conflicto (múltiples instancias)
        if "Conflict" in str(context.error):
            logger.error("⚠️ ERROR: Ya hay otra instancia del bot corriendo")
            logger.error("Solución: Cierra todas las ventanas de Python y vuelve a ejecutar start.bat")
            return

        # Si hay un update, intentar notificar al usuario
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "⚠️ Ups! Ocurrió un error inesperado.\n"
                    "El error ha sido registrado en los logs.\n\n"
                    "Por favor intenta nuevamente o contacta al administrador."
                )
            except Exception:
                pass

    # ==================== SETUP ====================

    def setup_handlers(self, app: Application):
        """Configurar handlers del bot"""
        # ConversationHandler para nueva factura
        conv_handler_nueva = ConversationHandler(
            entry_points=[
                CommandHandler('nueva', self.nueva_factura),
                MessageHandler(filters.Regex('^📝 Nueva Factura$'), self.nueva_factura)
            ],
            states={
                TIPO_GASTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.recibir_tipo_gasto)],
                PHOTO: [MessageHandler(filters.PHOTO, self.recibir_foto)],
                CONFIRMAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.confirmar_datos)],
                EDITAR_CAMPO: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.editar_campo)],
                EDITAR_VALOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.editar_valor)]
            },
            fallbacks=[CommandHandler('cancelar', self.cancelar)]
        )

        # ConversationHandler para borrar factura
        conv_handler_borrar = ConversationHandler(
            entry_points=[
                CommandHandler('borrar', self.borrar),
                MessageHandler(filters.Regex('^🗑️ Borrar Factura$'), self.borrar)
            ],
            states={
                BORRAR_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.borrar_recibir_id)]
            },
            fallbacks=[CommandHandler('cancelar', self.cancelar)]
        )

        # Agregar handlers de comandos y botones
        app.add_handler(CommandHandler('start', self.start))
        app.add_handler(CommandHandler('help', self.help_command))
        app.add_handler(conv_handler_nueva)
        app.add_handler(conv_handler_borrar)
        app.add_handler(CommandHandler('resumen', self.resumen))
        app.add_handler(CommandHandler('lista', self.lista))
        app.add_handler(CommandHandler('exportar', self.exportar))

        # Handler para botones del menú (debe ir al final)
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.manejar_menu))

        # Error handler
        app.add_error_handler(self.error_handler)

        logger.info("Handlers configurados correctamente")

    def run(self):
        """Ejecutar el bot"""
        try:
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

            app.run_polling(drop_pending_updates=True)

        except KeyboardInterrupt:
            logger.info("Bot detenido por el usuario")
        except Exception as e:
            if "Conflict" in str(e):
                logger.error("=" * 60)
                logger.error("❌ ERROR: Ya hay otra instancia del bot corriendo")
                logger.error("=" * 60)
                logger.error("")
                logger.error("Soluciones:")
                logger.error("1. Cierra todas las ventanas de Python")
                logger.error("2. Abre el Administrador de Tareas (Ctrl+Shift+Esc)")
                logger.error("3. Busca procesos 'python.exe' y ciérralos")
                logger.error("4. Vuelve a ejecutar start.bat")
                logger.error("")
                logger.error("O ejecuta en PowerShell: taskkill /F /IM python.exe")
                logger.error("=" * 60)
            else:
                logger.error(f"Error fatal al iniciar el bot: {e}", exc_info=True)
            raise
