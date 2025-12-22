#!/usr/bin/env python3
"""
Script de prueba de OCR
Prueba la extracción de datos de una factura antes de usar el bot
"""

import sys
import pytesseract
from PIL import Image
import re

def probar_ocr(imagen_path):
    """Probar OCR en una imagen de factura"""
    print("=" * 60)
    print("PRUEBA DE OCR - Bot de Viáticos")
    print("=" * 60)
    print()
    
    # Verificar que existe la imagen
    try:
        img = Image.open(imagen_path)
        print(f"✅ Imagen cargada: {imagen_path}")
        print(f"   Tamaño: {img.size}")
        print()
    except Exception as e:
        print(f"❌ Error al cargar imagen: {e}")
        return
    
    # Hacer OCR
    print("🔍 Ejecutando OCR...")
    try:
        texto = pytesseract.image_to_string(img, lang='spa')
        print("✅ OCR completado")
        print()
    except Exception as e:
        print(f"❌ Error en OCR: {e}")
        print("\nPosibles soluciones:")
        print("1. Instalar Tesseract OCR")
        print("2. Agregar Tesseract al PATH del sistema")
        print("3. O especificar la ruta en el código")
        return
    
    # Mostrar texto completo extraído
    print("-" * 60)
    print("TEXTO EXTRAÍDO (completo):")
    print("-" * 60)
    print(texto)
    print("-" * 60)
    print()
    
    # Intentar extraer datos específicos
    print("=" * 60)
    print("EXTRACCIÓN DE DATOS ESPECÍFICOS")
    print("=" * 60)
    print()
    
    lineas = texto.split('\n')
    
    # Buscar NIT
    print("🔍 Buscando NIT...")
    nits_encontrados = []
    for i, linea in enumerate(lineas):
        if 'NIT' in linea.upper():
            print(f"   Línea {i}: {linea}")
            # Buscar números
            for j in range(i, min(i+3, len(lineas))):
                numeros = re.findall(r'\d+', lineas[j])
                for num in numeros:
                    if len(num) >= 6 and num != '71224556':
                        nits_encontrados.append((num, lineas[j]))
    
    if nits_encontrados:
        print(f"   ✅ NITs encontrados: {len(nits_encontrados)}")
        for nit, linea in nits_encontrados:
            print(f"      • {nit} (en: {linea.strip()})")
    else:
        print("   ❌ No se encontró NIT")
    print()
    
    # Buscar SERIE
    print("🔍 Buscando SERIE...")
    series_encontradas = []
    for i, linea in enumerate(lineas):
        if 'SERIE' in linea.upper():
            print(f"   Línea {i}: {linea}")
            match = re.search(r'SERIE[:\s]*([A-Z0-9]+)', linea.upper())
            if match:
                series_encontradas.append(match.group(1))
            else:
                # Buscar en siguiente línea
                if i + 1 < len(lineas):
                    match = re.search(r'([A-Z0-9]{8,})', lineas[i + 1].upper())
                    if match:
                        series_encontradas.append(match.group(1))
    
    if series_encontradas:
        print(f"   ✅ Series encontradas: {len(series_encontradas)}")
        for serie in series_encontradas:
            print(f"      • {serie}")
    else:
        print("   ❌ No se encontró SERIE")
    print()
    
    # Buscar NÚMERO
    print("🔍 Buscando NÚMERO...")
    numeros_encontrados = []
    for i, linea in enumerate(lineas):
        if 'NUMERO' in linea.upper() or 'NÚMERO' in linea.upper():
            print(f"   Línea {i}: {linea}")
            match = re.search(r'N[UÚ]MERO[:\s]*(\d+)', linea.upper())
            if match:
                numeros_encontrados.append(match.group(1))
            else:
                if i + 1 < len(lineas):
                    nums = re.findall(r'\d{6,}', lineas[i + 1])
                    if nums:
                        numeros_encontrados.extend(nums)
    
    if numeros_encontrados:
        print(f"   ✅ Números encontrados: {len(numeros_encontrados)}")
        for num in numeros_encontrados:
            print(f"      • {num}")
    else:
        print("   ❌ No se encontró NÚMERO")
    print()
    
    # Buscar MONTO
    print("🔍 Buscando MONTO...")
    montos_encontrados = []
    for i, linea in enumerate(lineas):
        if 'TOTAL' in linea.upper() and 'Q' in linea:
            print(f"   Línea {i}: {linea}")
            match = re.search(r'Q\s*[\d,]+\.?\d*', linea)
            if match:
                monto_str = match.group().replace('Q', '').replace(',', '').replace(' ', '')
                try:
                    monto = float(monto_str)
                    montos_encontrados.append((monto, linea.strip()))
                except:
                    pass
    
    if montos_encontrados:
        print(f"   ✅ Montos encontrados: {len(montos_encontrados)}")
        for monto, linea in montos_encontrados:
            print(f"      • Q{monto:.2f} (en: {linea})")
    else:
        print("   ❌ No se encontró MONTO")
    print()
    
    # Resumen
    print("=" * 60)
    print("RESUMEN DE EXTRACCIÓN")
    print("=" * 60)
    print(f"NITs encontrados:    {len(nits_encontrados)}")
    print(f"Series encontradas:  {len(series_encontradas)}")
    print(f"Números encontrados: {len(numeros_encontrados)}")
    print(f"Montos encontrados:  {len(montos_encontrados)}")
    print()
    
    if all([nits_encontrados, series_encontradas, numeros_encontrados, montos_encontrados]):
        print("✅ EXTRACCIÓN EXITOSA - El OCR funcionó correctamente")
    else:
        print("⚠️  EXTRACCIÓN PARCIAL - Algunos datos no se pudieron extraer")
        print("\nRecomendaciones:")
        print("1. Toma la foto con buena iluminación")
        print("2. Asegúrate que el texto esté legible")
        print("3. Evita sombras y reflejos")
        print("4. Mantén la factura lo más plana posible")
    
    print()
    print("=" * 60)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python test_ocr.py <ruta_imagen>")
        print("\nEjemplo:")
        print("  python test_ocr.py factura.jpg")
        print("  python test_ocr.py /mnt/user-data/uploads/1766440603650_image.png")
    else:
        probar_ocr(sys.argv[1])
