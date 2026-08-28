<script lang="ts">
  import { navigating } from '$app/state';
  import { Tabs } from 'bits-ui';
  import {
    Activity,
    ArrowRight,
    BrainCircuit,
    CheckCircle2,
    CircleAlert,
    Clock3,
    Gauge,
    ImageOff,
    ScanLine,
    ShieldCheck
  } from 'lucide-svelte';
  import AdminShell from '$lib/components/AdminShell.svelte';

  export let data: {
    user: App.Locals['user'];
    dashboard: any;
    period: string;
    error: string | null;
  };

  const periods = [
    { value: '24h', label: '24 jam' },
    { value: '7d', label: '7 hari' },
    { value: '30d', label: '30 hari' }
  ];

  const classLabels: Record<string, string> = {
    healthy: 'Sehat',
    FMD: 'PMK',
    LSD: 'Lato-Lato'
  };

  const auditLabels: Record<string, string> = {
    'user.created': 'Pengguna dibuat',
    'user.updated': 'Pengguna diperbarui',
    'user.password_reset': 'Password pengguna direset',
    'disease_content.created': 'Konten penyakit dibuat',
    'disease_content.updated': 'Konten penyakit diperbarui',
    'disease_content.activated': 'Konten penyakit diaktifkan',
    'disease_content.deactivated': 'Konten penyakit dinonaktifkan',
    'model.registered': 'Model didaftarkan',
    'model.activated': 'Model diaktifkan',
    'model.rollback': 'Model di-rollback'
  };

  const formatNumber = (value: number | null | undefined) => value == null ? '—' : new Intl.NumberFormat('id-ID').format(value);
  const formatPercent = (value: number | null | undefined) => value == null ? '—' : `${(value * 100).toFixed(1)}%`;
  const formatDate = (value: string | null | undefined) => value ? new Intl.DateTimeFormat('id-ID', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value)) : 'Waktu tidak tersedia';
  const distributionTotal = () => Object.values(data.dashboard?.predictions?.distribution ?? {}).reduce((sum: number, value) => sum + Number(value), 0);
  const distributionPercent = (value: unknown) => distributionTotal() ? Math.round((Number(value) / distributionTotal()) * 100) : 0;
</script>

<svelte:head><title>Dashboard — SapiKenal Admin</title></svelte:head>

