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
    TIPO_GASTO, PHOTO, CONFIRMAR, EDITAR_CAMPO, EDITAR_VALOR, BORRAR_ID,
    REGISTRO_NOMBRE, SELECCIONAR_MES, SELECCIONAR_ANIO, CAMBIAR_NOMBRE
)
from .database import Database
from .ocr import extraer_datos_factura
from .excel_export import generar_excel
from .utils import (
    formatear_monto, truncar_texto, validar_monto,
    obtener_nombre_mes, obtener_mes_actual, obtener_anio_actual, formatear_periodo
)

logger = logging.getLogger(__name__)


class SamanthaBot:
    """Bot de Viáticos Samantha"""

    def __init__(self):
        """Inicializar bot"""
        self.db = Database()
        logger.info("Bot Samantha inicializado")

    def _get_user_id(self, update: Update) -> int:
        """Obtener user_id del update"""
        return update.effective_user.id

    async def _verificar_usuario_registrado(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Verificar si el usuario está registrado, si no iniciar registro"""
        user_id = self._get_user_id(update)

        if not self.db.usuario_existe(user_id):
            await update.message.reply_text(
                "¡Hola! 👋 Veo que es tu primera vez por aquí.\n\n"
                "Para empezar, ¿cómo te llamas? 😊",
                reply_markup=ReplyKeyboardRemove()
            )
            return False
        return True

    def _get_menu_principal(self):
        """Obtener teclado del menú principal"""
        return [
            ['📝 Nueva Factura', '📊 Resumen'],
            ['📋 Ver Lista', '📥 Exportar Excel'],
            ['🗑️ Borrar Factura', '⚙️ Mi Perfil'],
            ['❓ Ayuda']
        ]

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start - Menú principal con botones"""
        try:
            user_id = self._get_user_id(update)

            if not self.db.usuario_existe(user_id):
                await update.message.reply_text(
                    "¡Hola! 👋 Veo que es tu primera vez por aquí.\n\n"
                    "Para empezar, ¿cómo te llamas? 😊",
                    reply_markup=ReplyKeyboardRemove()
                )
                context.user_data['esperando_nombre_registro'] = True
                return

            nombre_usuario = self.db.obtener_nombre_usuario(user_id)

            mensaje = (
                f"¡Hola {nombre_usuario}! 👋 Soy *Samantha*, tu asistente personal de viáticos 💼\n\n"
                "Estoy aquí para ayudarte a llevar un control ordenado de todas tus facturas. "
                "Solo envíame las fotos y yo me encargo del resto 📸✨\n\n"
                "*¿Qué quieres hacer?*\n"
                "Selecciona una opción del menú:"
            )

            keyboard = self._get_menu_principal()

            await update.message.reply_text(
                mensaje,
                parse_mode='Markdown',
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            logger.info(f"Usuario {user_id} ({nombre_usuario}) inició el bot")
        except Exception as e:
            logger.error(f"Error en comando /start: {e}", exc_info=True)
            await update.message.reply_text(
                "Ups! Hubo un error al iniciar. Por favor intenta de nuevo."
            )

    async def registrar_nombre(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Registrar nombre de usuario nuevo"""
        try:
            user_id = self._get_user_id(update)
            nombre = update.message.text.strip()

            if len(nombre) < 2 or len(nombre) > 50:
                await update.message.reply_text(
                    "Mmm, ese nombre es muy corto o muy largo 🤔\n\n"
                    "Por favor escribe tu nombre (entre 2 y 50 caracteres):"
                )
                return

            self.db.registrar_usuario(user_id, nombre)
            logger.info(f"Usuario {user_id} registrado como: {nombre}")

            mensaje = (
                f"¡Encantada de conocerte, {nombre}! 😊\n\n"
                "Ya estás registrado y listo para empezar.\n\n"
                "*¿Qué quieres hacer?*\n"
                "Selecciona una opción del menú:"
            )

            keyboard = self._get_menu_principal()

            await update.message.reply_text(
                mensaje,
                parse_mode='Markdown',
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )

            context.user_data['esperando_nombre_registro'] = False

        except Exception as e:
            logger.error(f"Error al registrar nombre: {e}", exc_info=True)
            await update.message.reply_text(
                "⚠️ Error al registrar tu nombre. Por favor intenta de nuevo."
            )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /help"""
        try:
            if not await self._verificar_usuario_registrado(update, context):
                context.user_data['esperando_nombre_registro'] = True
                return

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

            keyboard = [['🏠 Menú Principal']]

            await update.message.reply_text(
                mensaje,
                parse_mode='Markdown',
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            logger.info(f"Usuario {self._get_user_id(update)} solicitó ayuda")
        except Exception as e:
            logger.error(f"Error en comando /help: {e}", exc_info=True)
            await update.message.reply_text("Error al mostrar ayuda. Intenta nuevamente.")

    async def nueva_factura(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Iniciar registro de nueva factura"""
        try:
            if not await self._verificar_usuario_registrado(update, context):
                context.user_data['esperando_nombre_registro'] = True
                return ConversationHandler.END

            keyboard = [['🍔 ALIMENTACIÓN', '⛽ COMBUSTIBLE'], ['❌ Cancelar']]
            await update.message.reply_text(
                '¡Perfecto! Vamos a registrar tu factura 📝\n\n'
                'Primero dime, ¿qué tipo de gasto es?',
                reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
            )
            logger.info(f"Usuario {self._get_user_id(update)} inició nueva factura")
            return TIPO_GASTO
        except Exception as e:
            logger.error(f"Error al iniciar nueva factura: {e}", exc_info=True)
            await update.message.reply_text("Error al iniciar. Intenta nuevamente desde el menú.")
            return ConversationHandler.END

    async def recibir_tipo_gasto(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Recibir tipo de gasto"""
        try:
            tipo = update.message.text.upper().replace('🍔 ', '').replace('⛽ ', '')

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

            os.makedirs(FACTURAS_FOLDER, exist_ok=True)

            photo = update.message.photo[-1]
            file = await photo.get_file()
            filename = f"{FACTURAS_FOLDER}/factura_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            await file.download_to_drive(filename)

            context.user_data['foto_path'] = filename
            logger.info(f"Foto guardada: {filename}")

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

            context.user_data['datos_factura'] = datos

            fecha_hoy = datetime.now().strftime('%d/%m/%Y')
            context.user_data['datos_factura']['fecha'] = fecha_hoy

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
            datos_faltantes = []
            if not datos['nit']:
                datos_faltantes.append('NIT')
            if not datos['serie']:
                datos_faltantes.append('Serie')
            if not datos['numero']:
                datos_faltantes.append('Número')
            if not datos['monto']:
                datos_faltantes.append('Monto')

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

            if campo == 'monto':
                try:
                    nuevo_valor = validar_monto(nuevo_valor)
                except ValueError:
                    await update.message.reply_text(
                        'Mmm, ese monto no me quedó claro 🤔\n'
                        'Intenta de nuevo, solo con números (ej: 150.50):'
                    )
                    return EDITAR_VALOR

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
            user_id = self._get_user_id(update)
            datos = context.user_data['datos_factura']
            tipo_gasto = context.user_data['tipo_gasto']
            foto = context.user_data['foto_path']

            factura_id = self.db.insertar_factura(
                user_id=user_id,
                fecha=datos.get('fecha'),
                nit=datos.get('nit'),
                nombre=datos.get('nombre'),
                serie=datos.get('serie'),
                numero=datos.get('numero'),
                tipo_gasto=tipo_gasto,
                monto=datos.get('monto'),
                foto_path=foto
            )

            logger.info(f"Factura #{factura_id} guardada exitosamente para usuario {user_id}")

            keyboard = self._get_menu_principal()

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
        keyboard = self._get_menu_principal()

        await update.message.reply_text(
            'Ok! Operación cancelada 👌\n\n'
            'Cuando quieras, estoy aquí para ayudarte 😊',
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        logger.info("Usuario canceló operación")
        return ConversationHandler.END

    async def resumen(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ver resumen de gastos del mes actual"""
        try:
            if not await self._verificar_usuario_registrado(update, context):
                context.user_data['esperando_nombre_registro'] = True
                return

            user_id = self._get_user_id(update)
            mes_actual = obtener_mes_actual()
            anio_actual = obtener_anio_actual()

            total, cantidad, por_tipo = self.db.obtener_resumen(user_id, mes_actual, anio_actual)

            keyboard = self._get_menu_principal()
            keyboard.insert(1, ['📅 Ver Otros Meses'])

            if cantidad == 0:
                await update.message.reply_text(
                    f'Todavía no tienes facturas guardadas en {obtener_nombre_mes(mes_actual)} {anio_actual} 📭\n\n'
                    'Presiona *Nueva Factura* para empezar a registrarlas!',
                    parse_mode='Markdown',
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return

            mensaje = f'📊 *Resumen de {obtener_nombre_mes(mes_actual)} {anio_actual}*\n\n'
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
            logger.info(f"Resumen solicitado por usuario {user_id}: {cantidad} facturas, total {total}")

        except Exception as e:
            logger.error(f"Error al obtener resumen: {e}", exc_info=True)
            await update.message.reply_text("⚠️ Error al obtener resumen. Intenta nuevamente.")

    async def resumen_seleccionar_mes(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mostrar opciones para seleccionar mes"""
        try:
            if not await self._verificar_usuario_registrado(update, context):
                context.user_data['esperando_nombre_registro'] = True
                return ConversationHandler.END

            user_id = self._get_user_id(update)
            meses_disponibles = self.db.obtener_meses_con_datos(user_id)

            if not meses_disponibles:
                keyboard = self._get_menu_principal()
                await update.message.reply_text(
                    'No tienes facturas registradas todavía 📭\n\n'
                    'Agrega algunas con *Nueva Factura* primero 😊',
                    parse_mode='Markdown',
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return ConversationHandler.END

            mensaje = '📅 *Selecciona el mes que quieres ver:*\n\n'
            keyboard = []

            for anio, mes in meses_disponibles[:12]:
                nombre_mes = obtener_nombre_mes(mes)
                keyboard.append([f'{nombre_mes} {anio}'])

            keyboard.append(['❌ Cancelar'])

            await update.message.reply_text(
                mensaje,
                parse_mode='Markdown',
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )

            context.user_data['meses_disponibles'] = meses_disponibles
            return SELECCIONAR_MES

        except Exception as e:
            logger.error(f"Error al seleccionar mes: {e}", exc_info=True)
            await update.message.reply_text("⚠️ Error al obtener meses. Intenta nuevamente.")
            return ConversationHandler.END

    async def resumen_mes_seleccionado(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mostrar resumen del mes seleccionado"""
        try:
            user_id = self._get_user_id(update)
            seleccion = update.message.text

            if seleccion == '❌ Cancelar':
                return await self.cancelar(update, context)

            meses_disponibles = context.user_data.get('meses_disponibles', [])

            anio_mes = None
            for anio, mes in meses_disponibles:
                nombre_mes = obtener_nombre_mes(mes)
                if f'{nombre_mes} {anio}' == seleccion:
                    anio_mes = (anio, mes)
                    break

            if not anio_mes:
                await update.message.reply_text(
                    'No entendí ese mes 🤔\n'
                    'Por favor selecciona uno de la lista:'
                )
                return SELECCIONAR_MES

            anio, mes = anio_mes
            total, cantidad, por_tipo = self.db.obtener_resumen(user_id, mes, anio)

            keyboard = self._get_menu_principal()

            mensaje = f'📊 *Resumen de {obtener_nombre_mes(mes)} {anio}*\n\n'
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

            return ConversationHandler.END

        except Exception as e:
            logger.error(f"Error al mostrar resumen de mes: {e}", exc_info=True)
            await update.message.reply_text("⚠️ Error al obtener resumen. Intenta nuevamente.")
            return ConversationHandler.END

    async def lista(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Listar últimas facturas del usuario"""
        try:
            if not await self._verificar_usuario_registrado(update, context):
                context.user_data['esperando_nombre_registro'] = True
                return

            user_id = self._get_user_id(update)
            facturas = self.db.obtener_facturas(user_id, limit=20)

            keyboard = self._get_menu_principal()

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
            logger.info(f"Lista de facturas solicitada por usuario {user_id}: {len(facturas)} facturas")

        except Exception as e:
            logger.error(f"Error al listar facturas: {e}", exc_info=True)
            await update.message.reply_text("⚠️ Error al obtener lista. Intenta nuevamente.")

    async def borrar(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Iniciar proceso de borrar factura"""
        try:
            if not await self._verificar_usuario_registrado(update, context):
                context.user_data['esperando_nombre_registro'] = True
                return ConversationHandler.END

            keyboard = [['❌ Cancelar']]

            await update.message.reply_text(
                'Perfecto! Vamos a borrar una factura 🗑️\n\n'
                'Escribe el *número de la factura* que quieres eliminar\n\n'
                '💡 Puedes usar *Ver Lista* primero para ver los números de tus facturas.',
                parse_mode='Markdown',
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            logger.info(f"Usuario {self._get_user_id(update)} inició proceso de borrado")
            return BORRAR_ID

        except Exception as e:
            logger.error(f"Error al iniciar borrado: {e}", exc_info=True)
            await update.message.reply_text("Error al iniciar. Intenta nuevamente desde el menú.")
            return ConversationHandler.END

    async def borrar_recibir_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Recibir ID de factura a borrar"""
        try:
            user_id = self._get_user_id(update)
            keyboard = self._get_menu_principal()

            if update.message.text == '❌ Cancelar':
                await update.message.reply_text(
                    'Ok! Operación cancelada 👌\n\n'
                    'No se eliminó ninguna factura.',
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return ConversationHandler.END

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

            eliminada = self.db.eliminar_factura(user_id, factura_id)

            if eliminada:
                await update.message.reply_text(
                    f'Listo! ✅ La factura #{factura_id} ya está eliminada.',
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                logger.info(f"Factura #{factura_id} eliminada exitosamente por usuario {user_id}")
            else:
                await update.message.reply_text(
                    f'Mmm... 🤔 No encontré ninguna factura tuya con el número #{factura_id}\n\n'
                    f'Usa *Ver Lista* para ver tus facturas disponibles.',
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

    async def exportar(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Iniciar proceso de exportación"""
        try:
            if not await self._verificar_usuario_registrado(update, context):
                context.user_data['esperando_nombre_registro'] = True
                return ConversationHandler.END

            user_id = self._get_user_id(update)
            meses_disponibles = self.db.obtener_meses_con_datos(user_id)

            if not meses_disponibles:
                keyboard = self._get_menu_principal()
                await update.message.reply_text(
                    'Todavía no tienes facturas para exportar 📭\n\n'
                    'Agrega algunas con *Nueva Factura* y después vuelve aquí 😊',
                    parse_mode='Markdown',
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return ConversationHandler.END

            mensaje = '📥 *Exportar a Excel*\n\n'
            mensaje += '¿Qué período quieres exportar?\n\n'

            keyboard = [['📅 Todas las Facturas']]

            for anio, mes in meses_disponibles[:10]:
                nombre_mes = obtener_nombre_mes(mes)
                keyboard.append([f'{nombre_mes} {anio}'])

            keyboard.append(['❌ Cancelar'])

            await update.message.reply_text(
                mensaje,
                parse_mode='Markdown',
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )

            context.user_data['meses_disponibles'] = meses_disponibles
            return SELECCIONAR_ANIO

        except Exception as e:
            logger.error(f"Error al iniciar exportación: {e}", exc_info=True)
            await update.message.reply_text("⚠️ Error al iniciar exportación. Intenta nuevamente.")
            return ConversationHandler.END

    async def exportar_periodo_seleccionado(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Exportar el período seleccionado"""
        try:
            user_id = self._get_user_id(update)
            seleccion = update.message.text

            if seleccion == '❌ Cancelar':
                return await self.cancelar(update, context)

            keyboard = self._get_menu_principal()

            await update.message.reply_text(
                'Dale! Ya estoy preparando tu Excel 📊\n'
                'Esto tomará solo unos segundos...'
            )

            mes = None
            anio = None

            if seleccion != '📅 Todas las Facturas':
                meses_disponibles = context.user_data.get('meses_disponibles', [])

                for a, m in meses_disponibles:
                    nombre_mes = obtener_nombre_mes(m)
                    if f'{nombre_mes} {a}' == seleccion:
                        mes = m
                        anio = a
                        break

                if mes is None:
                    await update.message.reply_text(
                        'No entendí ese período 🤔\n'
                        'Por favor intenta de nuevo desde el menú.',
                        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                    )
                    return ConversationHandler.END

            facturas = self.db.obtener_todas_facturas(user_id, mes, anio)

            if not facturas:
                await update.message.reply_text(
                    'No encontré facturas para ese período 📭',
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return ConversationHandler.END

            nombre_usuario = self.db.obtener_nombre_usuario(user_id)
            periodo_texto = formatear_periodo(mes, anio) if mes and anio else "Todas"

            filepath, filename = generar_excel(facturas, nombre_usuario, periodo_texto)

            total = sum([f[5] for f in facturas if f[5]])

            with open(filepath, 'rb') as file:
                caption = f'¡Listo! 🎉 Aquí está tu Excel\n\n'
                caption += f'📄 *{len(facturas)} facturas* registradas\n'
                caption += f'💰 *Total:* {formatear_monto(total)}\n'

                if mes and anio:
                    caption += f'📅 *Período:* {obtener_nombre_mes(mes)} {anio}\n\n'
                else:
                    caption += f'📅 *Período:* Todas las facturas\n\n'

                caption += 'Ya puedes usarlo para tus reportes de viáticos 😊'

                await update.message.reply_document(
                    document=file,
                    filename=filename,
                    caption=caption,
                    parse_mode='Markdown',
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )

            logger.info(f"Excel exportado por usuario {user_id}: {filename} con {len(facturas)} facturas")

            return ConversationHandler.END

        except Exception as e:
            logger.error(f"Error al exportar: {e}", exc_info=True)
            await update.message.reply_text(
                "⚠️ Error al generar el Excel.\n"
                "Por favor intenta nuevamente o contacta al administrador."
            )
            return ConversationHandler.END

    async def mi_perfil(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mostrar perfil del usuario"""
        try:
            if not await self._verificar_usuario_registrado(update, context):
                context.user_data['esperando_nombre_registro'] = True
                return

            user_id = self._get_user_id(update)
            nombre_usuario = self.db.obtener_nombre_usuario(user_id)

            total_facturas = self.db.contar_facturas_usuario(user_id)
            total_gastado, _, _ = self.db.obtener_resumen(user_id)

            mensaje = '⚙️ *Mi Perfil*\n\n'
            mensaje += f'👤 *Nombre:* {nombre_usuario}\n'
            mensaje += f'🆔 *ID Telegram:* {user_id}\n\n'
            mensaje += f'📊 *Estadísticas:*\n'
            mensaje += f'📄 Total de facturas: {total_facturas}\n'
            mensaje += f'💰 Total gastado: {formatear_monto(total_gastado)}\n'

            keyboard = [
                ['✏️ Cambiar Nombre'],
                ['🏠 Menú Principal']
            ]

            await update.message.reply_text(
                mensaje,
                parse_mode='Markdown',
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )

            logger.info(f"Usuario {user_id} consultó su perfil")

        except Exception as e:
            logger.error(f"Error al mostrar perfil: {e}", exc_info=True)
            await update.message.reply_text("⚠️ Error al mostrar perfil. Intenta nuevamente.")

    async def cambiar_nombre_inicio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Iniciar proceso de cambio de nombre"""
        try:
            if not await self._verificar_usuario_registrado(update, context):
                context.user_data['esperando_nombre_registro'] = True
                return ConversationHandler.END

            keyboard = [['❌ Cancelar']]

            await update.message.reply_text(
                '✏️ Cambiar nombre\n\n'
                'Escribe tu nuevo nombre:',
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )

            return CAMBIAR_NOMBRE

        except Exception as e:
            logger.error(f"Error al iniciar cambio de nombre: {e}", exc_info=True)
            await update.message.reply_text("Error al iniciar. Intenta nuevamente.")
            return ConversationHandler.END

    async def cambiar_nombre_guardar(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Guardar nuevo nombre de usuario"""
        try:
            user_id = self._get_user_id(update)

            if update.message.text == '❌ Cancelar':
                return await self.cancelar(update, context)

            nuevo_nombre = update.message.text.strip()

            if len(nuevo_nombre) < 2 or len(nuevo_nombre) > 50:
                await update.message.reply_text(
                    'Mmm, ese nombre es muy corto o muy largo 🤔\n\n'
                    'Por favor escribe un nombre entre 2 y 50 caracteres:'
                )
                return CAMBIAR_NOMBRE

            self.db.actualizar_nombre_usuario(user_id, nuevo_nombre)
            logger.info(f"Usuario {user_id} cambió su nombre a: {nuevo_nombre}")

            keyboard = self._get_menu_principal()

            await update.message.reply_text(
                f'¡Perfecto! ✨ Tu nombre ha sido actualizado a *{nuevo_nombre}*\n\n'
                '¿Qué quieres hacer ahora?',
                parse_mode='Markdown',
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )

            return ConversationHandler.END

        except Exception as e:
            logger.error(f"Error al cambiar nombre: {e}", exc_info=True)
            await update.message.reply_text(
                "⚠️ Error al cambiar nombre. Intenta nuevamente."
            )
            return ConversationHandler.END

    async def manejar_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar selección de botones del menú principal"""
        if context.user_data.get('esperando_nombre_registro'):
            return await self.registrar_nombre(update, context)

        texto = update.message.text

        if texto == '📊 Resumen':
            return await self.resumen(update, context)
        elif texto == '📋 Ver Lista':
            return await self.lista(update, context)
        elif texto == '📥 Exportar Excel':
            return await self.exportar(update, context)
        elif texto == '⚙️ Mi Perfil':
            return await self.mi_perfil(update, context)
        elif texto == '❓ Ayuda' or texto == '🏠 Menú Principal':
            if texto == '🏠 Menú Principal':
                return await self.start(update, context)
            else:
                return await self.help_command(update, context)
        else:
            keyboard = self._get_menu_principal()
            await update.message.reply_text(
                'No entendí ese comando 🤔\n'
                'Por favor selecciona una opción del menú:',
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar errores del bot"""
        logger.error(f"Error en update {update}: {context.error}", exc_info=context.error)

        if "Conflict" in str(context.error):
            logger.error("⚠️ ERROR: Ya hay otra instancia del bot corriendo")
            logger.error("Solución: Cierra todas las ventanas de Python y vuelve a ejecutar start.bat")
            return

        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "⚠️ Ups! Ocurrió un error inesperado.\n"
                    "El error ha sido registrado en los logs.\n\n"
                    "Por favor intenta nuevamente o contacta al administrador."
                )
            except Exception:
                pass

    def setup_handlers(self, app: Application):
        """Configurar handlers del bot"""
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

        conv_handler_resumen_mes = ConversationHandler(
            entry_points=[
                MessageHandler(filters.Regex('^📅 Ver Otros Meses$'), self.resumen_seleccionar_mes)
            ],
            states={
                SELECCIONAR_MES: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.resumen_mes_seleccionado)]
            },
            fallbacks=[CommandHandler('cancelar', self.cancelar)]
        )

        conv_handler_exportar = ConversationHandler(
            entry_points=[
                CommandHandler('exportar', self.exportar),
                MessageHandler(filters.Regex('^📥 Exportar Excel$'), self.exportar)
            ],
            states={
                SELECCIONAR_ANIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.exportar_periodo_seleccionado)]
            },
            fallbacks=[CommandHandler('cancelar', self.cancelar)]
        )

        conv_handler_perfil = ConversationHandler(
            entry_points=[
                MessageHandler(filters.Regex('^✏️ Cambiar Nombre$'), self.cambiar_nombre_inicio)
            ],
            states={
                CAMBIAR_NOMBRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.cambiar_nombre_guardar)]
            },
            fallbacks=[CommandHandler('cancelar', self.cancelar)]
        )

        app.add_handler(CommandHandler('start', self.start))
        app.add_handler(CommandHandler('help', self.help_command))
        app.add_handler(conv_handler_nueva)
        app.add_handler(conv_handler_borrar)
        app.add_handler(conv_handler_resumen_mes)
        app.add_handler(conv_handler_exportar)
        app.add_handler(conv_handler_perfil)
        app.add_handler(CommandHandler('resumen', self.resumen))
        app.add_handler(CommandHandler('lista', self.lista))
        app.add_handler(MessageHandler(filters.Regex('^⚙️ Mi Perfil$'), self.mi_perfil))

        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.manejar_menu))

        app.add_error_handler(self.error_handler)

        logger.info("Handlers configurados correctamente")

    def run(self):
        """Ejecutar el bot"""
        try:
            logger.info("=" * 60)
            logger.info("🤖 Samantha - Bot de Viáticos")
            logger.info("Iniciando bot...")
            logger.info("=" * 60)

            app = Application.builder().token(TELEGRAM_TOKEN).build()

            self.setup_handlers(app)

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
