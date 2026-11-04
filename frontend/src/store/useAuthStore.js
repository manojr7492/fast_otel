import { create } from 'zustand';
import { api } from '../services/api';
import { MOCK_SAVED_ADDRESSES } from '../data/mockData';

export const useAuthStore = create((set, get) => {
  // Load initial session from localStorage
  const savedUser = localStorage.getItem('auth_user');
  const savedAccessToken = localStorage.getItem('auth_access_token');
  const savedRefreshToken = localStorage.getItem('auth_refresh_token');

  return {
    user: savedUser ? JSON.parse(savedUser) : null,
    accessToken: savedAccessToken || null,
    refreshToken: savedRefreshToken || null,
    isAuthenticated: !!savedAccessToken,
    isOtpModalOpen: false,
    isAccountModalOpen: false,
    savedAddresses: MOCK_SAVED_ADDRESSES,

    // On-Screen OTP demo state
    demoOtp: {
      code: '',
      identifier: '',
      isVisible: false,
      expiresAt: 0,
      loading: false,
    },

    openOtpModal: () => set({ isOtpModalOpen: true }),
    closeOtpModal: () => set({ isOtpModalOpen: false }),

    openAccountModal: () => set({ isAccountModalOpen: true }),
    closeAccountModal: () => set({ isAccountModalOpen: false }),

    // Step 1: Request 6-digit OTP
    requestOtp: async (identifier) => {
      set((state) => ({ demoOtp: { ...state.demoOtp, loading: true } }));
      try {
        const resp = await api.auth.requestOtp(identifier);
        const code = resp.otp || '849201';
        const expiresAt = Date.now() + (resp.expires_in || 300) * 1000;

        set({
          demoOtp: {
            code,
            identifier,
            isVisible: true,
            expiresAt,
            loading: false,
          },
        });
        return { success: true, code };
      } catch (err) {
        // Fallback demo OTP code
        const fallbackCode = '849201';
        set({
          demoOtp: {
            code: fallbackCode,
            identifier,
            isVisible: true,
            expiresAt: Date.now() + 300000,
            loading: false,
          },
        });
        return { success: true, code: fallbackCode };
      }
    },

    // Step 2: Verify OTP and establish real session
    verifyOtp: async (identifier, code) => {
      set((state) => ({ demoOtp: { ...state.demoOtp, loading: true } }));
      try {
        const authData = await api.auth.verifyOtp(identifier, code);
        const user = authData.user || {
          uuid: `usr-${Date.now()}`,
          email: identifier.includes('@') ? identifier : `${identifier}@ecommerce.io`,
          username: identifier.split('@')[0],
          first_name: 'Satya',
          last_name: 'Customer',
          role: 'CUSTOMER',
        };

        const accessToken = authData.access_token;
        const refreshToken = authData.refresh_token;

        localStorage.setItem('auth_user', JSON.stringify(user));
        localStorage.setItem('auth_access_token', accessToken);
        localStorage.setItem('auth_refresh_token', refreshToken);

        set({
          user,
          accessToken,
          refreshToken,
          isAuthenticated: true,
          isOtpModalOpen: false,
          demoOtp: {
            code: '',
            identifier: '',
            isVisible: false,
            expiresAt: 0,
            loading: false,
          },
        });

        return { success: true, user };
      } catch (err) {
        set((state) => ({ demoOtp: { ...state.demoOtp, loading: false } }));
        throw err;
      }
    },

    logout: () => {
      localStorage.removeItem('auth_user');
      localStorage.removeItem('auth_access_token');
      localStorage.removeItem('auth_refresh_token');
      set({
        user: null,
        accessToken: null,
        refreshToken: null,
        isAuthenticated: false,
        isAccountModalOpen: false,
      });
    },

    addAddress: (address) => {
      set((state) => ({
        savedAddresses: [
          ...state.savedAddresses,
          {
            uuid: `addr-${Date.now()}`,
            ...address,
            is_default: state.savedAddresses.length === 0,
          },
        ],
      }));
    },
  };
});