<AdminShell title="Dashboard" active="/dashboard" user={data.user}>
  <section class="mt-7 flex flex-col items-stretch justify-between gap-6 sm:flex-row sm:items-end">
    <div class="grid max-w-2xl gap-1.5">
      <p class="m-0 text-[.95rem] leading-[1.45] text-[#34483e]">Ringkasan operasional sistem klasifikasi citra dan aktivitas administratif.</p>
      <span class="text-xs leading-[1.45] text-[#75837c]">Data citra dan koordinat presisi tidak ditampilkan pada web admin.</span>
    </div>
    <Tabs.Root value={data.period} onValueChange={(value) => { if (value !== data.period) window.location.href = `/dashboard?period=${value}`; }}>
      <Tabs.List class="inline-flex gap-1 rounded-[.58rem] border border-[#dce5e0] bg-[#edf2ef] p-1" aria-label="Periode dashboard">
        {#each periods as period}
          <Tabs.Trigger class="min-h-8 rounded-[.4rem] border-0 bg-transparent px-2.5 py-1.5 text-xs font-bold text-[#64736c] transition hover:bg-white/60 hover:text-[#234c39] data-[state=active]:bg-white data-[state=active]:text-[#174d35] data-[state=active]:shadow-sm active:translate-y-px" value={period.value}>{period.label}</Tabs.Trigger>
        {/each}
      </Tabs.List>
    </Tabs.Root>
  </section>

  {#if data.error}
    <div class="mt-5 flex items-start gap-3 rounded-[.65rem] border border-[#efced2] bg-[#fcf3f4] px-4 py-3.5 text-[#842f3b]" role="alert"><CircleAlert size={18} strokeWidth={1.8} aria-hidden="true" /><div class="grid gap-0.5"><strong class="text-[.82rem]">Data dashboard tidak dapat dimuat</strong><span class="text-xs">{data.error}</span></div></div>
  {/if}

  {#if navigating?.to?.url.pathname === '/dashboard'}
    <section class="mt-6 grid gap-4" aria-label="Memuat dashboard" aria-busy="true">
      <div class="skeleton h-16"></div>
      <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><div class="skeleton h-36"></div><div class="skeleton h-36"></div><div class="skeleton h-36"></div><div class="skeleton h-36"></div></div>
      <div class="grid gap-4 xl:grid-cols-2"><div class="skeleton h-80"></div><div class="skeleton h-80"></div></div>
    </section>
  {:else if data.dashboard}
    <section class={`mt-6 flex items-center justify-between gap-4 rounded-[.68rem] border px-3.5 py-3 ${data.dashboard.health.status === 'ok' ? 'border-[#d5e5dd] bg-[#f3f8f5] text-[#215c42]' : 'border-[#ecd9b6] bg-[#fcf8ee] text-[#74511a]'}`} aria-label="Status sistem">
      <div class="flex items-center gap-2.5">
        {#if data.dashboard.health.status === 'ok'}<CheckCircle2 size={18} strokeWidth={2} aria-hidden="true" />{:else}<CircleAlert size={18} strokeWidth={2} aria-hidden="true" />{/if}
        <div class="grid gap-0.5"><strong class="text-[.78rem]">{data.dashboard.health.status === 'ok' ? 'Semua sistem beroperasi normal' : 'Sistem memerlukan perhatian'}</strong><span class="text-[.72rem] text-[#63786c] max-sm:hidden">{data.dashboard.health.model_loaded ? 'Backend dan model inferensi siap digunakan.' : 'Model inferensi belum siap menerima klasifikasi.'}</span></div>
      </div>
      <span class="rounded-full border border-current px-2 py-1 text-[.66rem] font-bold">{data.dashboard.health.status === 'ok' ? 'Operasional' : 'Degraded'}</span>
    </section>

    <section class="mt-4 grid grid-cols-1 overflow-hidden rounded-xl border border-[#e0e7e3] bg-white shadow-sm sm:grid-cols-2 xl:grid-cols-4" aria-label="KPI dashboard">
      <article class="grid min-w-0 gap-2.5 border-b border-[#e7ece9] p-5 sm:border-r xl:border-b-0">
        <div class="flex items-center gap-2"><span class="grid size-7 place-items-center rounded-lg bg-[#edf5f1] text-[#357157]"><ScanLine size={18} strokeWidth={1.8} aria-hidden="true" /></span><span class="text-xs font-bold text-[#66766e]">Percobaan klasifikasi</span></div>
        <strong class="truncate text-[clamp(1.55rem,2.5vw,2rem)] font-bold leading-none tracking-[-.045em] text-[#17241f]">{formatNumber(data.dashboard.predictions.attempts ?? data.dashboard.predictions.total)}</strong>
        <div class="flex flex-wrap justify-between gap-1 text-[.68rem] text-[#7a8881]"><span>{formatNumber(data.dashboard.predictions.accepted)} diterima</span><span>{formatNumber(data.dashboard.predictions.rejected_non_cattle)} ditolak</span><span>{formatNumber(data.dashboard.predictions.failures)} gagal</span></div>
      </article>
      <article class="grid min-w-0 gap-2.5 border-b border-[#e7ece9] p-5 xl:border-b-0 xl:border-r">
        <div class="flex items-center justify-between gap-2">
          <div class="flex items-center gap-2"><span class="grid size-7 place-items-center rounded-lg bg-[#edf5f1] text-[#357157]"><ImageOff size={18} strokeWidth={1.8} aria-hidden="true" /></span><span class="text-xs font-bold text-[#66766e]">Citra non-sapi</span></div>
          <a class="text-[.68rem] font-bold text-[#286248] no-underline hover:text-[#123f2c]" href="/predictions?outcome=rejected&predicted_class=non_cattle" title="Lihat daftar penolakan">Detail →</a>
        </div>
        <strong class="truncate text-[clamp(1.55rem,2.5vw,2rem)] font-bold leading-none tracking-[-.045em] text-[#17241f]">{formatPercent(data.dashboard.predictions.non_cattle_rate)}</strong>
        <div class="flex justify-between gap-2 text-[.68rem] text-[#7a8881]"><span>{formatNumber(data.dashboard.predictions.rejected_non_cattle)} penolakan</span><span>Guardrail input</span></div>
      </article>
      <article class="grid min-w-0 gap-2.5 border-b border-[#e7ece9] p-5 sm:border-r xl:border-b-0">
        <div class="flex items-center gap-2"><span class="grid size-7 place-items-center rounded-lg bg-[#edf5f1] text-[#357157]"><Gauge size={18} strokeWidth={1.8} aria-hidden="true" /></span><span class="text-xs font-bold text-[#66766e]">Confidence rendah</span></div>
        <strong class="truncate text-[clamp(1.55rem,2.5vw,2rem)] font-bold leading-none tracking-[-.045em] text-[#17241f]">{formatPercent(data.dashboard.predictions.low_confidence_rate)}</strong>
        <div class="flex justify-between gap-2 text-[.68rem] text-[#7a8881]"><span>{formatNumber(data.dashboard.predictions.low_confidence)} hasil diterima</span><span>Di bawah ambang</span></div>
      </article>
      <article class="grid min-w-0 gap-2.5 p-5">
        <div class="flex items-center gap-2"><span class="grid size-7 place-items-center rounded-lg bg-[#edf5f1] text-[#357157]"><BrainCircuit size={18} strokeWidth={1.8} aria-hidden="true" /></span><span class="text-xs font-bold text-[#66766e]">Model aktif</span></div>
        <strong class="truncate text-[1.08rem] font-bold leading-none tracking-[-.02em] text-[#17241f]" title={data.dashboard.model.version}>{data.dashboard.model.version}</strong>
        <div class="flex justify-between gap-2 text-[.68rem] text-[#7a8881]"><span>{data.dashboard.model.status}</span><span>{data.dashboard.health.model_loaded ? 'Termuat' : 'Belum termuat'}</span></div>
      </article>
    </section>

    <div class="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,1.08fr)_minmax(0,.92fr)]">
      <section class="min-w-0 rounded-xl border border-[#e0e7e3] bg-white p-5 shadow-sm">
        <div class="flex items-start justify-between gap-4 border-b border-[#e8edea] pb-4">
          <div><h2 class="m-0 mb-1 text-[.9rem] font-bold tracking-[-.015em]">Distribusi hasil diterima</h2><p class="m-0 text-[.72rem] text-[#7a8881]">Komposisi hasil penyakit sapi pada periode terpilih ({formatNumber(data.dashboard.predictions.accepted)} diterima).</p></div>
          <a class="inline-flex items-center gap-1 whitespace-nowrap text-[.7rem] font-bold text-[#286248] no-underline hover:text-[#123f2c]" href="/predictions?outcome=accepted">Lihat diterima <ArrowRight size={14} strokeWidth={1.8} aria-hidden="true" /></a>
        </div>
        {#if distributionTotal()}
          <div class="grid gap-4 py-5">
            {#each Object.entries(data.dashboard.predictions.distribution) as [label, count]}
              <div class="grid gap-2">
                <div class="flex items-baseline justify-between gap-4 text-xs text-[#465a50]"><span>{classLabels[label] ?? label}</span><strong class="text-[.78rem] text-[#24372e]">{formatNumber(count as number)} <small class="ml-1 text-[.66rem] font-semibold text-[#829088]">{distributionPercent(count)}%</small></strong></div>
                <div class="h-1.5 overflow-hidden rounded-full bg-[#edf1ef]" role="meter" aria-label={`Proporsi ${classLabels[label] ?? label}`} aria-valuemin="0" aria-valuemax="100" aria-valuenow={distributionPercent(count)}><span class="block h-full rounded-full bg-[#398361]" style={`width: ${distributionPercent(count)}%`}></span></div>
              </div>
            {/each}
          </div>
        {:else}
          <div class="grid min-h-44 place-items-center gap-2 text-center text-xs text-[#7c8b83]"><ScanLine size={22} strokeWidth={1.5} aria-hidden="true" /><span>Belum ada hasil penyakit diterima pada periode ini.</span></div>
        {/if}

        <div class="rounded-lg border border-[#e2e8e5] bg-[#f8faf9] p-3 text-xs">
          <div class="flex items-center justify-between gap-2">
            <div class="flex items-center gap-2 text-[#32453c]">
              <ImageOff size={15} strokeWidth={1.8} class="text-[#597165]" aria-hidden="true" />
              <span class="font-bold">Kualitas Input (Citra Non-Sapi)</span>
            </div>
            <a class="text-[.68rem] font-bold text-[#286248] no-underline hover:text-[#123f2c]" href="/predictions?outcome=rejected&predicted_class=non_cattle">Buka data penolakan →</a>
          </div>
          <p class="mb-0 mt-1 text-[.72rem] leading-relaxed text-[#63756d]">
            Sebanyak <strong>{formatNumber(data.dashboard.predictions.rejected_non_cattle)}</strong> citra ditolak ({formatPercent(data.dashboard.predictions.non_cattle_rate)}) sebagai guardrail validasi input dan tidak dihitung ke distribusi klinis penyakit sapi.
          </p>
        </div>

        <div class="mt-4 grid gap-2 border-t border-[#e8edea] pt-4 sm:grid-cols-2">
          <div class="grid grid-cols-[auto_1fr_auto] items-center gap-2 text-[.69rem] text-[#708078]"><Clock3 size={15} strokeWidth={1.8} aria-hidden="true" /><span>Median proses</span><strong class="text-[.72rem] text-[#263a30]">{formatNumber(data.dashboard.predictions.median_processing_ms)} ms</strong></div>
          <div class="grid grid-cols-[auto_1fr_auto] items-center gap-2 text-[.69rem] text-[#708078]"><Activity size={15} strokeWidth={1.8} aria-hidden="true" /><span>Persentil ke-95</span><strong class="text-[.72rem] text-[#263a30]">{formatNumber(data.dashboard.predictions.p95_processing_ms)} ms</strong></div>
        </div>
      </section>

      <section class="min-w-0 rounded-xl border border-[#e0e7e3] bg-white p-5 shadow-sm">
        <div class="flex items-start justify-between gap-4 border-b border-[#e8edea] pb-4">
          <div><h2 class="m-0 mb-1 text-[.9rem] font-bold tracking-[-.015em]">Aktivitas terbaru</h2><p class="m-0 text-[.72rem] text-[#7a8881]">Perubahan administratif terkini.</p></div>
          <a class="inline-flex items-center gap-1 whitespace-nowrap text-[.7rem] font-bold text-[#286248] no-underline hover:text-[#123f2c]" href="/audit-logs">Buka audit log <ArrowRight size={14} strokeWidth={1.8} aria-hidden="true" /></a>
        </div>
        {#if data.dashboard.recent_audit_events.length}
          <ol class="m-0 grid list-none p-0">
            {#each data.dashboard.recent_audit_events as event}
              <li class="grid grid-cols-[1.75rem_minmax(0,1fr)_auto] items-center gap-2.5 border-b border-[#edf1ef] py-3 last:border-b-0">
                <span class="grid size-7 place-items-center rounded-lg border border-[#dde8e2] bg-[#f6f9f7] text-[#40745c]"><ShieldCheck size={15} strokeWidth={1.8} aria-hidden="true" /></span>
                <div class="grid min-w-0 gap-0.5"><strong class="truncate text-[.73rem]">{auditLabels[event.action] ?? event.action}</strong><span class="truncate text-[.65rem] text-[#7b8982]">{event.resource_type ?? 'Sistem'} · {formatDate(event.created_at)}</span></div>
                <span class={`rounded-full px-1.5 py-1 text-[.62rem] font-bold capitalize ${event.status === 'success' ? 'bg-[#eaf4ef] text-[#246246]' : 'bg-[#f9e9ec] text-[#8b2635]'}`}>{event.status === 'success' ? 'Berhasil' : event.status}</span>
              </li>
            {/each}
          </ol>
        {:else}
          <div class="grid min-h-44 place-items-center gap-2 text-center text-xs text-[#7c8b83]"><ShieldCheck size={22} strokeWidth={1.5} aria-hidden="true" /><span>Belum ada aktivitas administratif.</span></div>
        {/if}
      </section>
    </div>
  {:else if !data.error}
    <section class="mt-6 grid justify-items-center gap-2 rounded-xl border border-dashed border-[#d7e0db] px-4 py-16 text-center text-[#6f7e76]"><Activity size={26} strokeWidth={1.5} aria-hidden="true" /><h2 class="m-0 mt-1 text-[.95rem] font-bold text-[#30453a]">Belum ada data dashboard</h2><p class="m-0 text-xs">Data operasional akan tampil setelah backend menerima aktivitas.</p></section>
  {/if}
</AdminShell>
