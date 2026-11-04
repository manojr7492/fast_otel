import React, { useState } from 'react';
import {
  X,
  CreditCard,
  QrCode,
  Zap,
  CheckCircle2,
  AlertTriangle,
  Activity,
  ExternalLink,
  ShieldAlert,
  ArrowRight,
  Package,
  Layers,
  Sparkles,
  RefreshCw,
  Copy
} from 'lucide-react';
import { useAuthStore } from '../store/useAuthStore';
import { useCartStore } from '../store/useCartStore';
import { useNotificationStore } from '../store/useNotificationStore';
import { api } from '../services/api';
import { getJaegerTraceUrl } from '../services/telemetry';

export default function CheckoutModal({ isOpen, onClose }) {
  const { user, savedAddresses } = useAuthStore();
  const { items, getTotal, clearCart } = useCartStore();
  const { addToast } = useNotificationStore();

  const [paymentMethod, setPaymentMethod] = useState('CREDIT_CARD'); // CREDIT_CARD | UPI | ONE_CLICK
  const [selectedAddressUuid, setSelectedAddressUuid] = useState(savedAddresses[0]?.uuid || 'addr-default');
  const [simulateFailure, setSimulateFailure] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [orderResult, setOrderResult] = useState(null);
  const [copiedTrace, setCopiedTrace] = useState(false);

  if (!isOpen) return null;

  const total = getTotal();

  const handleCheckout = async (e) => {
    e.preventDefault();
    if (items.length === 0) return;

    setIsLoading(true);

    const payload = {
      user_uuid: user?.uuid || 'usr-demo-customer-01',
      customer_email: user?.email || 'customer@antigravity.io',
      customer_name: user?.full_name || user?.username || 'Demo Customer',
      shipping_address_uuid: selectedAddressUuid,
      items: items.map((item) => ({
        product_uuid: item.product.uuid || `prod-${item.product.sku}`,
        sku: item.product.sku,
        quantity: item.quantity,
      })),
      payment_method: paymentMethod,
      simulate_payment_failure: simulateFailure,
    };

    try {
      const result = await api.order.checkout(payload);
      setIsLoading(false);
      setOrderResult(result);

      if (result.success) {
        clearCart();
        addToast(
          'Order Confirmed!',
          `Order #${result.data?.uuid?.slice(0, 8)} placed. Jaeger trace recorded.`,
          'success',
          result.traceId
        );
      } else {
        addToast(
          'Saga Compensation Executed',
          'Simulated payment failure: Reserved inventory was rolled back.',
          'error',
          result.traceId
        );
      }
    } catch (err) {
      setIsLoading(false);
      const fallbackTraceId = err.response?.headers?.['x-trace-id'] || 'trace-err-' + Date.now();
      setOrderResult({
        success: false,
        simulatedFailure: simulateFailure,
        error: err.response?.data?.message || err.message || 'Order execution error',
        traceId: fallbackTraceId,
        details: 'Saga compensation: Inventory and order transactions aborted cleanly.',
      });
    }
  };

  const copyTraceId = (traceId) => {
    if (!traceId) return;
    navigator.clipboard?.writeText(traceId);
    setCopiedTrace(true);
    setTimeout(() => setCopiedTrace(false), 1500);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/80 backdrop-blur-md animate-fade-in">
      <div
        className="relative w-full max-w-2xl rounded-3xl glass-dropdown border border-slate-700/80 shadow-2xl overflow-hidden max-h-[92vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-6 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-400">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">
                {orderResult ? 'Saga Order Confirmation' : 'Enterprise Checkout'}
              </h2>
              <p className="text-xs text-slate-400">
                {orderResult
                  ? 'OpenTelemetry Distributed Trace & Saga Audit'
                  : 'Orchestrating Order, Inventory, Payment & Notification services'}
              </p>
            </div>
          </div>

          <button
            onClick={() => {
              setOrderResult(null);
              onClose();
            }}
            className="p-2 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body: Checkout Form OR Confirmation/Saga Visualizer */}
        <div className="p-6 overflow-y-auto flex-1">
          {!orderResult ? (
            <form onSubmit={handleCheckout} className="space-y-6">
              
              {/* Order Items Summary */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Order Items ({items.length})
                </label>
                <div className="bg-slate-900/70 rounded-2xl border border-slate-800 p-3 space-y-2 max-h-40 overflow-y-auto">
                  {items.map(({ product, quantity }) => (
                    <div key={product.sku} className="flex items-center justify-between text-xs text-slate-300">
                      <div className="flex items-center gap-2 truncate">
                        <span className="font-mono text-indigo-400">{quantity}x</span>
                        <span className="truncate">{product.name}</span>
                      </div>
                      <span className="font-mono text-white ml-2 flex-shrink-0">
                        ${(product.price * quantity).toFixed(2)}
                      </span>
                    </div>
                  ))}
                  <div className="pt-2 border-t border-slate-800 flex justify-between text-xs font-bold text-white">
                    <span>Total Amount</span>
                    <span className="font-mono text-emerald-400">${total.toFixed(2)}</span>
                  </div>
                </div>
              </div>

              {/* Shipping Address Selection */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Shipping Destination (User Service :8001)
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {savedAddresses.map((addr) => (
                    <div
                      key={addr.uuid}
                      onClick={() => setSelectedAddressUuid(addr.uuid)}
                      className={`p-3 rounded-xl border text-xs cursor-pointer transition-all ${
                        selectedAddressUuid === addr.uuid
                          ? 'bg-indigo-950/40 border-indigo-500 text-white'
                          : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700'
                      }`}
                    >
                      <div className="font-semibold text-white mb-0.5">
                        {addr.address_line_1}
                      </div>
                      <div>
                        {addr.city}, {addr.state} {addr.postal_code}
                      </div>
                      <div className="text-[10px] text-slate-500 mt-1 uppercase font-mono">
                        {addr.country}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Payment Method Selector */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Payment Gateway (Payment Service :8004)
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { id: 'CREDIT_CARD', label: 'Credit Card', icon: CreditCard },
                    { id: 'UPI', label: 'UPI / Instant QR', icon: QrCode },
                    { id: 'ONE_CLICK', label: 'One-Click Demo', icon: Zap },
                  ].map(({ id, label, icon: Icon }) => (
                    <button
                      key={id}
                      type="button"
                      onClick={() => setPaymentMethod(id)}
                      className={`p-3 rounded-xl border text-xs font-medium flex flex-col items-center gap-2 transition-all ${
                        paymentMethod === id
                          ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-md'
                          : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700'
                      }`}
                    >
                      <Icon className="w-5 h-5 text-indigo-400" />
                      <span>{label}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* KEY SAGA TESTING FEATURE: SIMULATE PAYMENT FAILURE TOGGLE */}
              <div className="p-4 rounded-2xl bg-amber-950/20 border border-amber-500/30">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex gap-2.5">
                    <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <h4 className="text-xs font-bold text-amber-300">
                        Test Distributed Saga Compensation
                      </h4>
                      <p className="text-[11px] text-amber-200/80 leading-relaxed mt-0.5">
                        Toggle to simulate a payment gateway rejection. Watch the Order service execute compensation rollback to immediately release reserved inventory in <code>inventory_service (:8005)</code> and log error traces in Jaeger.
                      </p>
                    </div>
                  </div>

                  {/* Toggle Switch */}
                  <label className="relative inline-flex items-center cursor-pointer flex-shrink-0">
                    <input
                      type="checkbox"
                      checked={simulateFailure}
                      onChange={(e) => setSimulateFailure(e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-amber-500"></div>
                  </label>
                </div>
              </div>

              {/* Submit Trigger */}
              <button
                type="submit"
                disabled={isLoading}
                className={`w-full py-3.5 rounded-xl font-bold text-sm shadow-xl flex items-center justify-center gap-2 transition-all hover:scale-[1.01] active:scale-[0.99] ${
                  simulateFailure
                    ? 'bg-amber-600 hover:bg-amber-500 text-white shadow-amber-900/30'
                    : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-900/30'
                }`}
              >
                {isLoading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Executing Distributed Saga...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    <span>
                      {simulateFailure
                        ? `Submit & Test Failure Rollback - $${total.toFixed(2)}`
                        : `Place & Confirm Order - $${total.toFixed(2)}`}
                    </span>
                  </>
                )}
              </button>

            </form>
          ) : (
            /* ========================================================== */
            /* ORDER CONFIRMATION & SAGA VISUALIZER                       */
            /* ========================================================== */
            <div className="space-y-6">
              
              {/* Status Banner */}
              {orderResult.success ? (
                <div className="p-4 rounded-2xl bg-emerald-950/40 border border-emerald-500/40 flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center flex-shrink-0">
                    <CheckCircle2 className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white">
                      Order Confirmed & Committed
                    </h3>
                    <p className="text-xs text-emerald-300">
                      Order UUID: <code className="font-mono font-bold text-white">{orderResult.data?.uuid || 'ord-' + Date.now()}</code>
                    </p>
                  </div>
                </div>
              ) : (
                <div className="p-4 rounded-2xl bg-rose-950/40 border border-rose-500/40 flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-rose-500/20 text-rose-400 flex items-center justify-center flex-shrink-0">
                    <ShieldAlert className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white">
                      Payment Declined & Saga Compensated
                    </h3>
                    <p className="text-xs text-rose-300">
                      {orderResult.error || 'Simulated payment failure occurred.'}
                    </p>
                  </div>
                </div>
              )}

              {/* OPENTELEMETRY / JAEGER TRACE CORRELATION CARD */}
              <div className="p-4 rounded-2xl bg-slate-900 border border-indigo-500/30 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-2 text-xs font-semibold text-indigo-400 uppercase tracking-wider">
                    <Activity className="w-4 h-4 text-indigo-400 animate-pulse" />
                    Distributed Trace Context
                  </span>
                  <span className="text-[11px] font-mono text-slate-400">
                    Latency: {orderResult.latencyMs ? `${orderResult.latencyMs}ms` : 'Recorded'}
                  </span>
                </div>

                <div className="flex items-center justify-between gap-2 p-2.5 rounded-xl bg-black/50 border border-slate-800">
                  <div className="truncate">
                    <span className="block text-[10px] text-slate-500 uppercase font-mono">
                      W3C Trace ID
                    </span>
                    <span className="text-xs font-mono font-bold text-slate-200 select-all">
                      {orderResult.traceId || '4bf92f3577b34da6a3ce929d0e0e4736'}
                    </span>
                  </div>
                  <button
                    onClick={() => copyTraceId(orderResult.traceId)}
                    className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs flex items-center gap-1 transition-colors"
                  >
                    <Copy className="w-3.5 h-3.5" />
                    <span className="text-[10px]">{copiedTrace ? 'Copied' : 'Copy'}</span>
                  </button>
                </div>

                {/* Direct Clickable Jaeger UI Link */}
                <a
                  href={getJaegerTraceUrl(orderResult.traceId)}
                  target="_blank"
                  rel="noreferrer"
                  className="w-full py-2 px-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs flex items-center justify-center gap-2 shadow-md transition-all hover:scale-[1.01]"
                >
                  <Activity className="w-3.5 h-3.5" />
                  <span>Open Full Trace in Jaeger UI (localhost:16686)</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>

              {/* SAGA ORCHESTRATION 5-STEP TIMELINE */}
              <div>
                <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">
                  Distributed Saga Execution Pipeline
                </h4>
                <div className="space-y-2">
                  {[
                    {
                      step: '1. Order Service (:8003)',
                      detail: 'Created initial order draft in MySQL database',
                      status: 'COMPLETED',
                      color: 'emerald',
                    },
                    {
                      step: '2. Inventory Service (:8005)',
                      detail: 'Stock reserved atomically in warehouse pool',
                      status: 'COMPLETED',
                      color: 'emerald',
                    },
                    {
                      step: '3. Payment Service (:8004)',
                      detail: orderResult.success
                        ? `Transaction authorized via ${paymentMethod}`
                        : 'Simulated payment failure (CARD_DECLINED)',
                      status: orderResult.success ? 'COMPLETED' : 'FAILED',
                      color: orderResult.success ? 'emerald' : 'rose',
                    },
                    {
                      step: '4. Inventory Service (:8005)',
                      detail: orderResult.success
                        ? 'Reserved stock permanently committed to order'
                        : 'Compensation: Released reserved stock back to available pool',
                      status: orderResult.success ? 'COMMITTED' : 'COMPENSATED',
                      color: orderResult.success ? 'emerald' : 'amber',
                    },
                    {
                      step: '5. Notification Service (:8006)',
                      detail: orderResult.success
                        ? 'Dispatched ORDER_CONFIRMATION email notification'
                        : 'Dispatched ORDER_FAILURE notification to customer',
                      status: 'DELIVERED',
                      color: 'emerald',
                    },
                  ].map((s, idx) => (
                    <div
                      key={idx}
                      className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between text-xs"
                    >
                      <div className="flex items-center gap-2.5">
                        <span
                          className={`w-2 h-2 rounded-full ${
                            s.color === 'emerald'
                              ? 'bg-emerald-400'
                              : s.color === 'rose'
                              ? 'bg-rose-400'
                              : 'bg-amber-400'
                          }`}
                        />
                        <div>
                          <span className="font-semibold text-white block">{s.step}</span>
                          <span className="text-[11px] text-slate-400">{s.detail}</span>
                        </div>
                      </div>
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                          s.color === 'emerald'
                            ? 'bg-emerald-950 text-emerald-300'
                            : s.color === 'rose'
                            ? 'bg-rose-950 text-rose-300'
                            : 'bg-amber-950 text-amber-300'
                        }`}
                      >
                        {s.status}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Action */}
              <button
                onClick={() => {
                  setOrderResult(null);
                  onClose();
                }}
                className="w-full py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-medium text-xs transition-colors"
              >
                Back to Shopping
              </button>

            </div>
          )}
        </div>

      </div>
    </div>
  );
}

