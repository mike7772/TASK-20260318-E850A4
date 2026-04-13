import { useUiStore } from "../app/store/uiStore";

export function useToast() {
  const store = useUiStore();
  return {
    success: (message: string) => store.pushToast(message, "success"),
    error: (message: string) => store.pushToast(message, "error")
  };
}
