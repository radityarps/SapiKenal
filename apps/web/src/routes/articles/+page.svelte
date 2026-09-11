<script lang="ts">
	import { enhance } from "$app/forms";
	import { goto } from "$app/navigation";
	import { Archive, Eye, EyeOff, Pencil, Plus } from "lucide-svelte";
	import AdminFilterSelect from "$lib/components/AdminFilterSelect.svelte";
	import AdminShell from "$lib/components/AdminShell.svelte";
	import TablePagination from "$lib/components/TablePagination.svelte";

	export let data: {
		user: App.Locals["user"];
		articles: any;
		filters: { category: string; locale: string; publication_status: string; revision_status: string };
		error: string | null;
	};
	export let form: { success?: boolean; error?: string } | null;

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
	const locales = [
		{ value: "__all__", label: "Semua locale" },
		{ value: "id-ID", label: "Indonesia (id-ID)" },
		{ value: "en-US", label: "English (en-US)" },
	];
	const publicationStatuses = [
		{ value: "__all__", label: "Semua publikasi" },
		{ value: "draft", label: "Draft" },
		{ value: "active", label: "Aktif" },
		{ value: "inactive", label: "Nonaktif" },
	];
	const revisionStatuses = [
		{ value: "__all__", label: "Semua revisi terbaru" },
		{ value: "draft", label: "Draft" },
		{ value: "active", label: "Aktif" },
		{ value: "inactive", label: "Nonaktif" },
	];

	const categoryLabel = (category: string) =>
		categories.find((item) => item.value === category)?.label ?? category;
	const localeLabel = (locale: string) =>
		locales.find((item) => item.value === locale)?.label ?? locale;
	const statusLabel = (status: string) =>
		({ draft: "Draft", active: "Aktif", inactive: "Nonaktif" })[status] ?? status;
	const reviewed = (article: any) => Boolean(article.revision.content_reviewed);
	const isActive = (article: any) => article.publication_status === "active";
	// Publish: gunakan review_and_activate jika belum review, activate jika sudah
	const publishAction = (article: any) =>
		!reviewed(article) && article.revision.sources?.length > 0
			? "?/review_and_activate"
			: "?/activate";
	const publishTooltip = (article: any) => {
		if (isActive(article)) return ""; // tidak dipakai saat aktif
		if (!reviewed(article) && article.revision.sources?.length > 0)
			return "Tinjau & publikasikan artikel";
		if (reviewed(article)) return "Publikasikan artikel";
		return "Perlu review sebelum publikasi";
	};
	const canPublishAction = (article: any) =>
		!isActive(article) &&
		article.revision.sources?.length > 0 &&
		article.revision.status !== "active";

	function updateFilter(key: string, value: string) {
		const query = new URLSearchParams(window.location.search);
		if (value) query.set(key, value);
		else query.delete(key);
		query.delete("page");
		goto(`?${query}`, { keepFocus: true, noScroll: true, invalidateAll: true });
	}
	function updatePage(page: number) {
		const query = new URLSearchParams(window.location.search);
		query.set("page", String(page));
		goto(`?${query}`, { keepFocus: true, noScroll: true, invalidateAll: true });
	}
	function pairingState(article: any) {
		const pair = article.locale_pair;
		if (!pair || pair.status === "missing") return "Pasangan locale belum dibuat";
		if (pair.status !== "active") return `Pasangan ${localeLabel(pair.locale)} belum aktif`;
		return `Pasangan ${localeLabel(pair.locale)} aktif`;
	}
</script>

