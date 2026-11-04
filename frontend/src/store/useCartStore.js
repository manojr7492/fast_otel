import { create } from 'zustand';

export const useCartStore = create((set, get) => {
  const savedCart = localStorage.getItem('shopping_cart');
  const initialItems = savedCart ? JSON.parse(savedCart) : [];

  const persist = (items) => {
    localStorage.setItem('shopping_cart', JSON.stringify(items));
  };

  return {
    items: initialItems,
    isOpen: false,
    couponCode: '',
    discountPercent: 0,

    openCart: () => set({ isOpen: true }),
    closeCart: () => set({ isOpen: false }),

    addItem: (product, quantity = 1) => {
      set((state) => {
        const existingIdx = state.items.findIndex((item) => item.product.sku === product.sku);
        let updatedItems;

        if (existingIdx > -1) {
          updatedItems = [...state.items];
          updatedItems[existingIdx].quantity += quantity;
        } else {
          updatedItems = [...state.items, { product, quantity }];
        }

        persist(updatedItems);
        return { items: updatedItems, isOpen: true };
      });
    },

    removeItem: (sku) => {
      set((state) => {
        const updatedItems = state.items.filter((item) => item.product.sku !== sku);
        persist(updatedItems);
        return { items: updatedItems };
      });
    },

    updateQuantity: (sku, quantity) => {
      if (quantity <= 0) {
        get().removeItem(sku);
        return;
      }
      set((state) => {
        const updatedItems = state.items.map((item) => {
          if (item.product.sku === sku) {
            return { ...item, quantity };
          }
          return item;
        });
        persist(updatedItems);
        return { items: updatedItems };
      });
    },

    clearCart: () => {
      persist([]);
      set({ items: [], couponCode: '', discountPercent: 0 });
    },

    applyCoupon: (code) => {
      const clean = code.trim().toUpperCase();
      if (clean === 'FASTAPI20' || clean === 'OPENTELEMETRY') {
        set({ couponCode: clean, discountPercent: 20 });
        return { success: true, message: 'Coupon applied! 20% discount added.' };
      }
      if (clean === 'DEMO10') {
        set({ couponCode: clean, discountPercent: 10 });
        return { success: true, message: 'Demo coupon applied! 10% discount added.' };
      }
      return { success: false, message: 'Invalid promo code. Try "FASTAPI20"' };
    },

    // Computations
    getItemCount: () => {
      return get().items.reduce((total, item) => total + item.quantity, 0);
    },

    getSubtotal: () => {
      return get().items.reduce((total, item) => total + item.product.price * item.quantity, 0);
    },

    getDiscountAmount: () => {
      const subtotal = get().getSubtotal();
      return (subtotal * get().discountPercent) / 100;
    },

    getShippingCost: () => {
      const subtotal = get().getSubtotal();
      if (subtotal === 0 || subtotal >= 150) return 0;
      return 15.00;
    },

    getEstimatedTax: () => {
      const taxable = get().getSubtotal() - get().getDiscountAmount();
      return taxable > 0 ? taxable * 0.0825 : 0; // 8.25% standard tax
    },

    getTotal: () => {
      const subtotal = get().getSubtotal();
      if (subtotal === 0) return 0;
      return subtotal - get().getDiscountAmount() + get().getShippingCost() + get().getEstimatedTax();
    },

    getFreeShippingProgress: () => {
      const threshold = 150;
      const subtotal = get().getSubtotal();
      const percent = Math.min(100, Math.round((subtotal / threshold) * 100));
      const remaining = Math.max(0, threshold - subtotal);
      return { percent, remaining, threshold };
    },
  };
});

