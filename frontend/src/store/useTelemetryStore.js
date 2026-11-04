import { create } from 'zustand';
import { telemetryHub } from '../services/telemetry';

export const useTelemetryStore = create((set, get) => {
  // Subscribe to live client telemetry hub updates
  telemetryHub.subscribe((traces) => {
    set({ traces: [...traces] });
  });

  return {
    isOpen: false,
    traces: telemetryHub.getTraces(),
    activeFilter: 'all',

    toggle: () => set((state) => ({ isOpen: !state.isOpen })),
    open: () => set({ isOpen: true }),
    close: () => set({ isOpen: false }),

    setFilter: (filter) => set({ activeFilter: filter }),
    clear: () => {
      telemetryHub.clear();
      set({ traces: [] });
    },
  };
});

