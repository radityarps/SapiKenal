<script lang="ts">
  import { enhance } from '$app/forms';
  import type { SubmitFunction } from '@sveltejs/kit';
  import PasswordField from '$lib/components/PasswordField.svelte';
  import type { ActionData } from './$types';

  export let form: ActionData;

  let isSubmitting = false;
  const enhanceLogin: SubmitFunction = () => {
    isSubmitting = true;
    return async ({ result, update }) => {
      await update();
      isSubmitting = false;
      if (result.type === 'failure') {
        window.dispatchEvent(new CustomEvent('sapikenal:toast', { detail: { message: 'Login gagal. Periksa kembali kredensial Anda.', tone: 'error' } }));
      }
    };
  };
</script>

<svelte:head>
  <title>Login — SapiKenal Admin</title>
  <meta name="description" content="Login administrator SapiKenal" />
</svelte:head>

<div class="grid min-h-dvh place-items-center bg-[#f3f7f4] p-6">
  <section class="w-full max-w-[27rem] rounded-[1.25rem] border border-[#d7e7dc] bg-white p-9 shadow-[0_1.5rem_4rem_rgba(23,49,42,.08)]" aria-labelledby="login-title">
    <p class="mb-1 mt-5 text-xs font-extrabold uppercase tracking-[.14em] text-[#18794e]">SapiKenal</p>
    <h1 id="login-title" class="m-0 text-[2rem] font-bold tracking-[-.04em]">Dashboard</h1>
    <p class="leading-relaxed text-[#587069]">Kelola operasional dan konten deteksi dini secara aman.</p>

    {#if form?.message}
      <div class="mt-4 rounded-lg border border-[#f1cdd2] bg-[#fbf0f2] px-3 py-3 text-sm text-[#8b2f2f]" role="alert">{form.message}</div>
    {/if}

    <form class="mt-7 grid gap-2" method="POST" use:enhance={enhanceLogin} aria-busy={isSubmitting}>
      <label class="mt-1 text-sm font-bold" for="email">Email</label>
      <input class="w-full" id="email" name="email" type="email" autocomplete="username" value={form?.email ?? ''} required disabled={isSubmitting} />

      <PasswordField id="password" name="password" label="Kata sandi" autocomplete="current-password" required disabled={isSubmitting} />

      <button class="mt-3 min-h-11 w-full rounded-lg bg-[#18794e] px-4 py-3 text-sm font-extrabold text-white hover:bg-[#12623f]" type="submit" disabled={isSubmitting}>{isSubmitting ? 'Memeriksa…' : 'Masuk ke dashboard'}</button>
    </form>
  </section>
</div>
