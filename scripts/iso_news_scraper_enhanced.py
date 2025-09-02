#!/usr/bin/env python3
"""
Script para búsqueda de noticias sobre normativas ISO en español.
"""

import requests
import json
import os
from datetime import datetime
from typing import Dict, List, Any
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging

class ISONewsScraperEnhanced:
    def __init__(self, output_dir: str = r"src/data/iso_news"):
        """
        Inicializa el scraper de noticias ISO.
        """
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        os.makedirs(output_dir, exist_ok=True)
        
        self.sources = {
            "isoexpertise": {
                "url": "https://www.isoexpertise.com/noticias/",
                "scrape_function": self.scrape_isoexpertise_news
            },
            "sgs_chile": {
                "url": "https://www.sgs.com/es-cl/noticias",
                "scrape_function": self.scrape_sgs_chile_news
            }
        }

    def scrape_sgs_chile_news(self) -> List[Dict[str, str]]:
        """
        Extrae la lista de noticias de la página de noticias de SGS Chile.
        """
        url = self.sources['sgs_chile']['url']
        self.logger.info(f"Extrayendo lista de artículos de: {url}")
        articles = []
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            next_data_script = soup.find('script', id='__NEXT_DATA__')
            if next_data_script:
                data = json.loads(next_data_script.string)
                items = data['props']['pageProps']['layoutData']['sitecore']['route']['placeholders']['jss-main'][0]['placeholders']['filtered-list-overview-filtered-list'][0]['fields']['items']

                for item in items:
                    title = item.get('headline', {}).get('value')
                    article_url_path = item.get('cta', {}).get('value', {}).get('href')
                    date = item.get('date', {}).get('value')

                    if title and article_url_path:
                        article_url = urljoin(url, article_url_path)
                        articles.append({
                            'title': title,
                            'url': article_url,
                            'date': date,
                            'source': 'SGS Chile'
                        })
        except Exception as e:
            self.logger.error(f"Error extrayendo la lista de noticias de SGS Chile: {e}")

        self.logger.info(f"Encontrados {len(articles)} artículos en SGS Chile.")
        return articles

    def scrape_isoexpertise_news(self) -> List[Dict[str, str]]:
        """
        Extrae la lista de noticias de la página principal de isoexpertise.com.
        """
        url = self.sources['isoexpertise']['url']
        self.logger.info(f"Extrayendo lista de artículos de: {url}")
        articles = []
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Cada artículo está en un div con la clase 'noticiasitem'
            for post in soup.select('div.noticiasitem'):
                title_element = post.select_one('h2.h2 a')
                date_element = post.select_one('.date')

                if title_element and title_element.get('href'):
                    title = title_element.get_text(strip=True)
                    article_url = urljoin(url, title_element['href'])
                    # Limpiar y formatear la fecha
                    date_text = date_element.get_text(strip=True).replace('/', '').strip() if date_element else ''
                    # Reformat date from 'DD MM YYYY' to 'DD/MM/YYYY'
                    parts = date_text.split()
                    if len(parts) == 3:
                        date = f"{parts[0]}/{parts[1]}/{parts[2]}"
                    else:
                        date = None

                    articles.append({
                        'title': title,
                        'url': article_url,
                        'date': date,
                        'source': 'isoExpertise'
                    })
        except Exception as e:
            self.logger.error(f"Error extrayendo la lista de noticias de isoExpertise: {e}")

        self.logger.info(f"Encontrados {len(articles)} artículos en isoExpertise.")
        return articles

    def scrape_article_content(self, article_url: str) -> Dict[str, Any]:
        """
        Extrae el contenido completo y la imagen de la URL de un artículo.
        """
        content_data = {'full_content': '', 'image_url': None, 'content_length': 0}
        try:
            self.logger.info(f"Extrayendo contenido de: {article_url}")
            # Nota: verify=False se añade para omitir errores de SSL
            response = self.session.get(article_url, timeout=15, verify=False)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extraer imagen principal (og:image o primera imagen relevante)
            og_image = soup.select_one('meta[property="og:image"]')
            if og_image:
                content_data['image_url'] = urljoin(article_url, og_image['content'])
            else:
                content_img = soup.select_one('.entry-content img, .post-content img, .article-body img, .content img, article img')
                if content_img and content_img.get('src'):
                    content_data['image_url'] = urljoin(article_url, content_img['src'])

            # Extraer contenido de texto
            content_text = ''
            content_selectors = [
                '.entry-content', '.post-content', '.article-content',
                '.article-body', 'article', '.main-content'
            ]

            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    for script in content_elem(["script", "style"]):
                        script.decompose()
                    content_text = content_elem.get_text(strip=True, separator=' ')
                    break

            if not content_text:
                content_text = soup.get_text(strip=True, separator=' ')

            content_data['full_content'] = content_text[:10000]
            content_data['content_length'] = len(content_text)

        except Exception as e:
            self.logger.warning(f"Error extrayendo {article_url}: {str(e)}")
        
        return content_data

    def save_results_json(self, data: List[Dict[str, Any]], filename: str) -> str:
        """
        Guarda los resultados en formato JSON.
        """
        filepath = os.path.join(self.output_dir, filename)
        
        output_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_articles": len(data),
            },
            "articles": data
        }

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Resultados guardados en: {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"Error guardando resultados: {str(e)}")
            raise
    
    def run_complete_analysis(self) -> Dict[str, str]:
        """
        Ejecuta el scraping de todas las fuentes y genera el archivo JSON.
        """
        self.logger.info("Iniciando el scraping de noticias ISO en español.")
        all_articles = []

        for source_name, source_data in self.sources.items():
            self.logger.info(f"Procesando fuente: {source_name}")
            base_articles = source_data["scrape_function"]()

            for article in base_articles:
                content = self.scrape_article_content(article['url'])
                article.update(content)
                article['scraped_at'] = datetime.now().isoformat()
                all_articles.append(article)
                time.sleep(1)

        files_generated = {}
        if all_articles:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            files_generated['articles'] = self.save_results_json(
                all_articles, f'iso_news_articulos_{timestamp}.json'
            )
        else:
            self.logger.info("No se encontraron artículos para guardar.")
        
        return files_generated

def main():
    print("🚀 Iniciando scraper de noticias ISO en español...")
    print("=" * 60)
    
    scraper = ISONewsScraperEnhanced()
    
    try:
        generated_files = scraper.run_complete_analysis()
        
        if generated_files:
            print("\n✅ Scraping completado exitosamente!")
            print(f"\n📄 Archivo JSON generado:")
            for file_type, filepath in generated_files.items():
                filename = os.path.basename(filepath)
                print(f"   • {file_type.title()}: {filename}")
        else:
            print("\nℹ️ No se generaron archivos nuevos.")

    except Exception as e:
        print(f"❌ Error durante la ejecución: {str(e)}")
        raise

if __name__ == "__main__":
    main()
