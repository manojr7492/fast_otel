import React, { useState } from 'react';
import {
  ShoppingBag,
  Bell,
  User,
  Activity,
  Search,
  X,
  Layers,
  ChevronDown,
  LogOut,
  CheckCircle2,
  ExternalLink
} from 'lucide-react';
import { useAuthStore } from '../store/useAuthStore';
import { useCartStore } from '../store/useCartStore';
import { useNotificationStore } from '../store/useNotificationStore';
import { useTelemetryStore } from '../store/useTelemetryStore';

export default function Navbar({ searchQuery, setSearchQuery, selectedCategory, setSelectedCategory, categories = [] }) {
  const { user, isAuthenticated, openOtpModal, openAccountModal, logout } = useAuthStore();
  const { items, getItemCount, openCart } = useCartStore();
  const { unreadCount, toggleCenter } = useNotificationStore();
  const { traces, toggle: toggleTelemetry } = useTelemetryStore();
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);

  const totalItems = getItemCount();

  return (
    <header className="sticky top-0 z-40 w-full glass-panel border-b border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 gap-3 sm:gap-6">
          
          {/* Brand Logo & Architecture Pill */}
          <div className="flex items-center gap-3">
            <a href="#" className="flex items-center gap-2.5 group">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-emerald-400 p-0.5 shadow-lg shadow-indigo-500/20 group-hover:scale-105 transition-transform">
                <div className="w-full h-full bg-[#090D16] rounded-[10px] flex items-center justify-center">
                  <Layers className="w-5 h-5 text-indigo-400 group-hover:text-emerald-400 transition-colors" />
                </div>
              </div>
              <div className="hidden sm:block">
                <span className="text-lg font-bold bg-gradient-to-r from-white via-slate-200 to-indigo-200 bg-clip-text text-transparent">
                  ShopSphere
                </span>
                <span className="block text-[10px] uppercase font-semibold tracking-wider text-emerald-400">
                  Microservices Core
                </span>
              </div>
            </a>

            {/* Health Status Indicator */}
            <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-800/60 border border-slate-700/60 text-[11px] text-slate-300">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>6 Services Online</span>
            </div>
          </div>

          {/* Global Search Bar with Live Clear */}
          <div className="flex-1 max-w-md hidden md:block">
            <div className="relative">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search MacBook, Sony ANC, Keyboards..."
                className="w-full pl-9 pr-9 py-2 bg-slate-900/80 border border-slate-700/70 rounded-xl text-sm text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>

          {/* Action Tools: Observability, Notifications, Cart, Auth */}
          <div className="flex items-center gap-2 sm:gap-3">
            
            {/* OpenTelemetry Jaeger Inspector Trigger */}
            <button
              onClick={toggleTelemetry}
              title="OpenTelemetry Distributed Tracing Inspector"
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl bg-indigo-950/40 border border-indigo-700/50 hover:bg-indigo-900/50 text-indigo-300 text-xs font-medium transition-all"
            >
              <Activity className="w-4 h-4 text-indigo-400 animate-pulse" />
              <span className="hidden sm:inline font-mono">Traces</span>
              <span className="px-1.5 py-0.5 rounded-full bg-indigo-500/20 text-[10px] font-mono font-bold text-indigo-300">
                {traces.length}
              </span>
            </button>

            {/* In-App Notifications Bell */}
            <button
              onClick={toggleCenter}
              title="Notification Center (:8006)"
              className="relative p-2 rounded-xl text-slate-300 hover:text-white hover:bg-slate-800/80 border border-transparent hover:border-slate-700 transition-all"
            >
              <Bell className="w-5 h-5" />
              {unreadCount > 0 && (
                <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-indigo-500 ring-2 ring-[#090D16] animate-ping" />
              )}
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 px-1.5 py-0.2 rounded-full bg-indigo-600 text-[10px] font-bold text-white shadow-sm">
                  {unreadCount}
                </span>
              )}
            </button>

            {/* Shopping Cart Trigger */}
            <button
              onClick={openCart}
              className="relative flex items-center gap-2 px-3 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-white font-medium text-xs sm:text-sm shadow-md shadow-emerald-900/30 transition-all hover:scale-[1.02] active:scale-[0.98]"
            >
              <ShoppingBag className="w-4 h-4" />
              <span className="hidden sm:inline font-medium">Cart</span>
              {totalItems > 0 && (
                <span className="px-1.5 py-0.5 rounded-full bg-emerald-950/60 text-emerald-200 text-xs font-bold font-mono">
                  {totalItems}
                </span>
              )}
            </button>

            {/* User Session / OTP Login */}
            {isAuthenticated ? (
              <div className="relative">
                <button
                  onClick={() => setUserDropdownOpen(!userDropdownOpen)}
                  className="flex items-center gap-2 p-1.5 sm:px-3 sm:py-1.5 rounded-xl bg-slate-800/70 border border-slate-700/80 hover:bg-slate-700/60 text-sm text-slate-200 transition-all"
                >
                  <div className="w-7 h-7 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white text-xs">
                    {(user?.first_name || user?.username || 'U')[0].toUpperCase()}
                  </div>
                  <span className="hidden md:inline font-medium text-xs">
                    {user?.first_name || user?.username}
                  </span>
                  <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                </button>

                {userDropdownOpen && (
                  <div className="absolute right-0 mt-2 w-56 rounded-2xl glass-dropdown shadow-2xl p-2 z-50 animate-slide-up">
                    <div className="px-3 py-2 border-b border-slate-800">
                      <p className="text-xs font-semibold text-white truncate">
                        {user?.full_name || user?.username}
                      </p>
                      <p className="text-[11px] text-slate-400 truncate">{user?.email}</p>
                      <div className="mt-1 flex items-center gap-1 text-[10px] text-emerald-400 font-mono">
                        <CheckCircle2 className="w-3 h-3" /> Customer Verified
                      </div>
                    </div>
                    <div className="py-1">
                      <button
                        onClick={() => {
                          setUserDropdownOpen(false);
                          openAccountModal();
                        }}
                        className="w-full flex items-center gap-2 px-3 py-2 text-xs text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
                      >
                        <User className="w-4 h-4 text-slate-400" /> Account & Orders
                      </button>
                      <a
                        href="http://localhost:16686"
                        target="_blank"
                        rel="noreferrer"
                        className="w-full flex items-center justify-between px-3 py-2 text-xs text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
                      >
                        <span className="flex items-center gap-2">
                          <Activity className="w-4 h-4 text-indigo-400" /> Jaeger Tracing UI
                        </span>
                        <ExternalLink className="w-3 h-3 text-slate-400" />
                      </a>
                    </div>
                    <div className="pt-1 border-t border-slate-800">
                      <button
                        onClick={() => {
                          setUserDropdownOpen(false);
                          logout();
                        }}
                        className="w-full flex items-center gap-2 px-3 py-2 text-xs text-rose-400 hover:bg-rose-950/40 rounded-lg transition-colors"
                      >
                        <LogOut className="w-4 h-4" /> Sign Out
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <button
                onClick={openOtpModal}
                className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs sm:text-sm shadow-md shadow-indigo-900/30 transition-all hover:scale-[1.02] active:scale-[0.98]"
              >
                <User className="w-4 h-4" />
                <span>Demo OTP Login</span>
              </button>
            )}

          </div>

        </div>

        {/* Mobile Search input */}
        <div className="pb-3 md:hidden">
          <div className="relative">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search products..."
              className="w-full pl-9 pr-9 py-2 bg-slate-900/90 border border-slate-800 rounded-xl text-sm text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>

      </div>
    </header>
  );
}

