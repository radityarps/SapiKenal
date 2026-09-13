<script lang="ts">
  import { tick } from "svelte";
  import { enhance } from "$app/forms";
  import { goto } from "$app/navigation";
  import {
    Archive,
    Eye,
    EyeOff,
    Globe,
    Pencil,
    Plus,
    Search,
    X,
  } from "lucide-svelte";
  import AdminFilterSelect from "$lib/components/AdminFilterSelect.svelte";
  import AdminShell from "$lib/components/AdminShell.svelte";
  import TablePagination from "$lib/components/TablePagination.svelte";

  export let data: {
    user: App.Locals["user"];
    articles: any;
    filters: {
      search: string;
      category: string;
      publication_status: string;
      revision_status: string;
    };
    error: string | null;
  };
  export let form: { success?: boolean; error?: string } | null;

  let selectedArticle: any = null;
  let detailDialog: HTMLDialogElement | undefined;
  let search = data.filters.search;
  let searchTimer: ReturnType<typeof setTimeout>;

  const categories = [
    { value: "__all__", label: "Semua kategori" },
    { value: "app_usage", label: "Penggunaan aplikasi" },
    { value: "aceh", label: "Aceh" },
    { value: "bali", label: "Bali" },
    { value: "brahman", label: "Brahman" },
    { value: "brangus", label: "Brangus" },
    { value: "limusin", label: "Limusin" },
    { value: "madura", label: "Madura" },
    { value: "pasundan", label: "Pasundan" },
    { value: "po", label: "PO" },
  ];

  const publicationStatuses = [
    { value: "__all__", label: "Semua publikasi" },
    { value: "draft", label: "Draft" },
    { value: "active", label: "Aktif" },
    { value: "inactive", label: "Nonaktif" },
  ];

  const revisionStatuses = [
    { value: "__all__", label: "Semua revisi" },
    { value: "draft", label: "Draft" },
    { value: "active", label: "Aktif" },
    { value: "inactive", label: "Nonaktif" },
  ];

  const categoryLabel = (category: string) =>
    categories.find((item) => item.value === category)?.label ?? category;
  const statusLabel = (status: string) =>
    ({ draft: "Draft", active: "Aktif", inactive: "Nonaktif" })[status] ?? status;
  const reviewed = (article: any) => Boolean(article?.revision?.content_reviewed);
  const isActive = (article: any) => article?.publication_status === "active";
  const publishAction = (article: any) =>
    !reviewed(article) && article?.revision?.sources?.length > 0
      ? "?/review_and_activate"
      : "?/activate";
  const publishTooltip = (article: any) => {
    if (isActive(article)) return "";
    if (!reviewed(article) && article?.revision?.sources?.length > 0)
      return "Tinjau dan publikasikan artikel";
    if (reviewed(article)) return "Publikasikan artikel";
    return "Perlu peninjauan sebelum publikasi";
  };
  const canPublishAction = (article: any) =>
    !isActive(article) &&
    article?.revision?.sources?.length > 0 &&
    article?.revision?.status !== "active";

  async function openDetail(article: any) {
    selectedArticle = article;
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
    if (value && value !== "__all__") query.set(key, value);
    else query.delete(key);
    query.delete("page");
    goto(`?${query}`, { keepFocus: true, noScroll: true, invalidateAll: true });
  }

  function debounceSearch(value: string) {
    search = value;
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => updateQuery("search", value.trim()), 350);
  }

  function updatePage(page: number) {
    const query = new URLSearchParams(window.location.search);
    query.set("page", String(page));
    goto(`?${query}`, { keepFocus: true, noScroll: true, invalidateAll: true });
  }
</script>

