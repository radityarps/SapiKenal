<script lang="ts">
  import { page } from '$app/state';
  import { onMount } from 'svelte';

  let message = $state('');
  let tone = $state<'success' | 'error'>('success');
  let timer: ReturnType<typeof setTimeout>;

  function show(nextMessage: string, nextTone: 'success' | 'error' = 'success') {
    clearTimeout(timer);
    message = nextMessage;
    tone = nextTone;
    timer = setTimeout(() => (message = ''), 5000);
  }

  onMount(() => {
    const listener = (event: Event) => {
      const detail = (event as CustomEvent<{ message: string; tone?: 'success' | 'error' }>).detail;
      if (detail?.message) show(detail.message, detail.tone);
    };
    window.addEventListener('sapikenal:toast', listener);
    return () => window.removeEventListener('sapikenal:toast', listener);
  });

  $effect(() => {
    const toast = page.url.searchParams.get('toast');
    if (toast) show(toast, page.url.searchParams.get('toastType') === 'error' ? 'error' : 'success');
  });
</script>

{#if message}
  <div class:toast-error={tone === 'error'} class="toast" role="status" aria-live="polite">
    {message}
  </div>
{/if}
