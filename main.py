#!/usr/bin/env python3
"""
Samantha - Bot de Viáticos
Punto de entrada principal para ejecutar el bot
"""

import sys
import logging
from src.config import validate_config
from src.utils import configurar_logging
from src.bot import SamanthaBot


def main():
    """Función principal"""
    try:
        # Configurar logging
        configurar_logging(nivel=logging.INFO)
        logger = logging.getLogger(__name__)

        # Validar configuración
        logger.info("Validando configuración...")
        validate_config()
        logger.info("Configuración válida ✓")

        # Crear e iniciar bot
        bot = SamanthaBot()
        bot.run()

    except ValueError as e:
        print(f"\n{e}\n")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 Bot detenido por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error fatal: {e}\n")
        logging.error(f"Error fatal: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
