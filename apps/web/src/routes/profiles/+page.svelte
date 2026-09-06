<script lang="ts">
  import { goto } from '$app/navigation';
  import { enhance } from '$app/forms';
  import AdminFilterSelect from '$lib/components/AdminFilterSelect.svelte';
  import AdminShell from '$lib/components/AdminShell.svelte';
  import TablePagination from '$lib/components/TablePagination.svelte';

  export let data: { user: App.Locals['user']; profiles: any; status: string; error: string | null };
  export let form: { success?: boolean; error?: string } | null;

  const breedItems = [
    { value: '__all__', label: 'Semua jenis' },
    { value: 'bali', label: 'Bali' },
    { value: 'brahman', label: 'Brahman' },
    { value: 'brangus', label: 'Brangus' },
    { value: 'limusin', label: 'Limusin' }
  ];
  const statuses = [
    { value: '__all__', label: 'Semua status' },
    { value: 'draft', label: 'Draft' },
    { value: 'active', label: 'Aktif' },
    { value: 'inactive', label: 'Nonaktif' }
  ];
  const statusLabel = (status: string) => ({ draft: 'Draft', active: 'Aktif', inactive: 'Nonaktif' }[status] ?? status);
  let selected: any = null;

  function filterStatus(value: string) {
    const query = new URLSearchParams(window.location.search);
    if (value) query.set('status', value);
    else query.delete('status');
    query.delete('page');
    goto(`?${query}`, { keepFocus: true, noScroll: true, invalidateAll: true });
  }

  function updatePage(page: number) {
    const query = new URLSearchParams(window.location.search);
    query.set('page', String(page));
    goto(`?${query}`, { keepFocus: true, noScroll: true, invalidateAll: true });
  }

  function reviewed(profile: any) {
    return Boolean(profile.revision.content_reviewed);
  }

</script>

