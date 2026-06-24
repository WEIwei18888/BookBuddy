import { create } from 'zustand'

export const useStore = create((set) => ({
  toast: null,
  setToast: (message, type = 'info') => set({ toast: { message, type } }),
  clearToast: () => set({ toast: null }),
}))

