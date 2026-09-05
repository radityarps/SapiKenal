<script lang="ts">
  import { tick } from 'svelte';
  import { goto } from '$app/navigation';
  import { Eye, Search, X } from 'lucide-svelte';
  import AdminFilterSelect from '$lib/components/AdminFilterSelect.svelte';
  import AdminShell from '$lib/components/AdminShell.svelte';
  import DateRangeFilter from '$lib/components/DateRangeFilter.svelte';
  import TablePagination from '$lib/components/TablePagination.svelte';

  export let data: { user: App.Locals['user']; logs: any; filters: { search: string; action: string; status: string; date_from: string; date_to: string }; error: string | null };

  let selectedLog: any = null;
  let detailDialog: HTMLDialogElement | undefined;
  let search = data.filters.search;
  let searchTimer: ReturnType<typeof setTimeout>;

  const actionLabels: Record<string, string> = {
    login_succeeded: 'Login berhasil',
    login_failed: 'Login ditolak',
    session_refreshed: 'Sesi diperbarui',
    logout: 'Logout',
    logout_all: 'Logout semua sesi',
    password_changed: 'Password diubah',
    user_created: 'Pengguna dibuat',
    user_updated: 'Pengguna diperbarui',
    user_password_reset: 'Password pengguna direset',
    breed_profile_created: 'Profil jenis dibuat',
    breed_profile_updated: 'Profil jenis diperbarui',
    breed_profile_activated: 'Profil jenis diaktifkan',
    breed_profile_deactivated: 'Profil jenis dinonaktifkan',
    model_registered: 'Model didaftarkan',
    model_activate: 'Model diaktifkan',
    model_rollback: 'Model dikembalikan',
    model_activate_failed: 'Aktivasi model gagal',
    model_rollback_failed: 'Rollback model gagal',
    seed_admin_created: 'Admin awal dibuat',
    seed_admin_password_rotated: 'Password admin awal dirotasi'
  };

  const actionDescriptions: Record<string, string> = {
    login_succeeded: 'Administrator berhasil masuk ke Web Admin.',
    login_failed: 'Percobaan masuk ke Web Admin ditolak.',
    session_refreshed: 'Sesi administrator diperbarui.',
    logout: 'Administrator keluar dan sesi saat ini dicabut.',
    logout_all: 'Seluruh sesi administrator dicabut.',
    password_changed: 'Password akun administrator berhasil diperbarui.',
    user_created: 'Akun pengguna baru dibuat oleh administrator.',
    user_updated: 'Data atau akses akun pengguna diperbarui.',
    user_password_reset: 'Password pengguna direset dan sesi terkait dicabut.',
    breed_profile_created: 'Draft profil jenis baru dibuat.',
    breed_profile_updated: 'Revisi profil jenis dibuat.',
    breed_profile_activated: 'Profil jenis diterbitkan untuk konsumsi publik.',
    breed_profile_deactivated: 'Profil jenis ditarik dari publikasi.',
    model_registered: 'Versi model baru didaftarkan ke registri.',
    model_activate: 'Versi model dipilih sebagai model aktif.',
    model_rollback: 'Model aktif dikembalikan ke versi sebelumnya.',
    model_activate_failed: 'Model kandidat gagal diaktifkan.',
    model_rollback_failed: 'Model sebelumnya gagal dipulihkan.',
    seed_admin_created: 'Akun administrator awal dibuat oleh seeder.',
    seed_admin_password_rotated: 'Password administrator awal dirotasi secara eksplisit.'
  };

  const actionFilterItems = [
    { value: '__all__', label: 'Semua aktivitas' },
    { value: 'login_succeeded', label: 'Login berhasil' },
    { value: 'login_failed', label: 'Login ditolak' },
    { value: 'logout', label: 'Logout' },
    { value: 'password_changed', label: 'Password diubah' },
    { value: 'breed_profile_created', label: 'Profil jenis dibuat' },
    { value: 'breed_profile_activated', label: 'Profil jenis diaktifkan' },
    { value: 'breed_profile_deactivated', label: 'Profil jenis dinonaktifkan' },
    { value: 'model_registered', label: 'Model didaftarkan' },
    { value: 'model_activate', label: 'Model diaktifkan' },
    { value: 'model_rollback', label: 'Model dikembalikan' }
  ];
  const statusFilterItems = [
    { value: '__all__', label: 'Semua status' },
    { value: 'success', label: 'Berhasil' },
    { value: 'failed', label: 'Gagal' }
  ];

  const actionLabel = (action: string) => actionLabels[action] ?? action.replaceAll('_', ' ');
  const actionDescription = (action: string) => actionDescriptions[action] ?? `Aktivitas ${actionLabel(action)} dicatat oleh sistem.`;
  const actorName = (item: any) => item.actor_display_name || (item.actor_user_id ? 'Pengguna tidak tersedia' : 'Sistem');
  const statusLabel = (status: string) => status === 'success' ? 'Berhasil' : 'Gagal';
  const formatDate = (value: string) => new Intl.DateTimeFormat('id-ID', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value));
  const formatFields = (fields: Record<string, unknown> | null) => fields ? Object.entries(fields).map(([key, value]) => `${key}: ${String(value)}`).join(', ') : 'Tidak ada';

  async function openDetail(item: any) {
    selectedLog = item;
    await tick();
    detailDialog?.showModal();
  }

  function closeDetail() {
    detailDialog?.close();
  }

  function closeFromBackdrop(event: MouseEvent) {
    if (event.target === detailDialog) closeDetail();
  }

  function updateQuery(key: string, value: string) {
    const query = new URLSearchParams(window.location.search);
    value ? query.set(key, value) : query.delete(key);
    query.delete('page');
    goto(`?${query}`, { keepFocus: true, noScroll: true });
  }

  function debounceSearch(value: string) {
    search = value;
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => updateQuery('search', value.trim()), 350);
  }
  function updatePage(page: number) {
    const query = new URLSearchParams(window.location.search);
    query.set('page', String(page));
    goto(`?${query}`, { keepFocus: true, noScroll: true, invalidateAll: true });
  }

  function updateDateRange(range: { start: string; end: string }) {
    const query = new URLSearchParams(window.location.search);
    range.start ? query.set('date_from', range.start) : query.delete('date_from');
    range.end ? query.set('date_to', range.end) : query.delete('date_to');
    query.delete('page');
    goto(`?${query}`, { keepFocus: true, noScroll: true, invalidateAll: true });
  }
