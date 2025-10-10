import { useEffect, useState } from 'react';

export default function ISOToolsSectionClient() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const timestamp = Date.now();
        const response = await fetch(`https://raw.githubusercontent.com/thenext90/noticias_isotools_cms/main/isotools-daily-news.json?t=${timestamp}`);
        if (!response.ok) throw new Error('No se pudo cargar el archivo remoto');
        const json = await response.json();
        setData(json.daily_news || []);
      } catch (err) {
        setError('No se pudieron cargar las noticias de ISOTools.');
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) return (
    <section className="py-12 text-center"><p>Cargando noticias ISOTools...</p></section>
  );
  if (error) return (
    <section className="py-12 text-center text-red-600"><p>{error}</p></section>
  );
  if (!data || data.length === 0) return (
    <section className="py-12 text-center"><p>No hay noticias disponibles.</p></section>
  );

  // Filtrar duplicados por ID (si existieran)
  const uniqueArticles = Array.isArray(data)
    ? data.filter((item, idx, arr) => arr.findIndex(a => a.id === item.id) === idx)
    : [];

  return (
    <section className="pb-6 pt-12 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-xl font-bold text-accent-800 bg-accent-50 inline-block px-6 py-3 rounded-full border-2 border-accent-200">
            Consejos y tendencias para ayudarte a mejorar tus sistemas de gestión
          </h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-12">
          {uniqueArticles.map((article) => (
            <article key={article.id} className="bg-white rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 overflow-hidden group">
              {article.image_url && (
                <div className="w-full h-48 bg-gray-100 flex items-center justify-center overflow-hidden">
                  <img
                    src={article.image_url}
                    alt={article.title}
                    className="object-cover w-full h-full max-h-48"
                    style={{ objectFit: 'cover', width: '100%', height: '100%', maxHeight: '12rem' }}
                  />
                </div>
              )}
              <div className="p-6">
                <h3 className="text-lg font-bold text-gray-800 leading-tight mb-3 group-hover:text-accent-800 transition-colors">
                  {article.title}
                </h3>
                {article.text && (
                  <p className="text-gray-700 text-sm leading-relaxed whitespace-pre-line">
                    {article.text}
                  </p>
                )}
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
