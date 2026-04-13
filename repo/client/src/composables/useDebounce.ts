import { ref, watch } from "vue";

export function useDebounce<T>(source: () => T, delay = 250) {
  const value = ref(source()) as { value: T };
  let timer: number | undefined;
  watch(source, (next) => {
    if (timer) window.clearTimeout(timer);
    timer = window.setTimeout(() => {
      value.value = next;
    }, delay);
  });
  return value;
}
