<script lang="ts">
  import { tick } from 'svelte';
  import { goto } from '$app/navigation';
  import { Eye, Search, X } from 'lucide-svelte';
  import AdminFilterSelect from '$lib/components/AdminFilterSelect.svelte';
  import AdminShell from '$lib/components/AdminShell.svelte';
  import DateRangeFilter from '$lib/components/DateRangeFilter.svelte';
  import TablePagination from '$lib/components/TablePagination.svelte';

  export let data: {
    user: App.Locals['user'];
    predictions: any;
    filters: {
      search: string;
      predicted_class: string;
      outcome: string;
      inference_mode: string;
      reliable: string;
      date_from: string;
      date_to: string;
    };
    error: string | null;
  };

  let selectedPrediction: any = null;
  let detailDialog: HTMLDialogElement;
  let search = data.filters.search;
  let searchTimer: ReturnType<typeof setTimeout>;

  const formatDate = (value: number) => new Intl.DateTimeFormat('id-ID', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value));
  const formatConfidence = (value: number) => `${(value * 100).toFixed(1)}%`;
  const reliabilityLabel = (value: boolean) => value ? 'Reliable' : 'Confidence rendah';
  const modeLabel = (value: string) => {
    const normalized = value?.toLowerCase();
    return normalized === 'online' ? 'Online' : normalized === 'offline' || normalized === 'offline_fallback' ? 'Offline' : value;
  };

  const classDisplayMap: Record<string, string> = {
    healthy: 'Sehat',
    FMD: 'PMK',
    LSD: 'Lato-Lato',
    non_cattle: 'Objek bukan sapi'
  };

  const outcomeFilterItems = [
    { value: '__all__', label: 'Semua status' },
    { value: 'accepted', label: 'Diterima' },
    { value: 'rejected', label: 'Ditolak' },
    { value: 'failed', label: 'Gagal' }
  ];
  const classFilterItems = [
    { value: '__all__', label: 'Semua kelas' },
    { value: 'healthy', label: 'Sehat' },
    { value: 'FMD', label: 'PMK' },
    { value: 'LSD', label: 'Lato-Lato' },
    { value: 'non_cattle', label: 'Objek bukan sapi' }
  ];
  const modeFilterItems = [
    { value: '__all__', label: 'Semua mode' },
    { value: 'online', label: 'Online' },
    { value: 'offline', label: 'Offline' }
  ];
  const reliabilityFilterItems = [
    { value: '__all__', label: 'Semua reliability' },
    { value: 'true', label: 'Reliable' },
    { value: 'false', label: 'Confidence rendah' }
  ];

  function isItemRejected(item: any): boolean {
    return item?.outcome === 'rejected' || item?.predicted_class === 'non_cattle';
  }

  function isItemFailed(item: any): boolean {
    return item?.outcome === 'failed';
  }

  async function openDetail(item: any) {
    selectedPrediction = item;
    await tick();
    detailDialog.showModal();
  }

  function closeDetail() {
    detailDialog.close();
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

<svelte:head><title>Prediksi — SapiKenal Admin</title></svelte:head>
<AdminShell title="Prediksi" eyebrow="Metadata klasifikasi" active="/predictions" user={data.user}>
  <section class="page-intro"><p class="muted">Riwayat menampilkan metadata operasional utama. Citra, koordinat, dan device ID mentah tidak disimpan atau ditampilkan.</p></section>
  {#if data.error}<p class="error">{data.error}</p>{/if}
  <div class="mt-4 grid gap-3 lg:grid-cols-[minmax(14rem,.75fr)_minmax(33rem,1.25fr)]">
    <div>
      <label class="relative"><span>Cari prediksi</span><Search class="pointer-events-none absolute bottom-3 left-3 text-[#718078]" size={16} aria-hidden="true" /><input class="w-full pl-9" type="search" value={search} placeholder="Hasil, model, mode, atau user ID" oninput={(event) => debounceSearch(event.currentTarget.value)} /></label>
    </div>
    <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
      <DateRangeFilter start={data.filters.date_from} end={data.filters.date_to} onChange={updateDateRange} />
      <AdminFilterSelect label="Status" value={data.filters.outcome} items={outcomeFilterItems} placeholder="Semua status" onChange={(value) => updateQuery('outcome', value)} />
      <AdminFilterSelect label="Kelas" value={data.filters.predicted_class} items={classFilterItems} placeholder="Semua kelas" onChange={(value) => updateQuery('predicted_class', value)} />
      <AdminFilterSelect label="Mode" value={data.filters.inference_mode} items={modeFilterItems} placeholder="Semua mode" onChange={(value) => updateQuery('inference_mode', value)} />
      <AdminFilterSelect label="Reliability" value={data.filters.reliable} items={reliabilityFilterItems} placeholder="Semua reliability" onChange={(value) => updateQuery('reliable', value)} />
    </div>
  </div>
  <section class="panel mt-3 p-0">
    {#if data.predictions.items.length}
      <table class="table-fixed">
        <thead><tr><th class="w-[17%]">Waktu</th><th class="w-[28%]">Hasil prediksi</th><th class="w-[18%]">Perangkat</th><th class="w-[13%]">Mode</th><th>Durasi proses</th><th class="w-14 text-center"><span class="sr-only">Detail</span></th></tr></thead>
        <tbody>
          {#each data.predictions.items as item}
            <tr>
              <td class="whitespace-normal text-xs leading-5 text-[#53645b]">{formatDate(item.timestamp)}</td>
              <td class="whitespace-normal">
                {#if isItemRejected(item)}
                  <div class="grid gap-1">
                    <div class="flex flex-wrap items-center gap-2">
                      <span class="badge !bg-[#edf1ef] !text-[#52645c]">Ditolak</span>
                      <strong class="text-sm text-[#263a30]">Objek bukan sapi</strong>
                    </div>
                    <span class="text-[.68rem] font-semibold text-[#667870]">Confidence penolakan: {formatConfidence(item.confidence)}</span>
                  </div>
                {:else if isItemFailed(item)}
                  <div class="grid gap-1">
                    <div class="flex flex-wrap items-center gap-2">
                      <span class="badge !bg-[#fff3dc] !text-[#8b5a16]">Gagal</span>
                      <strong class="text-sm text-[#263a30]">Gagal teknis</strong>
                    </div>
                    <span class="text-[.68rem] font-semibold text-[#8b5a16]">Kejadian operasional</span>
                  </div>
                {:else}
                  <div class="grid gap-1">
                    <div class="flex flex-wrap items-center gap-2">
                      <span class="badge">{item.display_label}</span>
                      <strong class="text-sm text-[#263a30]">{formatConfidence(item.confidence)}</strong>
                    </div>
                    <span class:!text-[#8b5a16]={!item.is_reliable} class="text-[.68rem] font-semibold text-[#4d7561]">{reliabilityLabel(item.is_reliable)}</span>
                  </div>
                {/if}
              </td>
              <td><code class="rounded-md bg-[#f1f5f3] px-2 py-1 text-[.72rem] text-[#40554a]">{item.device_ref}</code></td>
              <td class="text-xs font-semibold text-[#40554a]">{modeLabel(item.inference_mode)}</td>
              <td class="text-xs text-[#53645b]">{item.processing_ms == null ? 'Tidak tersedia' : `${item.processing_ms} ms`}</td>
              <td class="text-center"><button class="grid size-9 min-h-0 place-items-center rounded-lg bg-transparent p-0 text-[#426353] hover:bg-[#edf5f1] hover:text-[#176b49]" type="button" aria-label={`Lihat detail prediksi ${item.display_label}`} title="Lihat detail" onclick={() => openDetail(item)}><Eye size={17} strokeWidth={1.8} aria-hidden="true" /></button></td>
            </tr>
          {/each}
        </tbody>
      </table>
    {:else}<div class="empty">Belum ada metadata prediksi pada periode ini.</div>{/if}
    <TablePagination count={data.predictions.total} page={data.predictions.page} perPage={data.predictions.page_size} onChange={updatePage} />
  </section>
</AdminShell>

<dialog bind:this={detailDialog} class="m-auto max-h-[calc(100dvh-2rem)] w-[min(92vw,42rem)] overflow-y-auto rounded-xl border border-[#dbe4df] bg-white p-0 text-[#17241f] shadow-[0_24px_70px_rgba(23,36,31,.22)] backdrop:bg-[#17241f]/35" aria-labelledby="prediction-detail-title" onclick={closeFromBackdrop}>
  {#if selectedPrediction}
    <div class="flex items-start justify-between gap-4 border-b border-[#e5ebe8] px-5 py-4">
      <div>
        <p class="mb-1 text-[.67rem] font-bold uppercase tracking-[.1em] text-[#6f7e76]">Detail prediksi</p>
        <h2 id="prediction-detail-title" class="m-0 text-lg font-bold">
          {isItemRejected(selectedPrediction) ? 'Objek bukan sapi' : isItemFailed(selectedPrediction) ? 'Gagal teknis' : selectedPrediction.display_label} · {formatConfidence(selectedPrediction.confidence)}
        </h2>
      </div>
      <button class="grid size-9 min-h-0 place-items-center rounded-lg bg-transparent p-0 text-[#64736c] hover:bg-[#edf2ef] hover:text-[#263a30]" type="button" aria-label="Tutup detail" onclick={closeDetail}><X size={18} aria-hidden="true" /></button>
    </div>
    <div class="grid gap-5 px-5 py-5">
      {#if isItemRejected(selectedPrediction)}
        <div class="rounded-lg border border-[#dde4e0] bg-[#f5f8f6] px-3.5 py-3 text-xs leading-relaxed text-[#40544a]">
          <div class="flex flex-wrap items-center gap-2">
            <span class="badge !bg-[#edf1ef] !text-[#52645c]">Ditolak</span>
            <strong>Confidence penolakan: {formatConfidence(selectedPrediction.confidence)}</strong>
          </div>
          <p class="mb-0 mt-1.5 text-[#5e7067]">Citra tidak menampilkan sapi (guardrail validasi input, bukan kondisi klinis).</p>
        </div>
      {:else if isItemFailed(selectedPrediction)}
        <div class="flex flex-wrap items-center gap-2 rounded-lg bg-[#fff8e8] px-3.5 py-3">
          <span class="badge !bg-[#fff3dc] !text-[#8b5a16]">Gagal</span>
          <strong>Gagal teknis</strong>
          <span class="text-xs text-[#8b5a16]">Kejadian operasional</span>
        </div>
      {:else}
        <div class="flex flex-wrap items-center gap-2 rounded-lg bg-[#f3f7f5] px-3.5 py-3">
          <span class="badge">{selectedPrediction.display_label}</span>
          <strong>{formatConfidence(selectedPrediction.confidence)}</strong>
          <span class:!bg-[#fff3dc]={!selectedPrediction.is_reliable} class:!text-[#8b5a16]={!selectedPrediction.is_reliable} class="badge">{reliabilityLabel(selectedPrediction.is_reliable)}</span>
        </div>
      {/if}

      {#if selectedPrediction.scores}
        <div class="rounded-lg border border-[#e4ebe7] bg-white p-3.5">
          <h3 class="m-0 mb-2 text-xs font-bold text-[#55675f]">Skor Probabilitas Model (4 Kelas)</h3>
          <div class="grid grid-cols-2 gap-2 text-xs sm:grid-cols-4">
            <div class="rounded-md bg-[#f8faf9] p-2">
              <span class="block text-[.68rem] text-[#6b7c73]">PMK (FMD)</span>
              <strong class="text-[.82rem] text-[#24372e]">{formatConfidence(selectedPrediction.scores.FMD ?? 0)}</strong>
            </div>
            <div class="rounded-md bg-[#f8faf9] p-2">
              <span class="block text-[.68rem] text-[#6b7c73]">Sehat</span>
              <strong class="text-[.82rem] text-[#24372e]">{formatConfidence(selectedPrediction.scores.healthy ?? 0)}</strong>
            </div>
            <div class="rounded-md bg-[#f8faf9] p-2">
              <span class="block text-[.68rem] text-[#6b7c73]">Lato-Lato (LSD)</span>
              <strong class="text-[.82rem] text-[#24372e]">{formatConfidence(selectedPrediction.scores.LSD ?? 0)}</strong>
            </div>
            <div class="rounded-md bg-[#f8faf9] p-2">
              <span class="block text-[.68rem] text-[#6b7c73]">Objek bukan sapi</span>
              <strong class="text-[.82rem] text-[#24372e]">{formatConfidence(selectedPrediction.scores.non_cattle ?? 0)}</strong>
            </div>
          </div>
        </div>
      {/if}

      <dl class="m-0 grid gap-x-5 gap-y-4 text-sm sm:grid-cols-2">
        <div><dt class="text-xs font-bold text-[#718078]">Waktu</dt><dd class="m-0 mt-1 break-words">{formatDate(selectedPrediction.timestamp)}</dd></div>
        <div><dt class="text-xs font-bold text-[#718078]">ID prediksi</dt><dd class="m-0 mt-1 break-all font-mono text-xs">{selectedPrediction.id}</dd></div>
        <div><dt class="text-xs font-bold text-[#718078]">Referensi perangkat</dt><dd class="m-0 mt-1 font-mono text-xs">{selectedPrediction.device_ref}</dd></div>
        <div><dt class="text-xs font-bold text-[#718078]">ID pengguna</dt><dd class="m-0 mt-1 break-all font-mono text-xs">{selectedPrediction.user_id || 'Tidak tersedia'}</dd></div>
        <div><dt class="text-xs font-bold text-[#718078]">Kelas model</dt><dd class="m-0 mt-1">{classDisplayMap[selectedPrediction.predicted_class] ?? selectedPrediction.predicted_class}</dd></div>
        <div><dt class="text-xs font-bold text-[#718078]">Mode inferensi</dt><dd class="m-0 mt-1">{modeLabel(selectedPrediction.inference_mode)}</dd></div>
        <div><dt class="text-xs font-bold text-[#718078]">Versi model</dt><dd class="m-0 mt-1 break-words">{selectedPrediction.model_version || 'Tidak tersedia'}</dd></div>
        <div><dt class="text-xs font-bold text-[#718078]">Versi aplikasi</dt><dd class="m-0 mt-1 break-words">{selectedPrediction.app_version || 'Tidak tersedia'}</dd></div>
        <div><dt class="text-xs font-bold text-[#718078]">Durasi proses</dt><dd class="m-0 mt-1">{selectedPrediction.processing_ms == null ? 'Tidak tersedia' : `${selectedPrediction.processing_ms} ms`}</dd></div>
        <div><dt class="text-xs font-bold text-[#718078]">Status operasional</dt><dd class="m-0 mt-1">{isItemRejected(selectedPrediction) ? 'Ditolak (Guardrail non-sapi)' : isItemFailed(selectedPrediction) ? 'Gagal teknis' : 'Diterima'}</dd></div>
        {#if selectedPrediction.rejection_reason}<div class="sm:col-span-2"><dt class="text-xs font-bold text-[#718078]">Alasan penolakan</dt><dd class="m-0 mt-1 break-words">{selectedPrediction.rejection_reason === 'non_cattle' ? 'Citra tidak menampilkan sapi (NON_CATTLE_IMAGE)' : selectedPrediction.rejection_reason}</dd></div>{/if}
        {#if selectedPrediction.error_code}<div class="sm:col-span-2"><dt class="text-xs font-bold text-[#718078]">Kode error</dt><dd class="m-0 mt-1 break-words">{selectedPrediction.error_code}</dd></div>{/if}
      </dl>
    </div>
  {/if}
</dialog>