<svelte:head><title>Artikel Panduan · SapiKenal Admin</title></svelte:head>
<AdminShell title="Artikel Panduan" eyebrow="Konten dan publikasi" active="/articles" user={data.user}>
  <section class="page-intro">
    <p class="muted">Kelola panduan penggunaan aplikasi dan informasi jenis sapi.</p>
  </section>

  {#if data.error}<p class="error" role="alert">Data Artikel Panduan tidak dapat dimuat: {data.error}</p>{/if}
  {#if form?.error}<p class="error" role="alert">{form.error}</p>{/if}
  {#if form?.success}<p class="notice" role="status">Perubahan Artikel Panduan berhasil disimpan.</p>{/if}

  <div class="mt-4 grid gap-3 lg:grid-cols-[minmax(14rem,0.8fr)_minmax(24rem,1.2fr)_auto]">
    <div>
      <label class="relative">
        <span>Cari artikel</span>
        <Search class="pointer-events-none absolute bottom-3 left-3 text-[#718078]" size={16} aria-hidden="true" />
        <input
          class="w-full pl-9"
          type="search"
          value={search}
          placeholder="Judul, key, atau ringkasan"
          oninput={(event) => debounceSearch(event.currentTarget.value)}
        />
      </label>
    </div>
    <div class="grid gap-3 sm:grid-cols-3">
      <AdminFilterSelect
        label="Kategori"
        value={data.filters.category}
        items={categories}
        placeholder="Semua kategori"
        onChange={(value) => updateQuery("category", value)}
      />
      <AdminFilterSelect
        label="Status publikasi"
        value={data.filters.publication_status}
        items={publicationStatuses}
        placeholder="Semua publikasi"
        onChange={(value) => updateQuery("publication_status", value)}
      />
      <AdminFilterSelect
        label="Status revisi"
        value={data.filters.revision_status}
        items={revisionStatuses}
        placeholder="Semua revisi"
        onChange={(value) => updateQuery("revision_status", value)}
      />
    </div>
    <div class="flex items-end">
      <a
        class="button inline-flex h-10 w-full items-center justify-center gap-2 whitespace-nowrap rounded-lg bg-[#176b49] px-3.5 py-2 text-sm font-semibold text-white shadow-2xs transition hover:bg-[#125a3d]"
        href="/articles/create"
      >
        <Plus size={16} strokeWidth={2.2} aria-hidden="true" />
        <span>Tambah Artikel</span>
      </a>
    </div>
  </div>

  <section class="panel mt-3 p-0">
    {#if data.articles.items.length}
      <table class="table-fixed">
        <thead>
          <tr>
            <th class="w-[35%]">Artikel</th>
            <th class="w-[15%]">Kategori</th>
            <th class="w-[20%]">Status</th>
            <th class="w-[15%]">Review</th>
            <th class="w-32 text-center"><span class="sr-only">Aksi</span></th>
          </tr>
        </thead>
        <tbody>
          {#each data.articles.items as article}
            <tr>
              <!-- Artikel (Judul, key, summary) -->
              <td class="whitespace-normal">
                <strong class="block text-sm font-semibold text-[#17241f]">{article.revision.title}</strong>
                <div class="mt-1 flex flex-wrap items-center gap-1.5">
                  <code class="rounded-md bg-[#f1f5f3] px-2 py-0.5 font-mono text-[.72rem] text-[#40554a]">{article.article_key}</code>
                  <span class="text-xs text-[#52655c]">· v{article.revision.revision}</span>
                </div>
                {#if article.revision.summary}
                  <p class="m-0 mt-1 line-clamp-2 text-xs leading-relaxed text-[#53645b]">{article.revision.summary}</p>
                {/if}
              </td>

              <!-- Kategori -->
              <td class="whitespace-normal text-xs font-semibold text-[#40554a]">
                {categoryLabel(article.revision.category)}
              </td>

              <!-- Status Publikasi & Revisi -->
              <td class="whitespace-normal">
                {#if article.publication_status === 'active'}
                  <span class="badge !bg-[#eaf6f0] !text-[#0f5436]">Publik: Aktif</span>
                {:else if article.publication_status === 'inactive'}
                  <span class="badge !bg-[#fdf2f4] !text-[#861f2f]">Publik: Nonaktif</span>
                {:else}
                  <span class="badge !bg-[#fffaf0] !text-[#764b07]">Publik: Draft</span>
                {/if}
                <span class="mt-1.5 block text-xs text-[#52655c]">
                  Revisi terbaru: v{article.revision.revision} · {statusLabel(article.revision.status)}
                </span>
                {#if article.active_revision}
                  <span class="mt-0.5 block text-xs text-[#52655c]">Publik saat ini: v{article.active_revision.revision}</span>
                {/if}
              </td>

              <!-- Review -->
              <td class="whitespace-normal">
                {#if reviewed(article)}
                  <span class="badge !bg-[#eaf6f0] !text-[#0f5436]">Sudah ditinjau</span>
                {:else}
                  <span class="badge !bg-[#fffaf0] !text-[#764b07]">Perlu ditinjau</span>
                {/if}
              </td>

              <!-- Aksi -->
              <td class="text-center">
                <div class="inline-flex items-center justify-center gap-1">
                  <!-- Lihat Detail Modal Button -->
                  <button
                    class="grid size-9 min-h-0 place-items-center rounded-lg bg-transparent p-0 text-[#426353] hover:bg-[#edf5f1] hover:text-[#176b49]"
                    type="button"
                    aria-label={`Lihat detail artikel ${article.revision?.title || article.article_key}`}
                    title="Lihat detail"
                    onclick={() => openDetail(article)}
                  >
                    <Eye size={17} strokeWidth={1.8} aria-hidden="true" />
                  </button>

                  <!-- Edit Button -->
                  <a
                    href={`/articles/${article.id}/edit`}
                    class="grid size-9 min-h-0 place-items-center rounded-lg bg-transparent p-0 text-[#426353] hover:bg-[#edf5f1] hover:text-[#176b49]"
                    title="Edit artikel"
                    aria-label={`Edit artikel ${article.revision?.title || article.article_key}`}
                  >
                    <Pencil size={16} strokeWidth={1.8} aria-hidden="true" />
                  </a>

                  <!-- Publikasi / Tarik Button -->
                  {#if isActive(article)}
                    <form method="POST" action="?/deactivate" use:enhance class="inline">
                      <input type="hidden" name="id" value={article.id} />
                      <input type="hidden" name="reason" value="Menarik Artikel Panduan dari publikasi" />
                      <button
                        type="submit"
                        title="Tarik dari publikasi"
                        aria-label="Tarik artikel dari publikasi"
                        class="grid size-9 min-h-0 place-items-center rounded-lg bg-transparent p-0 text-[#8b2635] hover:bg-[#f9e9ec] hover:text-[#8b2635]"
                      >
                        <EyeOff size={16} strokeWidth={1.8} aria-hidden="true" />
                      </button>
                    </form>
                  {:else if canPublishAction(article)}
                    <form method="POST" action={publishAction(article)} use:enhance class="inline">
                      <input type="hidden" name="id" value={article.id} />
                      <input type="hidden" name="reason" value="Publikasi Artikel Panduan yang telah ditinjau" />
                      <button
                        type="submit"
                        title={publishTooltip(article)}
                        aria-label={publishTooltip(article)}
                        class="grid size-9 min-h-0 place-items-center rounded-lg bg-transparent p-0 text-[#176b49] hover:bg-[#edf5f1] hover:text-[#125a3d]"
                      >
                        <Globe size={16} strokeWidth={1.8} aria-hidden="true" />
                      </button>
                    </form>
                  {:else}
                    <span
                      title={!article.revision?.sources?.length ? "Perlu sumber rujukan sebelum publikasi" : "Perlu ditinjau sebelum publikasi"}
                      aria-label="Publikasi tidak tersedia"
                      class="grid size-9 min-h-0 cursor-not-allowed place-items-center rounded-lg bg-transparent p-0 text-[#a3b3aa]"
                    >
                      <Globe size={16} strokeWidth={1.8} aria-hidden="true" />
                    </span>
                  {/if}

                  <!-- Arsip Button -->
                  {#if article.publication_status !== 'draft'}
                    <form method="POST" action="?/deactivate" use:enhance class="inline">
                      <input type="hidden" name="id" value={article.id} />
                      <input type="hidden" name="reason" value="Mengarsipkan Artikel Panduan" />
                      <button
                        type="submit"
                        title="Arsipkan artikel"
                        aria-label="Arsipkan artikel"
                        class="grid size-9 min-h-0 place-items-center rounded-lg bg-transparent p-0 text-[#64736c] hover:bg-[#edf2ef] hover:text-[#263a30]"
                      >
                        <Archive size={16} strokeWidth={1.8} aria-hidden="true" />
                      </button>
                    </form>
                  {/if}
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    {:else}
      <div class="empty">Belum ada Artikel Panduan pada filter ini.</div>
    {/if}
    <TablePagination count={data.articles.total} page={data.articles.page} perPage={data.articles.page_size} onChange={updatePage} />
  </section>
</AdminShell>

<dialog
  bind:this={detailDialog}
  class="m-auto max-h-[calc(100dvh-2rem)] w-[min(92vw,44rem)] overflow-y-auto rounded-xl border border-[#dbe4df] bg-white p-0 text-[#17241f] shadow-[0_24px_70px_rgba(23,36,31,.22)] backdrop:bg-[#17241f]/35"
  aria-labelledby="article-detail-title"
  onclick={closeFromBackdrop}
>
  {#if selectedArticle}
    <div class="flex items-start justify-between gap-4 border-b border-[#e5ebe8] px-5 py-4">
      <div>
        <p class="mb-1 text-[.67rem] font-bold uppercase tracking-[.1em] text-[#6f7e76]">Detail Artikel Panduan</p>
        <h2 id="article-detail-title" class="m-0 text-lg font-bold">{selectedArticle.revision?.title}</h2>
      </div>
      <button
        class="grid size-9 min-h-0 place-items-center rounded-lg bg-transparent p-0 text-[#64736c] hover:bg-[#edf2ef] hover:text-[#263a30]"
        type="button"
        aria-label="Tutup detail"
        onclick={closeDetail}
      >
        <X size={18} aria-hidden="true" />
      </button>
    </div>
    <div class="grid gap-5 px-5 py-5">
      <div class="flex flex-wrap items-center gap-2 rounded-lg bg-[#f3f7f5] px-3.5 py-3">
        {#if selectedArticle.publication_status === 'active'}
          <span class="badge !bg-[#eaf6f0] !text-[#0f5436]">Publik: Aktif</span>
        {:else if selectedArticle.publication_status === 'inactive'}
          <span class="badge !bg-[#fdf2f4] !text-[#861f2f]">Publik: Nonaktif</span>
        {:else}
          <span class="badge !bg-[#fffaf0] !text-[#764b07]">Publik: Draft</span>
        {/if}
        <span class="text-xs text-[#52655c]">
          Versi aktif: {selectedArticle.active_revision ? `v${selectedArticle.active_revision.revision}` : 'Belum pernah dipublikasikan'}
        </span>
        <span class="text-xs text-[#52655c]">·</span>
        <span class="text-xs text-[#52655c]">
          Revisi terbaru: v{selectedArticle.revision?.revision} ({selectedArticle.revision?.content_reviewed ? 'Sudah ditinjau' : 'Perlu ditinjau'})
        </span>
      </div>

      {#if selectedArticle.revision?.summary}
        <div class="rounded-lg border border-[#e4ebe7] bg-white p-3.5">
          <h3 class="m-0 mb-1.5 text-xs font-bold text-[#55675f]">Ringkasan</h3>
          <p class="m-0 text-xs leading-relaxed text-[#263a30]">{selectedArticle.revision.summary}</p>
        </div>
      {/if}

      {#if selectedArticle.revision?.body}
        <div class="rounded-lg border border-[#e4ebe7] bg-[#fafcfb] p-3.5">
          <h3 class="m-0 mb-1.5 text-xs font-bold text-[#55675f]">Konten Panduan</h3>
          <div class="max-h-48 overflow-y-auto whitespace-pre-wrap text-xs leading-relaxed text-[#33473e]">
            {selectedArticle.revision.body}
          </div>
        </div>
      {/if}

      <dl class="m-0 grid gap-x-5 gap-y-4 text-sm sm:grid-cols-2">
        <div><dt class="text-xs font-bold text-[#718078]">Article key</dt><dd class="m-0 mt-1 font-mono text-xs text-[#243d30]">{selectedArticle.article_key}</dd></div>
        <div><dt class="text-xs font-bold text-[#718078]">Kategori</dt><dd class="m-0 mt-1">{categoryLabel(selectedArticle.revision?.category)}</dd></div>
        <div><dt class="text-xs font-bold text-[#718078]">Urutan tampil</dt><dd class="m-0 mt-1">{selectedArticle.revision?.sort_order ?? 0}</dd></div>
        <div><dt class="text-xs font-bold text-[#718078]">Status review</dt><dd class="m-0 mt-1">{selectedArticle.revision?.content_reviewed ? 'Sudah ditinjau' : 'Perlu ditinjau'}</dd></div>
        {#if selectedArticle.revision?.sources?.length}
          <div class="sm:col-span-2">
            <dt class="text-xs font-bold text-[#718078]">Sumber rujukan</dt>
            <dd class="m-0 mt-1">
              <ul class="m-0 list-disc pl-4 text-xs text-[#355243]">
                {#each selectedArticle.revision.sources as src}
                  <li class="break-all">{src}</li>
                {/each}
              </ul>
            </dd>
          </div>
        {/if}
      </dl>

      <div class="flex items-center justify-end gap-2 border-t border-[#e5ebe8] pt-4">
        <a
          href={`/articles/${selectedArticle.id}/edit`}
          class="button inline-flex h-9 items-center gap-1.5 rounded-lg bg-[#176b49] px-3.5 text-xs font-semibold text-white transition hover:bg-[#125a3d]"
        >
          <Pencil size={14} strokeWidth={2} aria-hidden="true" />
          <span>Edit Artikel</span>
        </a>
      </div>
    </div>
  {/if}
</dialog>
