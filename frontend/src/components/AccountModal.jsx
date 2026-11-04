import React, { useState, useEffect } from 'react';
import {
  X,
  User,
  MapPin,
  Package,
  LogOut,
  ShieldCheck,
  Plus,
  Clock,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { useAuthStore } from '../store/useAuthStore';
import { useNotificationStore } from '../store/useNotificationStore';
import { api } from '../services/api';

export default function AccountModal() {
  const { user, isAccountModalOpen, closeAccountModal, savedAddresses, addAddress, logout } = useAuthStore();
  const { addToast } = useNotificationStore();

  const [activeTab, setActiveTab] = useState('profile'); // 'profile' | 'orders' | 'addresses'
  const [orders, setOrders] = useState([]);
  const [loadingOrders, setLoadingOrders] = useState(false);
  const [newAddressLine, setNewAddressLine] = useState('');
  const [newCity, setNewCity] = useState('');
  const [newState, setNewState] = useState('');
  const [newPostal, setNewPostal] = useState('');

  useEffect(() => {
    if (isAccountModalOpen && user?.uuid) {
      loadOrders();
    }
  }, [isAccountModalOpen, user]);

  const loadOrders = async () => {
    setLoadingOrders(true);
    try {
      const data = await api.order.listOrders(user?.uuid);
      setOrders(data);
    } catch (err) {
      console.warn('Order list fallback:', err.message);
    } finally {
      setLoadingOrders(false);
    }
  };

  const handleAddAddress = (e) => {
    e.preventDefault();
    if (!newAddressLine.trim() || !newCity.trim()) return;

    addAddress({
      address_line_1: newAddressLine.trim(),
      city: newCity.trim(),
      state: newState.trim().toUpperCase() || 'CA',
      postal_code: newPostal.trim() || '94105',
      country: 'United States',
    });

    setNewAddressLine('');
    setNewCity('');
    setNewState('');
    setNewPostal('');

    addToast('Address Added', 'New shipping address added to your address book.', 'success');
  };

  if (!isAccountModalOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/80 backdrop-blur-md animate-fade-in">
      <div
        className="relative w-full max-w-2xl rounded-3xl glass-dropdown border border-slate-700/80 shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-6 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-indigo-600 flex items-center justify-center font-bold text-white text-base">
              {(user?.first_name || user?.username || 'U')[0].toUpperCase()}
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">
                {user?.full_name || user?.username || 'Customer Account'}
              </h2>
              <p className="text-xs text-slate-400">{user?.email}</p>
            </div>
          </div>

          <button
            onClick={closeAccountModal}
            className="p-2 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-slate-800 bg-slate-900/50 px-6">
          {[
            { id: 'profile', label: 'Profile Details', icon: User },
            { id: 'orders', label: 'Order History', icon: Package },
            { id: 'addresses', label: 'Shipping Addresses', icon: MapPin },
          ].map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`flex items-center gap-2 py-3 px-4 text-xs font-semibold border-b-2 transition-all ${
                activeTab === id
                  ? 'border-indigo-500 text-white'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{label}</span>
            </button>
          ))}
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto flex-1">
          {activeTab === 'profile' && (
            <div className="space-y-4">
              <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 grid grid-cols-2 gap-4 text-xs">
                <div>
                  <span className="text-slate-500 block mb-1">Customer Name</span>
                  <span className="font-semibold text-white">
                    {user?.first_name ? `${user.first_name} ${user.last_name || ''}` : user?.username}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block mb-1">Email Address</span>
                  <span className="font-semibold text-white truncate block">
                    {user?.email}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block mb-1">Account Role</span>
                  <span className="font-mono text-emerald-400 uppercase font-semibold">
                    {user?.role || 'CUSTOMER'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block mb-1">Verification Status</span>
                  <span className="inline-flex items-center gap-1 text-emerald-400 font-semibold">
                    <ShieldCheck className="w-3.5 h-3.5" /> Verified User
                  </span>
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-indigo-950/20 border border-indigo-500/20 text-xs text-indigo-300">
                <span className="font-bold block mb-1">OpenTelemetry User Context</span>
                Your user UUID (<code>{user?.uuid || 'usr-demo-01'}</code>) is automatically injected as an attribute on all backend trace spans (<code>user.uuid</code>) for security tracking and distributed correlation.
              </div>

              <div className="pt-4 border-t border-slate-800 flex justify-end">
                <button
                  onClick={logout}
                  className="px-4 py-2 rounded-xl bg-rose-950/60 hover:bg-rose-900/60 text-rose-300 border border-rose-800/60 text-xs font-semibold flex items-center gap-2 transition-colors"
                >
                  <LogOut className="w-3.5 h-3.5" /> Sign Out
                </button>
              </div>
            </div>
          )}

          {activeTab === 'orders' && (
            <div>
              {loadingOrders ? (
                <div className="text-center py-8 text-xs text-slate-400">Loading order history...</div>
              ) : orders.length === 0 ? (
                <div className="text-center py-12">
                  <Package className="w-10 h-10 text-slate-600 mx-auto mb-2" />
                  <p className="text-xs text-slate-400">No orders placed yet in this session.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {orders.map((ord) => (
                    <div
                      key={ord.uuid}
                      className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 flex items-center justify-between text-xs"
                    >
                      <div>
                        <span className="font-mono text-indigo-300 block font-semibold mb-0.5">
                          Order #{ord.uuid.slice(0, 8)}
                        </span>
                        <span className="text-slate-400 text-[11px]">
                          {ord.created_at ? new Date(ord.created_at).toLocaleDateString() : 'Recent'}
                        </span>
                      </div>
                      <div className="text-right">
                        <span className="font-mono font-bold text-white block mb-1">
                          ${Number(ord.total_amount).toFixed(2)}
                        </span>
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                            ord.status === 'CONFIRMED'
                              ? 'bg-emerald-950 text-emerald-300'
                              : 'bg-slate-800 text-slate-400'
                          }`}
                        >
                          {ord.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'addresses' && (
            <div className="space-y-4">
              <div className="space-y-2">
                {savedAddresses.map((addr) => (
                  <div
                    key={addr.uuid}
                    className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-300"
                  >
                    <div className="font-semibold text-white">{addr.address_line_1}</div>
                    <div>{addr.city}, {addr.state} {addr.postal_code}</div>
                    <span className="text-[10px] text-slate-500 uppercase">{addr.country}</span>
                  </div>
                ))}
              </div>

              {/* Add New Address Form */}
              <form onSubmit={handleAddAddress} className="p-4 rounded-2xl bg-slate-900/40 border border-slate-800 space-y-3">
                <span className="text-xs font-semibold text-white block">Add Shipping Address</span>
                <input
                  type="text"
                  placeholder="Street Address"
                  value={newAddressLine}
                  onChange={(e) => setNewAddressLine(e.target.value)}
                  className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
                <div className="grid grid-cols-3 gap-2">
                  <input
                    type="text"
                    placeholder="City"
                    value={newCity}
                    onChange={(e) => setNewCity(e.target.value)}
                    className="px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                  <input
                    type="text"
                    placeholder="State"
                    value={newState}
                    onChange={(e) => setNewState(e.target.value)}
                    className="px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                  <input
                    type="text"
                    placeholder="Postal Code"
                    value={newPostal}
                    onChange={(e) => setNewPostal(e.target.value)}
                    className="px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>
                <button
                  type="submit"
                  className="w-full py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors"
                >
                  <Plus className="w-3.5 h-3.5" /> Save Address
                </button>
              </form>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}

