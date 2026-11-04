import React, { useState } from 'react';
import {
  Star,
  ShoppingBag,
  Eye,
  CheckCircle2,
  AlertTriangle,
  ArrowUpDown,
  SlidersHorizontal,
  PackageCheck,
  Check
} from 'lucide-react';
import { useCartStore } from '../store/useCartStore';
import { useNotificationStore } from '../store/useNotificationStore';

export default function ProductCatalog({ products, onSelectProduct, loading = false }) {
  const { addItem } = useCartStore();
  const { addToast } = useNotificationStore();
  const [sortBy, setSortBy] = useState('featured');
  const [addedSku, setAddedSku] = useState(null);

  // Sorting logic
  const sortedProducts = [...products].sort((a, b) => {
    if (sortBy === 'price-low') return a.price - b.price;
    if (sortBy === 'price-high') return b.price - a.price;
    if (sortBy === 'rating') return (b.rating || 0) - (a.rating || 0);
    return 0; // default featured
  });

  const handleAddToCart = (e, product) => {
    e.stopPropagation();
    addItem(product, 1);
    addToast('Item Added to Cart', `${product.name} added to your shopping cart.`, 'success');

    setAddedSku(product.sku);
    setTimeout(() => setAddedSku(null), 1200);
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {[1, 2, 3, 4, 5, 6, 7, 8].map((n) => (
          <div key={n} className="rounded-2xl bg-slate-900/50 border border-slate-800 p-4 animate-pulse">
            <div className="w-full h-48 bg-slate-800 rounded-xl mb-4"></div>
            <div className="h-4 bg-slate-800 rounded w-3/4 mb-2"></div>
            <div className="h-4 bg-slate-800 rounded w-1/2 mb-4"></div>
            <div className="h-8 bg-slate-800 rounded"></div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div>
      {/* Catalog Header with Count & Sort Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-4 border-b border-slate-800/80">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <span>Hardware Catalog</span>
            <span className="px-2 py-0.5 rounded-full bg-slate-800 text-xs font-mono text-slate-400">
              {sortedProducts.length} items
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time stock verified against Inventory Microservice (:8005)
          </p>
        </div>

        {/* Sort Filter Selector */}
        <div className="flex items-center gap-2">
          <SlidersHorizontal className="w-4 h-4 text-slate-400" />
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="bg-slate-900 border border-slate-700/80 text-xs text-slate-300 rounded-xl px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="featured">Featured Collection</option>
            <option value="price-low">Price: Low to High</option>
            <option value="price-high">Price: High to Low</option>
            <option value="rating">Top Customer Rated</option>
          </select>
        </div>
      </div>

      {/* Empty State */}
      {sortedProducts.length === 0 && (
        <div className="text-center py-16 rounded-3xl bg-slate-900/40 border border-slate-800">
          <p className="text-slate-400 text-sm mb-2">No hardware items match your search or filters.</p>
          <span className="text-xs text-indigo-400">Try clearing your search term or picking another category.</span>
        </div>
      )}

      {/* Product Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {sortedProducts.map((product) => {
          const qty = product.inventory?.available_quantity ?? 15;
          const isOutOfStock = qty <= 0;
          const isLowStock = qty > 0 && qty < 10;
          const isJustAdded = addedSku === product.sku;

          return (
            <div
              key={product.sku || product.uuid}
              onClick={() => onSelectProduct(product)}
              className="group glass-card rounded-2xl overflow-hidden flex flex-col cursor-pointer border border-slate-800/80 hover:border-indigo-500/50 hover:shadow-xl hover:shadow-indigo-500/10 transition-all duration-300"
            >
              {/* Product Image & Badges */}
              <div className="relative aspect-[4/3] w-full overflow-hidden bg-slate-950">
                <img
                  src={product.image || 'https://images.unsplash.com/photo-1526738549149-8e07eca6c147?w=800&auto=format&fit=crop&q=80'}
                  alt={product.name}
                  loading="lazy"
                  className="w-full h-full object-cover object-center group-hover:scale-105 transition-transform duration-500"
                />

                {/* Promotional Badge */}
                {product.badge && (
                  <span className="absolute top-3 left-3 px-2.5 py-1 rounded-lg bg-indigo-600/90 backdrop-blur-md text-[11px] font-semibold text-white shadow-sm">
                    {product.badge}
                  </span>
                )}

                {/* Stock Status Badge */}
                <div className="absolute top-3 right-3">
                  {isOutOfStock ? (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg bg-rose-950/80 backdrop-blur-md border border-rose-700/50 text-[10px] font-semibold text-rose-300">
                      Out of Stock
                    </span>
                  ) : isLowStock ? (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg bg-amber-950/80 backdrop-blur-md border border-amber-700/50 text-[10px] font-semibold text-amber-300">
                      <AlertTriangle className="w-3 h-3" /> Only {qty} left
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg bg-emerald-950/80 backdrop-blur-md border border-emerald-700/50 text-[10px] font-semibold text-emerald-300">
                      <CheckCircle2 className="w-3 h-3" /> In Stock ({qty})
                    </span>
                  )}
                </div>

                {/* Quick View Hover Overlay */}
                <div className="absolute inset-0 bg-slate-950/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                  <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900/90 text-xs font-medium text-white shadow-lg">
                    <Eye className="w-3.5 h-3.5" /> Quick View
                  </span>
                </div>
              </div>

              {/* Card Details */}
              <div className="p-4 flex-1 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1">
                    <span className="uppercase tracking-wider font-medium truncate max-w-[140px]">
                      {product.category_name || 'Hardware'}
                    </span>
                    <span className="font-mono text-slate-500">
                      {product.sku}
                    </span>
                  </div>

                  <h3 className="text-sm font-semibold text-white group-hover:text-indigo-300 transition-colors line-clamp-2 mb-2">
                    {product.name}
                  </h3>

                  {/* Rating */}
                  <div className="flex items-center gap-1.5 mb-3 text-xs">
                    <div className="flex items-center text-amber-400">
                      <Star className="w-3.5 h-3.5 fill-current" />
                      <span className="ml-1 font-semibold text-white">{product.rating || '4.9'}</span>
                    </div>
                    <span className="text-slate-500 text-[11px]">
                      ({product.reviewsCount || 42} reviews)
                    </span>
                  </div>
                </div>

                {/* Price & Add to Cart button */}
                <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between gap-3">
                  <div>
                    <span className="text-xs text-slate-400 font-mono">USD</span>
                    <span className="text-lg font-bold text-white ml-1 font-mono">
                      ${Number(product.price).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </span>
                  </div>

                  <button
                    disabled={isOutOfStock}
                    onClick={(e) => handleAddToCart(e, product)}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium transition-all ${
                      isOutOfStock
                        ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                        : isJustAdded
                        ? 'bg-emerald-600 text-white'
                        : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-900/30 active:scale-95'
                    }`}
                  >
                    {isJustAdded ? (
                      <>
                        <Check className="w-3.5 h-3.5" />
                        <span>Added</span>
                      </>
                    ) : (
                      <>
                        <ShoppingBag className="w-3.5 h-3.5" />
                        <span>Add</span>
                      </>
                    )}
                  </button>
                </div>

              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

