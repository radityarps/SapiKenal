<script lang="ts">
  import { enhance } from '$app/forms';
  import type { SubmitFunction } from '@sveltejs/kit';
  import AdminShell from '$lib/components/AdminShell.svelte';
  import PasswordField from '$lib/components/PasswordField.svelte';

  export let data: { user: App.Locals['user'] };
  export let form: { success?: boolean; error?: string } | null;

  let isSubmitting = false;
  const enhancePassword: SubmitFunction = () => {
    isSubmitting = true;
    return async ({ result, update }) => {
      await update();
      isSubmitting = false;
      window.dispatchEvent(new CustomEvent('sapikenal:toast', {
        detail: result.type === 'success'
          ? { message: 'Password berhasil diubah. Silakan login kembali.', tone: 'success' }
          : { message: 'Password gagal diubah.', tone: 'error' }
      }));
    };
  };
</script>

<svelte:head><title>Akun — SapiKenal Admin</title></svelte:head>
<AdminShell title="Akun admin" eyebrow="Pengaturan akun" active="/account" user={data.user}>
  <section class="page-intro"><p class="muted">Perubahan password akan mencabut seluruh sesi akun ini.</p></section>
  {#if form?.error}<p class="error">{form.error}</p>{/if}
  {#if form?.success}<p class="notice">Password berhasil diubah. Silakan login kembali.</p>{/if}
  <section class="panel max-w-lg"><h2 class="mb-4 text-base font-bold">Ubah password</h2><form class="grid gap-3" method="POST" action="?/changePassword" use:enhance={enhancePassword} aria-busy={isSubmitting}><PasswordField id="current-password" name="current_password" label="Password saat ini" autocomplete="current-password" required disabled={isSubmitting} /><PasswordField id="new-password" name="new_password" label="Password baru" autocomplete="new-password" minlength={12} required disabled={isSubmitting} /><button type="submit" disabled={isSubmitting}>{isSubmitting ? 'Menyimpan…' : 'Simpan password'}</button></form></section>
</AdminShell>