<svelte:head><title>Profil Jenis — SapiKenal Admin</title></svelte:head>
<AdminShell title="Profil jenis sapi" eyebrow="Konten dan publikasi" active="/profiles" user={data.user}>
  <section class="page-intro"><p class="muted">Kelola profil empat jenis sapi untuk informasi pendukung hasil identifikasi. Profil tetap draft sampai konten memiliki sumber dan ditinjau administrator.</p></section>
  {#if data.error}<p class="error" role="alert">Data profil tidak dapat dimuat: {data.error}</p>{/if}
  {#if form?.error}<p class="error" role="alert">{form.error}</p>{/if}
  {#if form?.success}<p class="success" role="status">Perubahan profil berhasil disimpan.</p>{/if}

  <div class="mt-5 flex flex-wrap items-end justify-between gap-3">
    <div><h2 class="m-0 text-lg font-bold text-[#263a30]">Profil terdaftar</h2><p class="mt-1 text-sm text-[#66766f]">{data.profiles.total ?? 0} profil pada hasil filter.</p></div>
    <details class="panel w-full max-w-2xl p-4">
      <summary class="cursor-pointer font-semibold">Tambah profil jenis</summary>
      <form class="mt-4 grid gap-3 sm:grid-cols-2" method="POST" action="?/create" use:enhance>
        <label>Jenis<select name="canonical_key" required><option value="" disabled selected>Pilih jenis</option>{#each breedItems.slice(1) as breed}<option value={breed.value}>{breed.label}</option>{/each}</select></label>
        <label>Nama tampilan<input name="display_name" required /></label>
        <label>Locale<input name="locale" value="id-ID" pattern="(id-ID|en-US)" required /></label>
        <label class="sm:col-span-2">Ringkasan<textarea name="summary" required></textarea></label>
        <label>Kelebihan<textarea name="strengths" required></textarea></label>
        <label>Kekurangan<textarea name="limitations" required></textarea></label>
        <label class="sm:col-span-2">Disclaimer<textarea name="disclaimer" required></textarea></label>
        <label class="sm:col-span-2">Sumber (satu URL per baris)<textarea name="sources" placeholder="https://sumber-tepercaya.example/profil" required></textarea></label>
        <p class="m-0 text-xs font-normal leading-5 text-[#66766f] sm:col-span-2">Simpan sebagai draft. Tinjau isi dan sumber sebelum mengaktifkan profil.</p>
        <button class="sm:col-span-2" type="submit">Simpan sebagai draft</button>
      </form>
    </details>
  </div>

  <div class="mt-4 flex flex-wrap justify-end gap-3"><AdminFilterSelect label="Status" value={data.status} items={statuses} placeholder="Semua status" onChange={filterStatus} /></div>
  <section class="panel mt-3 p-0">
    {#if data.profiles.items.length}
      <table class="table-fixed"><thead><tr><th>Jenis</th><th>Status</th><th>Review dan revisi</th><th class="text-right">Aksi</th></tr></thead><tbody>{#each data.profiles.items as profile}<tr><td><strong class="block text-sm text-[#263a30]">{profile.revision.display_name}</strong><code class="text-xs text-[#829088]">{profile.canonical_key} · {profile.locale}</code><p class="m-0 mt-1 text-xs text-[#66766f]">{profile.revision.summary}</p></td><td><span class="badge">{statusLabel(profile.status)}</span></td><td class="text-sm"><span>{reviewed(profile) ? 'Sudah ditinjau' : 'Perlu ditinjau'}</span><span class="block text-xs text-[#66766f]">Revisi v{profile.revision.revision}</span></td><td class="text-right"><button class="secondary" type="button" onclick={() => selected = profile}>Kelola</button></td></tr>{/each}</tbody></table>
    {:else}<div class="empty">Belum ada profil jenis pada filter ini.</div>{/if}
    <TablePagination count={data.profiles.total} page={data.profiles.page} perPage={data.profiles.page_size} onChange={updatePage} />
  </section>
</AdminShell>

{#if selected}
  <dialog open class="m-auto max-h-[calc(100dvh-2rem)] w-[min(92vw,42rem)] overflow-y-auto rounded-xl border border-[#dbe4df] bg-white p-0 text-[#17241f] shadow-[0_24px_70px_rgba(23,36,31,.22)]" aria-labelledby="profile-detail-title">
    <div class="flex items-start justify-between gap-4 border-b border-[#e5ebe8] px-5 py-4"><div><p class="mb-1 text-xs font-bold uppercase tracking-wider text-[#6f7e76]">Profil jenis</p><h2 id="profile-detail-title" class="m-0 text-lg font-bold">{selected.revision.display_name}</h2><code class="text-xs text-[#66766f]">{selected.canonical_key} · {selected.locale}</code></div><button class="secondary" type="button" onclick={() => selected = null}>Tutup</button></div>
    <form class="grid gap-3 px-5 py-5" method="POST" action="?/revise" use:enhance>
      <input type="hidden" name="id" value={selected.id} />
      <label>Nama tampilan<input name="display_name" value={selected.revision.display_name} required /></label>
      <label>Ringkasan<textarea name="summary" required>{selected.revision.summary}</textarea></label>
      <label>Kelebihan<textarea name="strengths" required>{selected.revision.strengths}</textarea></label>
      <label>Kekurangan<textarea name="limitations" required>{selected.revision.limitations}</textarea></label>
      <label>Disclaimer<textarea name="disclaimer" required>{selected.revision.disclaimer}</textarea></label>
      <label>Sumber (satu URL per baris)<textarea name="sources" required>{selected.revision.sources.join('\n')}</textarea></label>
      <p class="m-0 text-xs leading-5 text-[#66766f]">Menyimpan perubahan konten akan mengembalikan status ke draft dan memerlukan review ulang.</p>
      <button type="submit">Simpan revisi</button>
    </form>
    <form class="grid gap-3 px-5 py-4" method="POST" action="?/review" use:enhance>
      <input type="hidden" name="id" value={selected.id} />
      <p class="m-0 text-xs">Simpan perubahan terlebih dahulu. Review berlaku untuk konten tersimpan, bukan perubahan yang belum disimpan.</p>
      <label class="inline-flex items-center gap-2 text-sm font-normal"><input type="checkbox" name="content_reviewed" value="true" required /> Saya sudah meninjau isi dan sumber tersimpan</label>
      <button type="submit">Simpan review</button>
    </form>
    <div class="flex flex-wrap justify-end gap-2 border-t border-[#e5ebe8] px-5 py-4">
      <form method="POST" action="?/activate" use:enhance><input type="hidden" name="id" value={selected.id} /><input type="hidden" name="reason" value="Publikasi profil yang telah ditinjau" /><button type="submit">Aktifkan</button></form>
      <form method="POST" action="?/deactivate" use:enhance><input type="hidden" name="id" value={selected.id} /><input type="hidden" name="reason" value="Menarik profil dari publikasi" /><button class="danger" type="submit">Nonaktifkan</button></form>
    </div>
  </dialog>
{/if}
