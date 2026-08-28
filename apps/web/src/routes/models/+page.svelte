<script lang="ts">
  import { enhance } from '$app/forms';
  import { goto } from '$app/navigation';
  import type { SubmitFunction } from '@sveltejs/kit';
  import { tick } from 'svelte';
  import { CirclePower, Eye, Plus, RotateCcw, Search, X } from 'lucide-svelte';
  import AdminFilterSelect from '$lib/components/AdminFilterSelect.svelte';
  import AdminShell from '$lib/components/AdminShell.svelte';
  import DateRangeFilter from '$lib/components/DateRangeFilter.svelte';
  import TablePagination from '$lib/components/TablePagination.svelte';

  export let data: {
    user: App.Locals['user'];
    models: any;
    filters: { search: string; status: string; date_from: string; date_to: string };
    error: string | null;
  };
  export let form: { success?: boolean; error?: string; registerError?: string } | null;

  let registerDialog: HTMLDialogElement;
  let detailDialog: HTMLDialogElement;
  let mutationDialog: HTMLDialogElement;
  let isRegistering = false;
  let pendingMutation: string | null = null;
  let selectedModel: any = null;
  let mutationModel: any = null;
  let modelClasses: string[] = [];
  let search = data.filters.search;
  let searchTimer: ReturnType<typeof setTimeout>;

  $: modelClasses = data.models.expected_classes ?? ['FMD', 'healthy', 'LSD', 'non_cattle'];

  const statusItems = [
    { value: '__all__', label: 'Semua status' },
    { value: 'active', label: 'Aktif' },
    { value: 'available', label: 'Tersedia' },
    { value: 'retired', label: 'Pensiun' },
    { value: 'failed', label: 'Gagal' }
  ];
  const statusLabel = (status: string) => ({ active: 'Aktif', retired: 'Pensiun', failed: 'Gagal', available: 'Tersedia' }[status] ?? status);
  const formatDate = (value: string | null) => value ? new Intl.DateTimeFormat('id-ID', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value)) : 'Tidak tersedia';
  const mutationLabel = () => mutationModel?.status === 'retired' ? 'Rollback' : 'Aktifkan';

  function isCompatible(item: any): boolean {
    if (item.compatible !== undefined) return Boolean(item.compatible);
    const expected = JSON.stringify(modelClasses);
    return JSON.stringify(item.classes ?? []) === expected;
  }

  function toast(message: string, tone: 'success' | 'error') {
    window.dispatchEvent(new CustomEvent('sapikenal:toast', { detail: { message, tone } }));
  }
  function updateQuery(key: string, value: string) {
    const query = new URLSearchParams(window.location.search);
    value ? query.set(key, value) : query.delete(key);
    query.delete('page');
    goto(`?${query}`, { keepFocus: true, noScroll: true, invalidateAll: true });
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
  async function openRegisterDialog() {
    registerDialog.showModal();
    await tick();
    registerDialog.querySelector<HTMLInputElement>('input[name="version"]')?.focus();
  }
  async function openDetail(item: any) {
    selectedModel = item;
    await tick();
    detailDialog.showModal();
  }
  async function openMutation(item: any) {
    if (!isCompatible(item)) {
      toast('Model tidak kompatibel dengan kontrak 4 kelas aktif.', 'error');
      return;
    }
    mutationModel = item;
    await tick();
    mutationDialog.showModal();
    mutationDialog.querySelector<HTMLInputElement>('input[name="reason"]')?.focus();
  }
  const enhanceRegister: SubmitFunction = () => {
    isRegistering = true;
    return async ({ result, update }) => {
      await update();
      isRegistering = false;
      toast(result.type === 'success' ? 'Artefak model berhasil didaftarkan.' : 'Pendaftaran artefak model gagal.', result.type === 'success' ? 'success' : 'error');
    };
  };
  const enhanceMutation: SubmitFunction = () => {
    pendingMutation = mutationModel.id;
    return async ({ result, update }) => {
      await update();
      pendingMutation = null;
      if (result.type === 'success') mutationDialog.close();
      toast(result.type === 'success' ? 'Status model berhasil diperbarui.' : 'Perubahan status model gagal.', result.type === 'success' ? 'success' : 'error');
    };
  };
  $: if (form?.registerError && registerDialog && !registerDialog.open) registerDialog.showModal();
  $: if (form?.success && registerDialog?.open) registerDialog.close();
</script>

<svelte:head><title>Model AI — SapiKenal Admin</title></svelte:head>
<AdminShell title="Model AI" eyebrow="Registri dan aktivasi" active="/models" user={data.user}>
  <section class="page-intro"><p class="muted">Unggah kandidat model ke registry backend, lalu aktifkan terpisah setelah validasi artefak selesai. Model mobile offline tidak berubah.</p></section>
  {#if data.error}<p class="error">{data.error}</p>{/if}
  {#if form?.error}<p class="error">{form.error}</p>{/if}

  <div class="mt-5 flex flex-wrap items-end justify-between gap-3">
    <div><h2 class="m-0 text-lg font-bold text-[#263a30]">Versi model backend</h2><p class="mt-1 text-sm text-[#66766f]">Model aktif: <strong class="text-[#263a30]">{data.models.active_version || 'Tidak tersedia'}</strong> · Kontrak kanonis: <code class="rounded bg-[#f0f4f1] px-1.5 py-0.5 text-xs text-[#264d3b]">[{modelClasses.join(', ')}]</code></p></div>
    <button class="flex items-center gap-2 whitespace-nowrap" type="button" onclick={openRegisterDialog}><Plus size={17} strokeWidth={2} aria-hidden="true" />Daftarkan artefak</button>
  </div>

  <div class="mt-4 grid gap-3 lg:grid-cols-[minmax(15rem,.9fr)_minmax(26rem,1.1fr)]">
    <label class="relative"><span>Cari model</span><Search class="pointer-events-none absolute bottom-3 left-3 text-[#718078]" size={16} aria-hidden="true" /><input class="w-full pl-9" type="search" value={search} placeholder="Versi, artefak, atau catatan" oninput={(event) => debounceSearch(event.currentTarget.value)} /></label>
    <div class="grid gap-3 sm:grid-cols-2"><DateRangeFilter start={data.filters.date_from} end={data.filters.date_to} onChange={updateDateRange} /><AdminFilterSelect label="Status" value={data.filters.status} items={statusItems} placeholder="Semua status" onChange={(value) => updateQuery('status', value)} /></div>
  </div>

  <section class="panel mt-3 p-0">
    {#if data.models.items.length}
      <table class="table-fixed">
        <thead><tr><th class="w-[27%]">Versi model</th><th class="w-[17%]">Status</th><th class="w-[19%]">Input & kelas</th><th class="w-[22%]">Didaftarkan</th><th class="w-28 text-center"><span class="sr-only">Aksi</span></th></tr></thead>
        <tbody>
          {#each data.models.items as item}
            <tr>
              <td class="whitespace-normal">
                <strong class="block break-words text-sm text-[#263a30]">{item.version}</strong>
                <code class="mt-1 block truncate text-[.68rem] text-[#829088]" title={item.artifact_name}>{item.artifact_name}</code>
              </td>
              <td>
                <div class="grid gap-1">
                  <span class:!bg-[#eef1ef]={item.status === 'retired'} class:!text-[#64736c]={item.status === 'retired'} class:!bg-[#fbf0f2]={item.status === 'failed'} class:!text-[#8b2635]={item.status === 'failed'} class="badge">{statusLabel(item.status)}</span>
                  {#if !isCompatible(item)}
                    <span class="badge !bg-[#fff1f2] !text-[#9f1239]" title="Model tidak sesuai dengan kontrak 4 kelas aktif">Kontrak lama</span>
                  {/if}
                </div>
              </td>
              <td class="whitespace-normal text-xs leading-5 text-[#53645b]">
                <strong class="text-[#263a30]">{item.input_size} × {item.input_size}</strong>
                <span class="block truncate text-[.68rem]" title={item.classes?.join(', ')}>{item.classes?.join(', ') || 'Tidak tersedia'}</span>
              </td>
              <td class="whitespace-normal text-xs leading-5 text-[#53645b]">
                {formatDate(item.registered_at)}
                {#if item.activated_at}<small class="mt-1 block text-[.68rem] text-[#829088]">Aktif: {formatDate(item.activated_at)}</small>{/if}
                {#if item.deactivated_at}<small class="mt-1 block text-[.68rem] text-[#829088]">Nonaktif: {formatDate(item.deactivated_at)}</small>{/if}
                {#if item.rolled_back_at}<small class="mt-1 block text-[.68rem] text-[#829088]">Rollback: {formatDate(item.rolled_back_at)}</small>{/if}
              </td>
              <td class="text-center">
                <div class="flex justify-center gap-1">
                  <button class="grid size-9 min-h-0 place-items-center rounded-lg bg-transparent p-0 text-[#426353] hover:bg-[#edf5f1] hover:text-[#176b49]" type="button" aria-label={`Lihat detail model ${item.version}`} title="Lihat detail" onclick={() => openDetail(item)}><Eye size={17} strokeWidth={1.8} aria-hidden="true" /></button>
                  {#if item.status !== 'active' && item.status !== 'failed'}
                    <button
                      class:secondary={item.status === 'retired'}
                      class="grid size-9 min-h-0 place-items-center rounded-lg p-0"
                      type="button"
                      aria-label={`${item.status === 'retired' ? 'Rollback' : 'Aktifkan'} model ${item.version}`}
                      title={!isCompatible(item) ? 'Tidak kompatibel dengan kontrak 4 kelas aktif' : (item.status === 'retired' ? 'Rollback' : 'Aktifkan')}
                      disabled={!isCompatible(item)}
                      onclick={() => openMutation(item)}
                    >
                      {#if item.status === 'retired'}
                        <RotateCcw size={16} strokeWidth={1.9} aria-hidden="true" />
                      {:else}
                        <CirclePower size={17} strokeWidth={1.9} aria-hidden="true" />
                      {/if}
                    </button>
                  {/if}
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    {:else}<div class="empty">Tidak ada model yang sesuai dengan pencarian atau filter.</div>{/if}
    <TablePagination count={data.models.total} page={data.models.page} perPage={data.models.page_size} onChange={updatePage} />
  </section>
</AdminShell>

<dialog bind:this={registerDialog} class="m-auto max-h-[calc(100dvh-2rem)] w-[min(92vw,44rem)] overflow-x-hidden overflow-y-auto rounded-xl border border-[#dbe4df] bg-white p-0 text-[#17241f] shadow-[0_24px_70px_rgba(23,36,31,.22)] backdrop:bg-[#17241f]/35" aria-labelledby="register-model-title">
  <div class="flex min-w-0 items-start justify-between gap-4 border-b border-[#e5ebe8] px-5 py-4"><div class="min-w-0"><p class="mb-1 text-[.67rem] font-bold uppercase tracking-[.1em] text-[#6f7e76]">Registry backend</p><h2 id="register-model-title" class="m-0 text-lg font-bold">Daftarkan artefak model</h2></div><button class="grid size-9 min-h-0 shrink-0 place-items-center rounded-lg bg-transparent p-0 text-[#64736c] hover:bg-[#edf2ef] hover:text-[#263a30]" type="button" aria-label="Tutup form registrasi" onclick={() => registerDialog.close()} disabled={isRegistering}><X size={18} aria-hidden="true" /></button></div>
  <form class="min-w-0" method="POST" action="?/register" enctype="multipart/form-data" use:enhance={enhanceRegister}>
    <div class="grid min-w-0 gap-4 px-5 py-5 sm:grid-cols-2">
      {#if form?.registerError}<p class="error m-0 min-w-0 break-words sm:col-span-2" role="alert">{form.registerError}</p>{/if}
      <label class="min-w-0">Versi<input class="min-w-0 w-full" name="version" autocomplete="off" maxlength="128" required disabled={isRegistering} /></label>
      <label class="min-w-0">File model (.keras)<input class="min-w-0 w-full max-w-full text-xs" name="artifact" type="file" accept=".keras,application/octet-stream" required disabled={isRegistering} /></label>
      <label class="min-w-0 sm:col-span-2">Urutan kelas backend<input class="min-w-0 w-full font-mono text-xs" name="classes" value={modelClasses.join(',')} readonly aria-describedby="model-class-help" /></label>
      <p id="model-class-help" class="m-0 text-xs font-normal leading-5 text-[#66766f] sm:col-span-2">Urutan kelas wajib mengikuti kontrak 4 kelas: <code>FMD,healthy,LSD,non_cattle</code>.</p>
      <label class="min-w-0">Ukuran input<input class="min-w-0 w-full" name="input_size" type="number" min="1" max="4096" value="224" required disabled={isRegistering} /></label>
      <label class="min-w-0 sm:col-span-2">Catatan<textarea class="min-w-0 w-full" name="notes" maxlength="10000" disabled={isRegistering}></textarea></label>
    </div>
    {#if isRegistering}<p class="mx-5 mb-4 rounded-lg bg-[#f3f8f5] px-3.5 py-3 text-sm text-[#215c42]" role="status">Mengunggah dan memvalidasi model… Jangan tutup halaman.</p>{/if}
    <div class="flex flex-wrap justify-end gap-2 border-t border-[#e5ebe8] px-5 py-4"><button class="secondary" type="button" onclick={() => registerDialog.close()} disabled={isRegistering}>Batal</button><button type="submit" disabled={isRegistering}>{isRegistering ? 'Memvalidasi…' : 'Unggah dan daftarkan'}</button></div>
  </form>
</dialog>

<dialog bind:this={detailDialog} class="m-auto max-h-[calc(100dvh-2rem)] w-[min(92vw,42rem)] overflow-y-auto rounded-xl border border-[#dbe4df] bg-white p-0 text-[#17241f] shadow-[0_24px_70px_rgba(23,36,31,.22)] backdrop:bg-[#17241f]/35" aria-labelledby="model-detail-title">
  {#if selectedModel}
    <div class="flex items-start justify-between gap-4 border-b border-[#e5ebe8] px-5 py-4">
      <div class="min-w-0">
        <p class="mb-1 text-[.67rem] font-bold uppercase tracking-[.1em] text-[#6f7e76]">Detail model</p>
        <h2 id="model-detail-title" class="m-0 break-words text-lg font-bold">{selectedModel.version}</h2>
      </div>
      <button class="grid size-9 min-h-0 shrink-0 place-items-center rounded-lg bg-transparent p-0 text-[#64736c] hover:bg-[#edf2ef]" type="button" aria-label="Tutup detail" onclick={() => detailDialog.close()}><X size={18} aria-hidden="true" /></button>
    </div>
    <dl class="m-0 grid gap-x-5 gap-y-4 px-5 py-5 text-sm sm:grid-cols-2">
      <div><dt class="text-xs font-bold text-[#718078]">Status</dt><dd class="m-0 mt-1"><span class="badge">{statusLabel(selectedModel.status)}</span></dd></div>
      <div><dt class="text-xs font-bold text-[#718078]">Kompatibilitas Kontrak</dt><dd class="m-0 mt-1"><span class={isCompatible(selectedModel) ? 'badge' : 'badge !bg-[#fff1f2] !text-[#9f1239]'}>{isCompatible(selectedModel) ? 'Kompatibel (4 kelas)' : 'Tidak kompatibel (kontrak lama)'}</span></dd></div>
      <div><dt class="text-xs font-bold text-[#718078]">Ukuran input</dt><dd class="m-0 mt-1">{selectedModel.input_size} × {selectedModel.input_size}</dd></div>
      <div><dt class="text-xs font-bold text-[#718078]">Kelas</dt><dd class="m-0 mt-1 font-mono text-xs">{selectedModel.classes?.join(', ') || 'Tidak tersedia'}</dd></div>
      <div class="sm:col-span-2"><dt class="text-xs font-bold text-[#718078]">Artefak</dt><dd class="m-0 mt-1 break-all font-mono text-xs">{selectedModel.artifact_name}</dd></div>
      <div class="sm:col-span-2"><dt class="text-xs font-bold text-[#718078]">SHA-256</dt><dd class="m-0 mt-1 break-all font-mono text-xs">{selectedModel.checksum}</dd></div>
      <div><dt class="text-xs font-bold text-[#718078]">Didaftarkan</dt><dd class="m-0 mt-1">{formatDate(selectedModel.registered_at)}</dd></div>
      <div><dt class="text-xs font-bold text-[#718078]">Diaktifkan</dt><dd class="m-0 mt-1">{formatDate(selectedModel.activated_at)}</dd></div>
      <div><dt class="text-xs font-bold text-[#718078]">Dinonaktifkan</dt><dd class="m-0 mt-1">{formatDate(selectedModel.deactivated_at)}</dd></div>
      <div><dt class="text-xs font-bold text-[#718078]">Rollback terakhir</dt><dd class="m-0 mt-1">{formatDate(selectedModel.rolled_back_at)}</dd></div>
      <div class="sm:col-span-2"><dt class="text-xs font-bold text-[#718078]">Catatan</dt><dd class="m-0 mt-1 whitespace-pre-wrap break-words">{selectedModel.notes || 'Tidak ada catatan.'}</dd></div>
    </dl>
  {/if}
</dialog>

<dialog bind:this={mutationDialog} class="m-auto w-[min(92vw,30rem)] rounded-xl border border-[#dbe4df] bg-white p-0 text-[#17241f] shadow-[0_24px_70px_rgba(23,36,31,.22)] backdrop:bg-[#17241f]/35" aria-labelledby="model-mutation-title">
  {#if mutationModel}
    <div class="flex items-start justify-between gap-4 border-b border-[#e5ebe8] px-5 py-4">
      <div class="min-w-0"><h2 id="model-mutation-title" class="m-0 text-lg font-bold">{mutationLabel()} model?</h2><p class="mb-0 mt-1 break-words text-sm text-[#66766f]">{mutationModel.version}</p></div>
      <button class="grid size-9 min-h-0 shrink-0 place-items-center rounded-lg bg-transparent p-0 text-[#64736c] hover:bg-[#edf2ef]" type="button" aria-label="Tutup dialog" onclick={() => mutationDialog.close()} disabled={pendingMutation !== null}><X size={18} aria-hidden="true" /></button>
    </div>
    <form class="grid gap-4 px-5 py-5" method="POST" action={mutationModel.status === 'retired' ? '?/rollback' : '?/activate'} use:enhance={enhanceMutation}>
      <input type="hidden" name="id" value={mutationModel.id} />
      <label>Alasan {mutationLabel().toLowerCase()}<input name="reason" required disabled={pendingMutation !== null} /></label>
      <div class="flex justify-end gap-2">
        <button class="secondary" type="button" onclick={() => mutationDialog.close()} disabled={pendingMutation !== null}>Batal</button>
        <button class:secondary={mutationModel.status === 'retired'} type="submit" disabled={pendingMutation !== null}>{pendingMutation ? 'Memproses…' : mutationLabel()}</button>
      </div>
    </form>
  {/if}
</dialog>
