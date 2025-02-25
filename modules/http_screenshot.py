import os
import sys
import asyncio
from pyppeteer import launch


async def capture_screenshot_async(url, output_file):
    # Lanzamos el navegador en modo headless
    browser = await launch(headless=True)
    page = await browser.newPage()

    # Cargamos la URL
    await page.goto(url)

    # Capturamos la pantalla y guardamos la imagen en el archivo indicado
    await page.screenshot({'path': output_file})
    print(f"Captura de pantalla guardada en {output_file}.")

    await browser.close()


def capture_http_screenshot(url):
    """
    Captura una captura de pantalla de la página web especificada utilizando pyppeteer.
    La imagen se guarda en logs/{url}/http/screenshot.png y se copia en logs/{url}/reporte/.

    Parámetros:
      - url: URL de la página a capturar.

    Retorna:
      - True si la captura se realizó correctamente.
    """
    # Define la ruta del archivo de salida (asegúrate de que 'url' sea un nombre de directorio válido,
    # por lo que si es necesario, se debe sanitizar o extraer el hostname)
    output_file = f"logs/{url}/http/screenshot.png"

    # Aseguramos que los directorios necesarios existen
    os.makedirs(f"logs/{url}/http", exist_ok=True)
    os.makedirs(f"logs/{url}/reporte", exist_ok=True)

    # Ejecutamos la función asíncrona de pyppeteer usando el event loop de asyncio
    asyncio.get_event_loop().run_until_complete(capture_screenshot_async(url, output_file))

    # Copiamos la imagen en el directorio de reporte
    os.system(f"cp logs/{url}/http/screenshot.png logs/{url}/reporte/screenshot.png")

    return True


def run_http_screenshot(url):
    capture_http_screenshot(url)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        url = sys.argv[1]
        capture_http_screenshot(url)
    else:
        print("Uso: python http_screenshot.py <URL>")