</script>

<svelte:head><title>Audit log — SapiKenal Admin</title></svelte:head>
<AdminShell title="Audit log" eyebrow="Jejak administratif" active="/audit-logs" user={data.user}>
  <section class="page-intro"><p class="muted">Log bersifat append-only. Informasi utama ditampilkan langsung, sedangkan metadata teknis tersedia pada detail.</p></section>
  {#if data.error}<p class="error">{data.error}</p>{/if}
  <div class="mt-4 grid gap-3 lg:grid-cols-[minmax(16rem,1fr)_minmax(24rem,1fr)]">
    <div>
      <label class="relative"><span>Cari log</span><Search class="pointer-events-none absolute bottom-3 left-3 text-[#718078]" size={16} aria-hidden="true" /><input class="w-full pl-9" type="search" value={search} placeholder="Aktor, aktivitas, resource, request ID" oninput={(event) => debounceSearch(event.currentTarget.value)} /></label>
    </div>
    <div class="grid gap-3 sm:grid-cols-3">
      <DateRangeFilter start={data.filters.date_from} end={data.filters.date_to} onChange={updateDateRange} />
      <AdminFilterSelect label="Aktivitas" value={data.filters.action} items={actionFilterItems} placeholder="Semua aktivitas" onChange={(value) => updateQuery('action', value)} />
      <AdminFilterSelect label="Status" value={data.filters.status} items={statusFilterItems} placeholder="Semua status" onChange={(value) => updateQuery('status', value)} />
    </div>
  </div>
  <section class="panel mt-3 p-0">
    {#if data.logs.items.length}
      <table class="table-fixed">
        <thead><tr><th class="w-[16%]">Waktu</th><th class="w-[17%]">Aktor</th><th class="w-[18%]">Aktivitas</th><th class="w-[11%]">Status</th><th>Keterangan</th><th class="w-14 text-center"><span class="sr-only">Detail</span></th></tr></thead>
        <tbody>
          {#each data.logs.items as item}
            <tr>
              <td class="whitespace-normal text-xs leading-5 text-[#53645b]">{formatDate(item.created_at)}</td>
              <td class="whitespace-normal"><strong class="block truncate text-xs" title={actorName(item)}>{actorName(item)}</strong></td>
              <td class="whitespace-normal text-xs font-bold leading-5 text-[#263a30]">{actionLabel(item.action)}</td>
              <td><span class:!bg-[#f9e9ec]={item.status !== 'success'} class:!text-[#8b2635]={item.status !== 'success'} class="badge">{statusLabel(item.status)}</span></td>
              <td class="whitespace-normal text-xs leading-5 text-[#53645b]">{actionDescription(item.action)}</td>
              <td class="text-center"><button class="grid size-9 min-h-0 place-items-center rounded-lg bg-transparent p-0 text-[#426353] hover:bg-[#edf5f1] hover:text-[#176b49]" type="button" aria-label={`Lihat detail ${actionLabel(item.action)}`} title="Lihat detail" onclick={() => openDetail(item)}><Eye size={17} strokeWidth={1.8} aria-hidden="true" /></button></td>
            </tr>
          {/each}
        </tbody>
      </table>
    {:else}<div class="empty">Belum ada audit event.</div>{/if}
    <TablePagination count={data.logs.total} page={data.logs.page} perPage={data.logs.page_size} onChange={updatePage} />
  </section>
</AdminShell>

<dialog bind:this={detailDialog} class="m-auto w-[min(92vw,42rem)] rounded-xl border border-[#dbe4df] bg-white p-0 text-[#17241f] shadow-[0_24px_70px_rgba(23,36,31,.22)] backdrop:bg-[#17241f]/35" aria-labelledby="audit-detail-title" onclick={closeFromBackdrop}>
  {#if selectedLog}
    <div class="flex items-start justify-between gap-4 border-b border-[#e5ebe8] px-5 py-4"><div><p class="mb-1 text-[.67rem] font-bold uppercase tracking-[.1em] text-[#6f7e76]">Detail audit</p><h2 id="audit-detail-title" class="m-0 text-lg font-bold">{actionLabel(selectedLog.action)}</h2></div><button class="grid size-9 min-h-0 place-items-center rounded-lg bg-transparent p-0 text-[#64736c] hover:bg-[#edf2ef] hover:text-[#263a30]" type="button" aria-label="Tutup detail" onclick={closeDetail}><X size={18} aria-hidden="true" /></button></div>
    <div class="grid gap-5 px-5 py-5">
      <p class="m-0 rounded-lg bg-[#f3f7f5] px-3.5 py-3 text-sm leading-6 text-[#40554a]">{actionDescription(selectedLog.action)}</p>
      <dl class="m-0 grid gap-x-5 gap-y-4 text-sm sm:grid-cols-2">
        <div><dt class="text-xs font-bold text-[#718078]">Waktu</dt><dd class="m-0 mt-1 break-words">{formatDate(selectedLog.created_at)}</dd></div>
        <div><dt class="text-xs font-bold text-[#718078]">Aktor</dt><dd class="m-0 mt-1 break-words">{actorName(selectedLog)}</dd></div>
        <div><dt class="text-xs font-bold text-[#718078]">ID aktor</dt><dd class="m-0 mt-1 break-all font-mono text-xs">{selectedLog.actor_user_id || 'Sistem'}</dd></div>
        <div><dt class="text-xs font-bold text-[#718078]">Status</dt><dd class="m-0 mt-1">{statusLabel(selectedLog.status)}</dd></div>
        <div><dt class="text-xs font-bold text-[#718078]">Resource</dt><dd class="m-0 mt-1 break-words">{selectedLog.resource_type || 'Tidak tersedia'}</dd></div>
        <div><dt class="text-xs font-bold text-[#718078]">ID resource</dt><dd class="m-0 mt-1 break-all font-mono text-xs">{selectedLog.resource_id || 'Tidak tersedia'}</dd></div>
        <div><dt class="text-xs font-bold text-[#718078]">Request ID</dt><dd class="m-0 mt-1 break-all font-mono text-xs">{selectedLog.request_id || 'Tidak tersedia'}</dd></div>
        <div><dt class="text-xs font-bold text-[#718078]">Field berubah</dt><dd class="m-0 mt-1 break-words">{formatFields(selectedLog.changed_fields)}</dd></div>
        {#if selectedLog.reason}<div class="sm:col-span-2"><dt class="text-xs font-bold text-[#718078]">Catatan operasi</dt><dd class="m-0 mt-1 break-words">{selectedLog.reason}</dd></div>{/if}
      </dl>
    </div>
  {/if}
</dialog>
