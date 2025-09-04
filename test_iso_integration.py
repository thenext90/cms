import os
import sys

def test_iso_scraper():
    """Prueba el scraper ISO localmente"""
    print("🧪 Probando scraper ISO en CMS...")

    # Cambiar al directorio scripts
    script_dir = os.path.join(os.getcwd(), "scripts")

    if not os.path.exists(script_dir):
        print("❌ Directorio scripts no encontrado")
        return False

    # Verificar que existen los archivos
    scraper_file = os.path.join(script_dir, "iso_news_scraper_enhanced.py")
    config_file = os.path.join(script_dir, "config_iso_scraper.py")

    if not os.path.exists(scraper_file):
        print("❌ Scraper no encontrado")
        return False

    if not os.path.exists(config_file):
        print("❌ Configuración no encontrada")
        return False

    print("✅ Archivos encontrados")
    print(f"📋 Scraper: {scraper_file}")
    print(f"⚙️ Config: {config_file}")

    # Ejecutar scraper
    try:
        import subprocess
        result = subprocess.run([sys.executable, scraper_file],
                              cwd=script_dir,
                              capture_output=True,
                              text=True)

        if result.returncode == 0:
            print("✅ Scraper ejecutado exitosamente")

            # Verificar archivos JSON generados
            data_dir = os.path.join(os.getcwd(), "src", "data", "iso_news")
            if os.path.exists(data_dir):
                json_files = [f for f in os.listdir(data_dir) if f.endswith(".json")]
                print(f"📊 Archivos JSON generados: {len(json_files)}")
                for file in json_files:
                    print(f"  • {file}")
            else:
                print("⚠️ Directorio de datos no encontrado")

        else:
            print("❌ Error ejecutando scraper:")
            print(result.stderr)

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    return True

if __name__ == "__main__":
    test_iso_scraper()
