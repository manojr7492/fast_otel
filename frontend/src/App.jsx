import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import HeroBanner from './components/HeroBanner';
import ProductCatalog from './components/ProductCatalog';
import ProductDetailModal from './components/ProductDetailModal';
import CartDrawer from './components/CartDrawer';
import CheckoutModal from './components/CheckoutModal';
import OtpLoginModal from './components/OtpLoginModal';
import AccountModal from './components/AccountModal';
import NotificationCenter from './components/NotificationCenter';
import TelemetryDrawer from './components/TelemetryDrawer';
import ToastContainer from './components/ToastContainer';
import { api } from './services/api';
import { MOCK_PRODUCTS, MOCK_CATEGORIES } from './data/mockData';
import { Layers, Activity, ShieldCheck, Heart, ExternalLink, Terminal } from 'lucide-react';

export default function App() {
  const [products, setProducts] = useState(MOCK_PRODUCTS);
  const [categories, setCategories] = useState(MOCK_CATEGORIES);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [isCheckoutOpen, setIsCheckoutOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  // Initial data loading from live FastAPI backend (:8002) with automatic fallback
  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const [cats, prods] = await Promise.all([
          api.catalog.getCategories(),
          api.catalog.getProducts(),
        ]);
        if (cats && cats.length > 0) setCategories(cats);
        if (prods && prods.length > 0) setProducts(prods);
      } catch (err) {
        console.warn('Backend catalog loading fallback:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  // Filter products based on search query and category pill selection
  const filteredProducts = products.filter((p) => {
    const matchesCategory = !selectedCategory ||
      p.category_uuid === selectedCategory ||
      p.category_name === selectedCategory ||
      p.slug?.includes(selectedCategory);

    const matchesSearch = !searchQuery.trim() ||
      p.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.sku?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.description?.toLowerCase().includes(searchQuery.toLowerCase());

    return matchesCategory && matchesSearch;
  });

  return (
    <div className="min-h-screen bg-[#090D16] text-slate-100 flex flex-col font-sans selection:bg-indigo-600 selection:text-white">
      
      {/* Top Sticky Navigation */}
      <Navbar
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        selectedCategory={selectedCategory}
        setSelectedCategory={setSelectedCategory}
        categories={categories}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        
        {/* Hero Promotion & Category Pills */}
        <HeroBanner
          categories={categories}
          selectedCategory={selectedCategory}
          onSelectCategory={setSelectedCategory}
        />

        {/* Product Catalog Grid */}
        <ProductCatalog
          products={filteredProducts}
          onSelectProduct={setSelectedProduct}
          loading={loading}
        />

      </main>

      {/* Enterprise Architecture Footer */}
      <footer className="mt-16 border-t border-slate-800/80 bg-slate-950/70 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-10 text-xs">
            
            {/* Column 1: Brand & Core Mission */}
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white">
                  <Layers className="w-4 h-4" />
                </div>
                <span className="text-base font-bold text-white">ShopSphere Core</span>
              </div>
              <p className="text-slate-400 leading-relaxed">
                Production-grade distributed e-commerce platform orchestrating 6 microservices with OpenTelemetry tracing and automatic saga rollback.
              </p>
              <div className="flex items-center gap-1.5 text-emerald-400 font-mono text-[11px]">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <span>OpenTelemetry Traces Connected</span>
              </div>
            </div>

            {/* Column 2: Microservices Matrix */}
            <div>
              <h4 className="font-semibold text-white uppercase tracking-wider mb-3">
                Microservice Ports
              </h4>
              <ul className="space-y-1.5 text-slate-400 font-mono text-[11px]">
                <li><span className="text-indigo-400 font-semibold">:8001</span> User & Auth Service</li>
                <li><span className="text-indigo-400 font-semibold">:8002</span> Product Catalog Service</li>
                <li><span className="text-indigo-400 font-semibold">:8003</span> Order & Saga Service</li>
                <li><span className="text-indigo-400 font-semibold">:8004</span> Payment Gateway</li>
                <li><span className="text-indigo-400 font-semibold">:8005</span> Inventory & Stock</li>
                <li><span className="text-indigo-400 font-semibold">:8006</span> Notification Service</li>
              </ul>
            </div>

            {/* Column 3: Observability Endpoints */}
            <div>
              <h4 className="font-semibold text-white uppercase tracking-wider mb-3">
                Telemetry Infrastructure
              </h4>
              <ul className="space-y-2 text-slate-400">
                <li>
                  <a
                    href="http://localhost:16686"
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center justify-between text-indigo-300 hover:text-white transition-colors"
                  >
                    <span>Jaeger Tracing Web UI</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                  <span className="font-mono text-[10px] text-slate-500">http://localhost:16686</span>
                </li>
                <li>
                  <span className="text-slate-300 block">Jaeger OTLP HTTP Endpoint</span>
                  <span className="font-mono text-[10px] text-slate-500">http://localhost:4318/v1/traces</span>
                </li>
                <li>
                  <span className="text-slate-300 block">W3C Context Format</span>
                  <span className="font-mono text-[10px] text-slate-500">00-&#123;trace_id&#125;-&#123;span_id&#125;-01</span>
                </li>
              </ul>
            </div>

            {/* Column 4: Quick Start Commands */}
            <div>
              <h4 className="font-semibold text-white uppercase tracking-wider mb-3">
                Local Orchestration
              </h4>
              <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 font-mono text-[11px] text-slate-300 space-y-1">
                <div className="flex items-center gap-1.5 text-indigo-400 font-bold mb-1">
                  <Terminal className="w-3.5 h-3.5" /> Start Microservices
                </div>
                <div>./start_all.sh</div>
                <div className="text-slate-500 text-[10px]"># Launches all 6 services</div>
                <div className="pt-1 text-emerald-400">npm run dev</div>
                <div className="text-slate-500 text-[10px]"># Launches Vite on :5173</div>
              </div>
            </div>

          </div>

          <div className="pt-6 border-t border-slate-900 text-center text-slate-500 text-xs flex flex-col sm:flex-row items-center justify-between gap-3">
            <span>© 2026 ShopSphere Enterprise. Powered by FastAPI & React.</span>
            <span className="flex items-center gap-1">
              Built with <Heart className="w-3.5 h-3.5 text-rose-500 fill-current" /> and OpenTelemetry Observability.
            </span>
          </div>

        </div>
      </footer>

      {/* Global Modals & Drawers */}
      <ProductDetailModal
        product={selectedProduct}
        onClose={() => setSelectedProduct(null)}
      />

      <CartDrawer
        onCheckout={() => setIsCheckoutOpen(true)}
      />

      <CheckoutModal
        isOpen={isCheckoutOpen}
        onClose={() => setIsCheckoutOpen(false)}
      />

      <OtpLoginModal />

      <AccountModal />

      <NotificationCenter />

      <TelemetryDrawer />

      <ToastContainer />

    </div>
  );
}

