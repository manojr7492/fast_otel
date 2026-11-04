import axios from 'axios';
import { createW3CTraceparent, telemetryHub } from './telemetry';
import { MOCK_PRODUCTS, MOCK_CATEGORIES, MOCK_SAVED_ADDRESSES } from '../data/mockData';

// Base URLs defaulting to direct ports with fallback to Vite proxy paths
const USER_API_URL = import.meta.env.VITE_USER_API_URL || 'http://localhost:8001';
const PRODUCT_API_URL = import.meta.env.VITE_PRODUCT_API_URL || 'http://localhost:8002';
const ORDER_API_URL = import.meta.env.VITE_ORDER_API_URL || 'http://localhost:8003';
const PAYMENT_API_URL = import.meta.env.VITE_PAYMENT_API_URL || 'http://localhost:8004';
const INVENTORY_API_URL = import.meta.env.VITE_INVENTORY_API_URL || 'http://localhost:8005';
const NOTIFICATION_API_URL = import.meta.env.VITE_NOTIFICATION_API_URL || 'http://localhost:8006';

// Attach distributed tracing and auth interceptors to any Axios instance
function setupInterceptors(client, serviceName) {
  client.interceptors.request.use(
    (config) => {
      // 1. Generate standard W3C Trace Context
      const { traceId, spanId, traceparent } = createW3CTraceparent();
      const requestId = `req-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;

      config.headers = config.headers || {};
      config.headers['traceparent'] = traceparent;
      config.headers['X-Request-ID'] = requestId;

      // 2. Attach JWT bearer token if user session exists
      const token = localStorage.getItem('auth_access_token');
      if (token && !config.headers['Authorization']) {
        config.headers['Authorization'] = `Bearer ${token}`;
      }

      config.metadata = {
        startTime: performance.now(),
        traceId,
        spanId,
        service: serviceName,
        endpoint: config.url || '',
        method: config.method || 'GET',
      };

      return config;
    },
    (error) => Promise.reject(error)
  );

  client.interceptors.response.use(
    (response) => {
      const meta = response.config.metadata || {};
      const durationMs = meta.startTime ? Math.round(performance.now() - meta.startTime) : 0;
      const backendTraceId = response.headers['x-trace-id'] || response.headers['X-Trace-ID'] || meta.traceId;

      telemetryHub.recordTrace({
        traceId: meta.traceId,
        spanId: meta.spanId,
        backendTraceId,
        service: meta.service,
        endpoint: meta.endpoint,
        method: meta.method,
        status: response.status,
        durationMs,
      });

      return response;
    },
    async (error) => {
      const config = error.config || {};
      const meta = config.metadata || {};
      const durationMs = meta.startTime ? Math.round(performance.now() - meta.startTime) : 0;
      const status = error.response ? error.response.status : 503;
      const backendTraceId = error.response?.headers?.['x-trace-id'] || meta.traceId;

      telemetryHub.recordTrace({
        traceId: meta.traceId,
        spanId: meta.spanId,
        backendTraceId,
        service: meta.service || serviceName,
        endpoint: meta.endpoint || config.url || '',
        method: meta.method || config.method || 'GET',
        status,
        durationMs,
        error: error.response?.data?.message || error.message,
      });

      // Handle automatic token refresh on 401
      if (status === 401 && !config._retry) {
        config._retry = true;
        const refreshToken = localStorage.getItem('auth_refresh_token');
        if (refreshToken) {
          try {
            const refreshResp = await axios.post(`${USER_API_URL}/api/v1/auth/refresh`, {
              refresh_token: refreshToken,
            });
            const newAccessToken = refreshResp.data?.data?.access_token;
            if (newAccessToken) {
              localStorage.setItem('auth_access_token', newAccessToken);
              config.headers['Authorization'] = `Bearer ${newAccessToken}`;
              return client(config);
            }
          } catch (refreshErr) {
            localStorage.removeItem('auth_access_token');
            localStorage.removeItem('auth_refresh_token');
            localStorage.removeItem('auth_user');
          }
        }
      }

      return Promise.reject(error);
    }
  );

  return client;
}

// Dedicated microservice API clients
export const userClient = setupInterceptors(
  axios.create({ baseURL: USER_API_URL, timeout: 6000 }),
  'user-service'
);

export const productClient = setupInterceptors(
  axios.create({ baseURL: PRODUCT_API_URL, timeout: 6000 }),
  'product-service'
);

export const orderClient = setupInterceptors(
  axios.create({ baseURL: ORDER_API_URL, timeout: 8000 }),
  'order-service'
);

export const paymentClient = setupInterceptors(
  axios.create({ baseURL: PAYMENT_API_URL, timeout: 6000 }),
  'payment-service'
);

export const inventoryClient = setupInterceptors(
  axios.create({ baseURL: INVENTORY_API_URL, timeout: 6000 }),
  'inventory-service'
);

export const notificationClient = setupInterceptors(
  axios.create({ baseURL: NOTIFICATION_API_URL, timeout: 6000 }),
  'notification-service'
);

// High-level API Service Facade with Resilient Fallbacks
export const api = {
  // -------------------------------------------------------------
  // User & Auth Service (:8001)
  // -------------------------------------------------------------
  auth: {
    async requestOtp(loginIdentifier) {
      try {
        const resp = await userClient.post('/api/v1/auth/otp/request', {
          login_identifier: loginIdentifier,
        });
        return resp.data?.data || resp.data;
      } catch (err) {
        console.warn('Backend user_service OTP request fallback activated:', err.message);
        // Resilient fallback for demo presentation
        const mockOtp = String(Math.floor(100000 + Math.random() * 900000));
        return {
          otp: mockOtp,
          login_identifier: loginIdentifier,
          expires_in: 300,
          message: 'Demo Mode: Verification OTP generated locally.',
        };
      }
    },

    async verifyOtp(loginIdentifier, otpCode) {
      try {
        const resp = await userClient.post('/api/v1/auth/otp/verify', {
          login_identifier: loginIdentifier,
          otp_code: otpCode,
        });
        return resp.data?.data || resp.data;
      } catch (err) {
        console.warn('Backend user_service OTP verify fallback activated:', err.message);
        // Resilient fallback creating simulated authenticated JWT session
        const username = loginIdentifier.split('@')[0];
        return {
          access_token: `mock_jwt_access_${Date.now()}_${Math.random().toString(36)}`,
          refresh_token: `mock_jwt_refresh_${Date.now()}_${Math.random().toString(36)}`,
          token_type: 'bearer',
          expires_in: 1800,
          user: {
            uuid: `usr-${Date.now()}`,
            email: loginIdentifier.includes('@') ? loginIdentifier : `${loginIdentifier}@ecommerce.io`,
            username: username,
            first_name: username.charAt(0).toUpperCase() + username.slice(1),
            last_name: 'Customer',
            role: 'CUSTOMER',
            is_active: true,
            is_verified: true,
          },
        };
      }
    },

    async register(data) {
      const resp = await userClient.post('/api/v1/auth/register', data);
      return resp.data?.data || resp.data;
    },

    async getProfile() {
      try {
        const resp = await userClient.get('/api/v1/users/me');
        return resp.data?.data || resp.data;
      } catch (err) {
        const saved = localStorage.getItem('auth_user');
        return saved ? JSON.parse(saved) : null;
      }
    },

    async getAddresses() {
      try {
        const resp = await userClient.get('/api/v1/addresses/');
        return resp.data?.data || resp.data;
      } catch (err) {
        return MOCK_SAVED_ADDRESSES;
      }
    },
  },

  // -------------------------------------------------------------
  // Product & Catalog Service (:8002)
  // -------------------------------------------------------------
  catalog: {
    async getCategories() {
      try {
        const resp = await productClient.get('/api/v1/categories/');
        const categories = resp.data?.data || resp.data;
        return Array.isArray(categories) && categories.length > 0 ? categories : MOCK_CATEGORIES;
      } catch (err) {
        console.warn('Product service offline, using mock categories:', err.message);
        return MOCK_CATEGORIES;
      }
    },

    async getProducts(params = {}) {
      try {
        const resp = await productClient.get('/api/v1/products/', { params });
        const data = resp.data?.data?.items || resp.data?.data || resp.data;
        return Array.isArray(data) && data.length > 0 ? data : MOCK_PRODUCTS;
      } catch (err) {
        console.warn('Product service offline, using mock product catalog:', err.message);
        return MOCK_PRODUCTS;
      }
    },

    async getProductBySku(sku) {
      try {
        const resp = await productClient.get(`/api/v1/products/${sku}`);
        return resp.data?.data || resp.data;
      } catch (err) {
        return MOCK_PRODUCTS.find((p) => p.sku === sku) || MOCK_PRODUCTS[0];
      }
    },
  },

  // -------------------------------------------------------------
  // Inventory Service (:8005)
  // -------------------------------------------------------------
  inventory: {
    async checkStock(sku) {
      try {
        const resp = await inventoryClient.get(`/api/v1/inventory/${sku}`);
        return resp.data?.data || resp.data;
      } catch (err) {
        const found = MOCK_PRODUCTS.find((p) => p.sku === sku);
        return {
          sku,
          quantity: found?.inventory?.available_quantity || 25,
          reserved_quantity: 0,
          warehouse_location: found?.inventory?.warehouse_location || 'SAN-FRANCISCO-HUB',
        };
      }
    },

    async restock(sku, quantity = 50) {
      const resp = await inventoryClient.post('/api/v1/inventory/restock', {
        sku,
        quantity,
        warehouse_location: 'SAN-FRANCISCO-HUB',
      });
      return resp.data?.data || resp.data;
    },
  },

  // -------------------------------------------------------------
  // Order & Saga Checkout Service (:8003)
  // -------------------------------------------------------------
  order: {
    async checkout(payload) {
      // payload: { user_uuid, customer_email, customer_name, items, payment_method, simulate_payment_failure }
      try {
        const resp = await orderClient.post('/api/v1/orders/checkout', payload);
        const traceId = resp.headers['x-trace-id'] || resp.config?.metadata?.traceId;
        return {
          success: true,
          data: resp.data?.data || resp.data,
          traceId,
          latencyMs: resp.headers['x-process-time-ms'] || resp.config?.metadata?.durationMs,
        };
      } catch (err) {
        const traceId = err.response?.headers?.['x-trace-id'] || err.config?.metadata?.traceId;
        if (payload.simulate_payment_failure) {
          // Expected simulated failure
          return {
            success: false,
            simulatedFailure: true,
            error: err.response?.data?.message || 'Payment Declined: Card verification failed by issuer.',
            traceId,
            details: 'Saga compensation executed: Reserved inventory was rolled back automatically.',
          };
        }
        throw err;
      }
    },

    async listOrders(userUuid) {
      try {
        const resp = await orderClient.get('/api/v1/orders/', {
          params: { user_uuid: userUuid },
        });
        return resp.data?.data?.items || resp.data?.data || [];
      } catch (err) {
        return [];
      }
    },
  },

  // -------------------------------------------------------------
  // Payment Service (:8004)
  // -------------------------------------------------------------
  payment: {
    async getPayment(paymentUuid) {
      try {
        const resp = await paymentClient.get(`/api/v1/payments/${paymentUuid}`);
        return resp.data?.data || resp.data;
      } catch (err) {
        return null;
      }
    },
  },

  // -------------------------------------------------------------
  // Notification Service (:8006)
  // -------------------------------------------------------------
  notification: {
    async getHistory() {
      try {
        const resp = await notificationClient.get('/api/v1/notifications/history');
        return resp.data || [];
      } catch (err) {
        return [];
      }
    },
  },
};

