<script lang="ts">
  import '../app.css';
  import ToastHost from '$lib/components/ToastHost.svelte';
</script>

<svelte:head>
  <link rel="icon" href="/logo.png" type="image/png" />
</svelte:head>

<slot />
<ToastHost />
