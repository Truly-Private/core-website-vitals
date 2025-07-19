import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Define your site's pages with their priority and change frequency
const pages = [
  { path: '/', priority: 1.0, changefreq: 'daily' },
  { path: '/features', priority: 0.9, changefreq: 'weekly' },
  { path: '/pricing', priority: 0.9, changefreq: 'weekly' },
  { path: '/about', priority: 0.8, changefreq: 'monthly' },
  { path: '/blog', priority: 0.8, changefreq: 'daily' },
  { path: '/contact', priority: 0.7, changefreq: 'monthly' },
  { path: '/privacy', priority: 0.5, changefreq: 'yearly' },
  { path: '/terms', priority: 0.5, changefreq: 'yearly' },
  { path: '/trial', priority: 0.9, changefreq: 'weekly' },
  { path: '/login', priority: 0.6, changefreq: 'monthly' },
  { path: '/register', priority: 0.7, changefreq: 'monthly' },
];

// Blog posts (you can dynamically generate these from your CMS/database)
const blogPosts = [
  { path: '/blog/understanding-core-web-vitals', priority: 0.7, changefreq: 'monthly' },
  { path: '/blog/improve-seo-rankings-2024', priority: 0.7, changefreq: 'monthly' },
  { path: '/blog/technical-seo-best-practices', priority: 0.7, changefreq: 'monthly' },
];

const baseUrl = 'https://corewebsitevitals.com';
const today = new Date().toISOString().split('T')[0];

// Generate XML sitemap
function generateSitemap() {
  const allPages = [...pages, ...blogPosts];
  
  let xml = '<?xml version="1.0" encoding="UTF-8"?>\n';
  xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n';
  xml += '        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n';
  xml += '        xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9\n';
  xml += '        http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">\n';

  allPages.forEach(page => {
    xml += '  <url>\n';
    xml += `    <loc>${baseUrl}${page.path}</loc>\n`;
    xml += `    <lastmod>${today}</lastmod>\n`;
    xml += `    <changefreq>${page.changefreq}</changefreq>\n`;
    xml += `    <priority>${page.priority}</priority>\n`;
    xml += '  </url>\n';
  });

  xml += '</urlset>';

  // Write sitemap to public directory
  const sitemapPath = path.join(__dirname, '..', 'public', 'sitemap.xml');
  fs.writeFileSync(sitemapPath, xml, 'utf8');
  console.log('✅ Sitemap generated successfully at:', sitemapPath);
}

// Generate sitemap index for large sites
function generateSitemapIndex() {
  let xml = '<?xml version="1.0" encoding="UTF-8"?>\n';
  xml += '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n';
  
  // Main sitemap
  xml += '  <sitemap>\n';
  xml += `    <loc>${baseUrl}/sitemap.xml</loc>\n`;
  xml += `    <lastmod>${today}</lastmod>\n`;
  xml += '  </sitemap>\n';
  
  // Blog sitemap (if you have many blog posts)
  xml += '  <sitemap>\n';
  xml += `    <loc>${baseUrl}/sitemap-blog.xml</loc>\n`;
  xml += `    <lastmod>${today}</lastmod>\n`;
  xml += '  </sitemap>\n';
  
  xml += '</sitemapindex>';
  
  const indexPath = path.join(__dirname, '..', 'public', 'sitemap-index.xml');
  fs.writeFileSync(indexPath, xml, 'utf8');
  console.log('✅ Sitemap index generated successfully at:', indexPath);
}

// Generate blog-specific sitemap
function generateBlogSitemap() {
  let xml = '<?xml version="1.0" encoding="UTF-8"?>\n';
  xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n';
  xml += '        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">\n';

  blogPosts.forEach(post => {
    xml += '  <url>\n';
    xml += `    <loc>${baseUrl}${post.path}</loc>\n`;
    xml += `    <lastmod>${today}</lastmod>\n`;
    xml += `    <changefreq>${post.changefreq}</changefreq>\n`;
    xml += `    <priority>${post.priority}</priority>\n`;
    xml += '  </url>\n';
  });

  xml += '</urlset>';

  const blogSitemapPath = path.join(__dirname, '..', 'public', 'sitemap-blog.xml');
  fs.writeFileSync(blogSitemapPath, xml, 'utf8');
  console.log('✅ Blog sitemap generated successfully at:', blogSitemapPath);
}

// Run the generators
generateSitemap();
generateBlogSitemap();
generateSitemapIndex();

console.log('\n📋 Remember to:');
console.log('1. Submit your sitemap to Google Search Console');
console.log('2. Add sitemap URL to robots.txt');
console.log('3. Update sitemap whenever you add new pages');
console.log('4. Consider automating sitemap generation in your build process');