<svelte:head><title>Artikel Panduan — SapiKenal Admin</title></svelte:head>
<AdminShell title="Artikel Panduan" eyebrow="Konten dan publikasi" active="/articles" user={data.user}>
	<section class="page-intro"><p class="muted">Kelola panduan penggunaan aplikasi dan informasi jenis sapi. Setiap locale memiliki revisi, review, dan status publikasi sendiri.</p></section>
	{#if data.error}<p class="error" role="alert">Data Artikel Panduan tidak dapat dimuat: {data.error}</p>{/if}
	{#if form?.error}<p class="error" role="alert">{form.error}</p>{/if}
	{#if form?.success}<p class="notice" role="status">Perubahan Artikel Panduan berhasil disimpan.</p>{/if}

	<div class="mt-5 flex flex-wrap items-end justify-between gap-3">
		<div>
			<h2 class="m-0 text-lg font-bold text-[#263a30]">Artikel terdaftar</h2>
			<p class="mt-1 text-sm text-[#66766f]">{data.articles.total ?? 0} artikel pada hasil filter.</p>
		</div>
		<a class="button flex items-center gap-2 whitespace-nowrap" href="/articles/create">
			<Plus size={17} strokeWidth={2} aria-hidden="true" />Tambah Artikel Panduan
		</a>
	</div>

	<div class="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
		<AdminFilterSelect label="Kategori" value={data.filters.category} items={categories} placeholder="Semua kategori" onChange={(value) => updateFilter("category", value)} />
		<AdminFilterSelect label="Locale" value={data.filters.locale} items={locales} placeholder="Semua locale" onChange={(value) => updateFilter("locale", value)} />
		<AdminFilterSelect label="Status publikasi" value={data.filters.publication_status} items={publicationStatuses} placeholder="Semua publikasi" onChange={(value) => updateFilter("publication_status", value)} />
		<AdminFilterSelect label="Status revisi terbaru" value={data.filters.revision_status} items={revisionStatuses} placeholder="Semua revisi terbaru" onChange={(value) => updateFilter("revision_status", value)} />
	</div>

	<section class="panel mt-3 p-0">
		{#if data.articles.items.length}
			<table class="table-fixed">
				<thead>
					<tr>
						<th>Artikel</th>
						<th>Kategori</th>
						<th>Locale</th>
						<th>Status</th>
						<th>Review dan pasangan</th>
						<th class="w-24 text-right">Aksi</th>
					</tr>
				</thead>
				<tbody>
					{#each data.articles.items as article}
						<tr>
							<td class="whitespace-normal">
								<strong class="block text-sm text-[#263a30]">{article.revision.title}</strong>
								<code class="text-xs text-[#829088]">{article.article_key} · v{article.revision.revision}</code>
								<p class="m-0 mt-1 text-xs text-[#66766f]">{article.revision.summary}</p>
							</td>
							<td class="whitespace-normal text-sm">{categoryLabel(article.revision.category)}</td>
							<td class="text-sm">{localeLabel(article.locale)}</td>
							<td class="whitespace-normal text-sm">
								<span
									class="badge"
									class:!bg-[#e8f4ef]={article.publication_status === 'active'}
									class:!text-[#145c3e]={article.publication_status === 'active'}
									class:!bg-[#f9e9ec]={article.publication_status === 'inactive'}
									class:!text-[#8b2635]={article.publication_status === 'inactive'}
								>Publik: {statusLabel(article.publication_status)}</span>
								<span class="mt-1 block text-xs text-[#66766f]">
									Revisi terbaru: v{article.revision.revision} · {statusLabel(article.revision.status)}
								</span>
								{#if article.active_revision}
									<span class="block text-xs text-[#66766f]">Publik saat ini: v{article.active_revision.revision}</span>
								{/if}
							</td>
							<td class="whitespace-normal text-sm">
								<span>{reviewed(article) ? 'Sudah ditinjau' : 'Perlu ditinjau'}</span>
								<span class="block text-xs text-[#66766f]">{pairingState(article)}</span>
							</td>

							<!-- Kolom Aksi: 3 icon button -->
							<td class="text-right">
								<div class="inline-flex items-center justify-end gap-1">

									<!-- Edit -->
									<a
										href="/articles/{article.id}/edit"
										title="Edit artikel"
										aria-label="Edit artikel"
										class="inline-flex h-8 w-8 items-center justify-center rounded-md text-[#4a6358] transition-colors hover:bg-[#e8f0eb] hover:text-[#17241f]"
									>
										<Pencil size={15} aria-hidden="true" />
									</a>

									<!-- Publish / Unpublish -->
									{#if isActive(article)}
										<form method="POST" action="?/deactivate" use:enhance>
											<input type="hidden" name="id" value={article.id} />
											<input type="hidden" name="reason" value="Menarik Artikel Panduan dari publikasi" />
											<button
												type="submit"
												title="Nonaktifkan — tarik dari publikasi"
												aria-label="Nonaktifkan artikel"
												class="inline-flex h-8 w-8 items-center justify-center rounded-md text-[#145c3e] transition-colors hover:bg-[#f9e9ec] hover:text-[#8b2635]"
											>
												<EyeOff size={15} aria-hidden="true" />
											</button>
										</form>
									{:else if canPublishAction(article)}
										<form method="POST" action={publishAction(article)} use:enhance>
											<input type="hidden" name="id" value={article.id} />
											<input type="hidden" name="reason" value="Publikasi Artikel Panduan yang telah ditinjau" />
											<button
												type="submit"
												title={publishTooltip(article)}
												aria-label={publishTooltip(article)}
												class="inline-flex h-8 w-8 items-center justify-center rounded-md text-[#4a6358] transition-colors hover:bg-[#e8f0eb] hover:text-[#145c3e]"
											>
												<Eye size={15} aria-hidden="true" />
											</button>
										</form>
									{:else}
										<!-- Publish tidak tersedia (belum ada sumber / perlu review) -->
										<span
											title={!article.revision.sources?.length ? "Perlu sumber rujukan sebelum publikasi" : "Perlu ditinjau sebelum publikasi"}
											aria-label="Publikasi tidak tersedia"
											class="inline-flex h-8 w-8 cursor-not-allowed items-center justify-center rounded-md text-[#b2bfb9]"
										>
											<Eye size={15} aria-hidden="true" />
										</span>
									{/if}

									<!-- Archive (nonaktifkan permanen, hanya saat bukan draft) -->
									{#if article.publication_status !== 'draft'}
										<form method="POST" action="?/deactivate" use:enhance>
											<input type="hidden" name="id" value={article.id} />
											<input type="hidden" name="reason" value="Mengarsipkan Artikel Panduan" />
											<button
												type="submit"
												title="Arsipkan artikel"
												aria-label="Arsipkan artikel"
												class="inline-flex h-8 w-8 items-center justify-center rounded-md text-[#4a6358] transition-colors hover:bg-[#f9e9ec] hover:text-[#8b2635]"
											>
												<Archive size={15} aria-hidden="true" />
											</button>
										</form>
									{:else}
										<span
											title="Artikel draft tidak dapat diarsipkan"
											class="inline-flex h-8 w-8 cursor-not-allowed items-center justify-center rounded-md text-[#b2bfb9]"
										>
											<Archive size={15} aria-hidden="true" />
										</span>
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
