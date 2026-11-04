import React, { useState } from 'react';
import {
  X,
  Star,
  ShoppingBag,
  ShieldCheck,
  Truck,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  Layers,
  Activity,
  Plus,
  Minus
} from 'lucide-react';
import { useCartStore } from '../store/useCartStore';
import { useNotificationStore } from '../store/useNotificationStore';

export default function ProductDetailModal({ product, onClose }) {
  const { addItem } = useCartStore();
  const { addToast } = useNotificationStore();
  const [quantity, setQuantity] = useState(1);

  if (!product) return null;

  const stockQty = product.inventory?.available_quantity ?? 25;
  const isOutOfStock = stockQty <= 0;

  const handleAddToCart = () => {
    if (isOutOfStock) return;
    addItem(product, quantity);
    addToast(
      'Cart Updated',
      `Added ${quantity}x ${product.name} to your shopping cart.`,
      'success'
    );
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/75 backdrop-blur-md animate-fade-in">
      <div
        className="relative w-full max-w-3xl rounded-3xl glass-dropdown border border-slate-700/80 shadow-2xl overflow-hidden flex flex-col md:flex-row max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-10 p-2 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-slate-400 hover:text-white border border-slate-700/70 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Product Media Column */}
        <div className="md:w-1/2 relative bg-slate-950 flex items-center justify-center p-6 border-b md:border-b-0 md:border-r border-slate-800">
          <img
            src={product.image || 'https://images.unsplash.com/photo-1526738549149-8e07eca6c147?w=800&auto=format&fit=crop&q=80'}
            alt={product.name}
            className="w-full max-h-80 object-contain rounded-2xl shadow-xl"
          />
          {product.badge && (
            <span className="absolute top-4 left-4 px-3 py-1 rounded-xl bg-indigo-600/90 text-xs font-semibold text-white shadow-lg">
              {product.badge}
            </span>
          )}
        </div>

        {/* Product Information Column */}
        <div className="md:w-1/2 p-6 sm:p-8 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
              <span className="uppercase font-semibold tracking-wider text-indigo-400">
                {product.category_name || 'Hardware'}
              </span>
              <span className="font-mono bg-slate-800/80 px-2 py-0.5 rounded text-[11px]">
                SKU: {product.sku}
              </span>
            </div>

            <h2 className="text-xl sm:text-2xl font-bold text-white mb-2">
              {product.name}
            </h2>

            {/* Rating & Inventory Hub */}
            <div className="flex items-center gap-3 mb-4 text-xs">
              <div className="flex items-center text-amber-400">
                <Star className="w-4 h-4 fill-current" />
                <span className="ml-1 font-bold text-white">{product.rating || '4.9'}</span>
              </div>
              <span className="text-slate-500">({product.reviewsCount || 42} verified reviews)</span>
              <span className="text-slate-600">•</span>
              <span className="text-emerald-400 font-mono flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                {stockQty} Units Available
              </span>
            </div>

            {/* Price */}
            <div className="mb-4">
              <span className="text-2xl sm:text-3xl font-extrabold text-white font-mono">
                ${Number(product.price).toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </span>
              <span className="text-xs text-slate-400 ml-2 font-mono">USD</span>
            </div>

            {/* Description */}
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed mb-6">
              {product.description}
            </p>

            {/* Feature Bullets */}
            {product.features && product.features.length > 0 && (
              <div className="mb-6 space-y-1.5 bg-slate-900/60 p-3 rounded-xl border border-slate-800">
                <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                  Highlights:
                </p>
                {product.features.map((feat, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-xs text-slate-300">
                    <CheckCircle2 className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0" />
                    <span>{feat}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Action Row: Quantity + Add Button */}
          <div className="pt-4 border-t border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400 font-medium">Quantity</span>
              <div className="flex items-center border border-slate-700 bg-slate-900 rounded-xl overflow-hidden">
                <button
                  onClick={() => setQuantity(Math.max(1, quantity - 1))}
                  disabled={quantity <= 1 || isOutOfStock}
                  className="p-2 text-slate-400 hover:text-white disabled:opacity-40 transition-colors"
                >
                  <Minus className="w-3.5 h-3.5" />
                </button>
                <span className="px-3 font-mono text-xs font-semibold text-white">
                  {quantity}
                </span>
                <button
                  onClick={() => setQuantity(Math.min(stockQty, quantity + 1))}
                  disabled={quantity >= stockQty || isOutOfStock}
                  className="p-2 text-slate-400 hover:text-white disabled:opacity-40 transition-colors"
                >
                  <Plus className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            <button
              disabled={isOutOfStock}
              onClick={handleAddToCart}
              className={`w-full py-3 rounded-xl font-medium text-sm flex items-center justify-center gap-2 transition-all ${
                isOutOfStock
                  ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                  : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/30 hover:scale-[1.01] active:scale-[0.99]'
              }`}
            >
              <ShoppingBag className="w-4 h-4" />
              <span>
                {isOutOfStock ? 'Sold Out' : `Add to Cart - $${(product.price * quantity).toFixed(2)}`}
              </span>
            </button>
          </div>

        </div>
      </div>
    </div>
  );
}

