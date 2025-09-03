#!/usr/bin/env python3
"""
Script mejorado para bÃºsqueda de noticias sobre normativas ISO en Chile
Incluye datos reales encontrados y capacidad de scraping directo
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import time
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import logging

class ISONewsScraperEnhanced:
    def __init__(self, output_dir: str = r"src/data/iso_news"):
        """
        Inicializa el scraper mejorado de noticias ISO para Chile
        """
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Crear directorio de salida
        os.makedirs(output_dir, exist_ok=True)
        
        self.news_data = []
        self.inn_news_url = "https://www.inn.cl/noticias"
        self.isotools_blog_url = "https://www.isotools.us/blog-corporativo/"
        self.aenor_revista_url = "https://revista.aenor.com/"
        self.anexia_blog_url = "https://consultoria.anexia.es/blog/"
        self.hardcoded_articles = []

    def _parse_spanish_date(self, date_str: str) -> str:
        """
        Parsea una fecha en formato 'DD MMMM, YYYY' en español a 'DD/MM/YYYY'.
        """
        if not date_str:
            return ''

        meses = {
            'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
            'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
            'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
        }

        try:
            parts = date_str.lower().replace(',', '').split()
            if len(parts) == 3:
                day, month_name, year = parts
                month = meses.get(month_name)
                if month:
                    return f"{int(day):02d}/{month}/{year}"
        except Exception as e:
            self.logger.warning(f"No se pudo parsear la fecha '{date_str}': {e}")

        return date_str

    def scrape_inn_news(self) -> List[Dict[str, str]]:
        """
        Extrae las noticias directamente de la página de noticias del INN.
        (Función desactivada para excluir noticias del INN)
        """
        self.logger.info("La extracción de noticias del INN ha sido desactivada.")
        return []

    def scrape_isotools_blog(self) -> List[Dict[str, str]]:
        """
        Extrae la lista de artículos del blog de ISOTools.
        """
        self.logger.info(f"Extrayendo lista de noticias de: {self.isotools_blog_url}")
        articles = []
        try:
            response = self.session.get(self.isotools_blog_url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            for article_tag in soup.select('div.wpex-post-cards-entry'):
                title_link = article_tag.select_one('h2.wpex-card-title a')
                if title_link:
                    url = title_link.get('href')
                    title = title_link.get_text(strip=True)

                    date_tag = article_tag.select_one('div.wpex-card-date')
                    date_str = date_tag.get_text(strip=True) if date_tag else ''
                    formatted_date = self._parse_spanish_date(date_str)

                    articles.append({
                        'title': title,
                        'url': url,
                        'date': formatted_date,
                        'source': 'ISOTools Blog'
                    })
        except Exception as e:
            self.logger.error(f"Error extrayendo noticias de ISOTools: {e}")

        return articles

    def scrape_aenor_revista(self) -> List[Dict[str, str]]:
        """
        Extrae las noticias de la revista de AENOR.
        """
        self.logger.info(f"Extrayendo noticias de: {self.aenor_revista_url}")
        articles = []
        try:
            issues_page_url = "https://revista.aenor.com/adicional/revistas-anteriores.html"
            response = self.session.get(issues_page_url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            issue_links = []
            for link in soup.select('div.licont a[href]'):
                href = link.get('href')
                if href and 'descargar' not in href.lower() and href not in issue_links:
                    issue_links.append(urljoin(issues_page_url, href))

            for issue_url in issue_links:
                try:
                    issue_response = self.session.get(issue_url, timeout=15)
                    issue_soup = BeautifulSoup(issue_response.content, 'html.parser')

                    issue_title_tag = issue_soup.select_one('h1#menu_revista')
                    issue_title = issue_title_tag.get_text(strip=True) if issue_title_tag else ''
                    date_match = re.search(r'\|\s*([\w-]+)\s*\|\s*(\d{4})', issue_title)
                    date_str = f"01 {date_match.group(1).split('-')[0]} {date_match.group(2)}" if date_match else ''

                    # Main articles
                    for article_link in issue_soup.select('ul.lista_imagenes li a'):
                        url = urljoin(issue_url, article_link.get('href'))
                        title = article_link.get('title')
                        if title and url not in [a['url'] for a in articles]:
                            articles.append({
                                'title': title,
                                'url': url,
                                'date': self._parse_spanish_date(date_str.replace(' ', ', ')),
                                'source': 'Revista AENOR'
                            })

                    # "De un vistazo" articles
                    for article_link in issue_soup.select('div.modulo_noticia a.hover'):
                        url = urljoin(issue_url, article_link.get('href'))
                        title = article_link.get_text(strip=True)
                        if title and url not in [a['url'] for a in articles]:
                            articles.append({
                                'title': title,
                                'url': url,
                                'date': self._parse_spanish_date(date_str.replace(' ', ', ')),
                                'source': 'Revista AENOR'
                            })
                except Exception as e:
                    self.logger.warning(f"Error scraping issue {issue_url}: {e}")

        except Exception as e:
            self.logger.error(f"Error extrayendo noticias de AENOR: {e}")

        return articles

    def scrape_anexia_blog(self) -> List[Dict[str, str]]:
        """
        Extrae las noticias del blog de Anexia.
        (Función desactivada porque el contenido se carga dinámicamente con JavaScript)
        """
        self.logger.warning("El scraper para Anexia Consultoría está desactivado debido a la carga dinámica de contenido.")
        return []

    def scrape_direct_urls(self, articles_to_scrape: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Extrae contenido directamente de una lista de URLs de artÃ­culos.
        """
        scraped_articles = []

        for news_item in articles_to_scrape:
            try:
                self.logger.info(f"Extrayendo contenido de: {news_item['title'][:50]}...")

                # Nota: verify=False se aÃ±ade para omitir errores de SSL en sitios con certificados mal configurados (ej. ispch.gob.cl)
                response = self.session.get(news_item['url'], timeout=15, verify=False)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extraer contenido completo
                content_text = ''
                content_selectors = [
                    'div.field-item', '.content', '.article-content', '.entry-content',
                    '.post-content', '.main-content', 'article',
                    '.article-body', '.story-body'
                ]
                
                for selector in content_selectors:
                    content_elem = soup.select_one(selector)
                    if content_elem:
                        # Remover scripts y estilos
                        for script in content_elem(["script", "style"]):
                            script.decompose()
                        content_text = content_elem.get_text(strip=True, separator=' ')
                        break
                
                # Si no encontramos contenido especÃ­fico, usar todo el texto
                if not content_text:
                    content_text = soup.get_text(strip=True, separator=' ')
                
                # Extraer imagen principal (og:image o primera imagen relevante)
                image_url = None
                og_image = soup.select_one('meta[property="og:image"]')
                if og_image:
                    image_url = urljoin(news_item['url'], og_image['content'])
                else:
                    # Fallback a buscar una imagen en el contenido
                    content_img = soup.select_one('.content img, .entry-content img, .article-body img')
                    if content_img and content_img.get('src'):
                        image_url = urljoin(news_item['url'], content_img['src'])

                # Crear artÃ­culo completo
                summary = content_text[:200] + '...' if len(content_text) > 200 else content_text
                complete_article = {
                    'title': news_item['title'],
                    'url': news_item['url'],
                    'source': news_item['source'],
                    'date': news_item['date'],
                    'summary': summary,
                    'image_url': image_url,
                    'full_content': content_text[:10000],  # Limitar a 10k caracteres
                    'content_length': len(content_text),
                    'scraped_at': datetime.now().isoformat(),
                    'scraping_success': True
                }
                
                scraped_articles.append(complete_article)
                time.sleep(1)  # Pausa entre requests
                
            except Exception as e:
                self.logger.warning(f"Error extrayendo {news_item['url']}: {str(e)}")
                # Agregar artÃ­culo sin contenido completo
                error_article = {
                    'title': news_item['title'],
                    'url': news_item['url'],
                    'source': news_item['source'],
                    'date': news_item['date'],
                    'full_content': '',
                    'content_length': 0,
                    'scraped_at': datetime.now().isoformat(),
                    'scraping_success': False,
                    'error': str(e)
                }
                scraped_articles.append(error_article)
        
        return scraped_articles
    
    def save_results_json(self, data: List[Dict[str, Any]], filename: str) -> str:
        """
        Guarda los resultados en formato JSON
        """
        filepath = os.path.join(self.output_dir, filename)
        
        output_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "data_source": "Multiple Sources",
                "total_articles": len(data),
                "successful_scrapes": len([a for a in data if a.get('scraping_success', False)]),
                "failed_scrapes": len([a for a in data if not a.get('scraping_success', True)])
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
        Ejecuta el scraping, lo combina con artículos hardcodeados y genera el archivo JSON
        """
        self.logger.info("Iniciando el scraping de noticias ISO Chile")
        
        # 1. Obtener la lista de artÃ­culos de INN
        inn_articles = self.scrape_inn_news()
        
        # Obtener articulos de nuevas fuentes
        isotools_articles = self.scrape_isotools_blog()
        aenor_articles = self.scrape_aenor_revista()
        anexia_articles = self.scrape_anexia_blog()

        # 2. Combinar con artÃ­culos hardcodeados y de-duplicar
        all_articles = inn_articles + isotools_articles + aenor_articles + anexia_articles
        combined_articles = {article['url']: article for article in all_articles}
        for article in self.hardcoded_articles:
            if article['url'] not in combined_articles:
                combined_articles[article['url']] = article

        articles_to_scrape = list(combined_articles.values())

        # 3. Extraer contenido para todos los artÃ­culos
        self.logger.info(f"Se procesarÃ¡n {len(articles_to_scrape)} artÃ­culos Ãºnicos.")
        final_articles = self.scrape_direct_urls(articles_to_scrape)

        files_generated = {}
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        files_generated['articles'] = self.save_results_json(
            final_articles, f'iso_news_articulos_{timestamp}.json'
        )
        
        return files_generated


def main():
    """FunciÃ³n principal del script"""
    print("ðŸš€ Iniciando scraper de noticias ISO en Chile desde INN")
    print("=" * 60)
    
    scraper = ISONewsScraperEnhanced()
    
    try:
        generated_files = scraper.run_complete_analysis()
        
        print("\nâœ… Scraping completado exitosamente!")
        print(f"\nðŸ“ Archivo JSON generado:")
        
        for file_type, filepath in generated_files.items():
            filename = os.path.basename(filepath)
            print(f"   â€¢ {file_type.replace('_', ' ').title()}: {filename}")
        
    except Exception as e:
        print(f"âŒ Error durante la ejecuciÃ³n: {str(e)}")
        raise


if __name__ == "__main__":
    main()

