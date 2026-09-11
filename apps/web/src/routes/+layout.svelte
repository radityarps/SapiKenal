<script lang="ts">
  import '../app.css';
  import ToastHost from '$lib/components/ToastHost.svelte';
</script>

<svelte:head>
  <link rel="icon" href="/favicon.ico" sizes="any" />
  <link rel="icon" href="/logo.png" type="image/png" />
  <link rel="apple-touch-icon" href="/logo.png" />
</svelte:head>

<slot />
<ToastHost />
