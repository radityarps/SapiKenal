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
	const reviewed = (article: any) => Boolean(article.revision?.content_reviewed);
	const isActive = (article: any) => article.publication_status === "active";
	// Publish: gunakan review_and_activate jika belum review, activate jika sudah
	const publishAction = (article: any) =>
		!reviewed(article) && article.revision?.sources?.length > 0
			? "?/review_and_activate"
			: "?/activate";
	const publishTooltip = (article: any) => {
		if (isActive(article)) return ""; // tidak dipakai saat aktif
		if (!reviewed(article) && article.revision?.sources?.length > 0)
			return "Tinjau & publikasikan artikel";
		if (reviewed(article)) return "Publikasikan artikel";
		return "Perlu review sebelum publikasi";
	};
	const canPublishAction = (article: any) =>
		!isActive(article) &&
		article.revision?.sources?.length > 0 &&
		article.revision?.status !== "active";

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

	<div class="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
		<div>
			<h2 class="m-0 text-base font-bold text-[#17241f]">Artikel terdaftar</h2>
			<p class="mt-0.5 text-xs text-[#52655c]">{data.articles.total ?? 0} artikel pada hasil filter.</p>
		</div>
		<a class="button inline-flex items-center justify-center gap-2 rounded-lg bg-[#176b49] px-3.5 py-2 text-sm font-semibold text-white shadow-2xs transition hover:bg-[#125a3d]" href="/articles/create">
			<Plus size={16} strokeWidth={2.2} aria-hidden="true" />
			<span>Tambah Artikel Panduan</span>
		</a>
	</div>

	<div class="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
		<AdminFilterSelect label="Kategori" value={data.filters.category} items={categories} placeholder="Semua kategori" onChange={(value) => updateFilter("category", value)} />
		<AdminFilterSelect label="Locale" value={data.filters.locale} items={locales} placeholder="Semua locale" onChange={(value) => updateFilter("locale", value)} />
		<AdminFilterSelect label="Status publikasi" value={data.filters.publication_status} items={publicationStatuses} placeholder="Semua publikasi" onChange={(value) => updateFilter("publication_status", value)} />
		<AdminFilterSelect label="Status revisi terbaru" value={data.filters.revision_status} items={revisionStatuses} placeholder="Semua revisi terbaru" onChange={(value) => updateFilter("revision_status", value)} />
	</div>

	<section class="panel mt-4 overflow-hidden p-0">
		{#if data.articles.items.length}
			<!-- Desktop Table Layout (md and up) -->
			<div class="hidden overflow-x-auto md:block">
				<table class="w-full table-fixed border-collapse">
					<thead>
						<tr class="border-b border-[#e2e8e4] bg-[#f8faf9]">
							<th class="w-[34%] px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-[#35483f]">Artikel</th>
							<th class="w-[14%] px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-[#35483f]">Kategori</th>
							<th class="w-[12%] px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-[#35483f]">Locale</th>
							<th class="w-[18%] px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-[#35483f]">Status</th>
							<th class="w-[18%] px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-[#35483f]">Review & Pasangan</th>
							<th class="w-24 px-4 py-3 text-right text-xs font-bold uppercase tracking-wider text-[#35483f]">Aksi</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-[#e8edea]">
						{#each data.articles.items as article}
							<tr class="transition-colors hover:bg-[#f9fbf9]">
								<!-- Artikel (Judul, key, summary) -->
								<td class="whitespace-normal px-4 py-3.5 align-top">
									<strong class="block text-sm font-semibold text-[#17241f]">{article.revision.title}</strong>
									<div class="mt-1 flex flex-wrap items-center gap-1.5">
										<code class="rounded bg-[#edf2ef] px-1.5 py-0.5 font-mono text-[0.72rem] font-semibold text-[#243d30]">{article.article_key}</code>
										<span class="text-xs text-[#52655c]">· v{article.revision.revision}</span>
									</div>
									{#if article.revision.summary}
										<p class="m-0 mt-1.5 line-clamp-2 text-xs leading-relaxed text-[#44574f]">{article.revision.summary}</p>
									{/if}
								</td>

								<!-- Kategori -->
								<td class="whitespace-normal px-4 py-3.5 text-sm font-medium text-[#1e3228] align-top">
									{categoryLabel(article.revision.category)}
								</td>

								<!-- Locale -->
								<td class="whitespace-normal px-4 py-3.5 align-top">
									<span class="inline-flex items-center rounded-md border border-[#d3ded8] bg-[#f4f7f5] px-2 py-0.5 font-mono text-xs font-semibold text-[#1f372c]">
										{localeLabel(article.locale)}
									</span>
								</td>

								<!-- Status -->
								<td class="whitespace-normal px-4 py-3.5 align-top">
									{#if article.publication_status === 'active'}
										<span class="inline-flex items-center rounded-full border border-[#b7dfcb] bg-[#eaf6f0] px-2.5 py-0.5 text-xs font-semibold text-[#0f5436]">
											Publik: Aktif
										</span>
									{:else if article.publication_status === 'inactive'}
										<span class="inline-flex items-center rounded-full border border-[#f2c7ce] bg-[#fdf2f4] px-2.5 py-0.5 text-xs font-semibold text-[#861f2f]">
											Publik: Nonaktif
										</span>
									{:else}
										<span class="inline-flex items-center rounded-full border border-[#f0dfad] bg-[#fffaf0] px-2.5 py-0.5 text-xs font-semibold text-[#764b07]">
											Publik: Draft
										</span>
									{/if}
									<span class="mt-1.5 block text-xs text-[#52655c]">
										Revisi terbaru: v{article.revision.revision} · {statusLabel(article.revision.status)}
									</span>
									{#if article.active_revision}
										<span class="mt-0.5 block text-xs text-[#52655c]">Publik saat ini: v{article.active_revision.revision}</span>
									{/if}
								</td>

								<!-- Review & Pasangan -->
								<td class="whitespace-normal px-4 py-3.5 align-top">
									<div class="flex items-center gap-1.5">
										{#if reviewed(article)}
											<span class="inline-flex items-center rounded-md border border-[#c1e2d1] bg-[#eff8f3] px-2 py-0.5 text-[0.72rem] font-semibold text-[#0e5234]">
												Sudah ditinjau
											</span>
										{:else}
											<span class="inline-flex items-center rounded-md border border-[#f0dfad] bg-[#fffaf0] px-2 py-0.5 text-[0.72rem] font-semibold text-[#764b07]">
												Perlu ditinjau
											</span>
										{/if}
									</div>
									<span class="mt-1.5 block text-xs text-[#52655c]">{pairingState(article)}</span>
								</td>

								<!-- Aksi -->
								<td class="whitespace-nowrap px-4 py-3.5 text-right align-top">
									<div class="inline-flex items-center justify-end gap-1.5">
										<!-- Edit -->
										<a
											href="/articles/{article.id}/edit"
											title="Edit artikel"
											aria-label="Edit artikel"
											class="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-[#cfdad4] bg-white text-[#213d30] shadow-2xs transition-colors hover:border-[#176b49] hover:bg-[#edf5f1] hover:text-[#176b49] focus-visible:outline-2 focus-visible:outline-[#176b49]"
										>
											<Pencil size={15} strokeWidth={2} aria-hidden="true" />
										</a>

										<!-- Publish / Unpublish -->
										{#if isActive(article)}
											<form method="POST" action="?/deactivate" use:enhance class="inline">
												<input type="hidden" name="id" value={article.id} />
												<input type="hidden" name="reason" value="Menarik Artikel Panduan dari publikasi" />
												<button
													type="submit"
													title="Nonaktifkan — tarik dari publikasi"
													aria-label="Nonaktifkan artikel"
													class="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-[#f3c2c8] bg-[#fff5f6] text-[#932333] shadow-2xs transition-colors hover:border-[#8b2635] hover:bg-[#8b2635] hover:text-white focus-visible:outline-2 focus-visible:outline-[#8b2635]"
												>
													<EyeOff size={15} strokeWidth={2} aria-hidden="true" />
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
													class="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-[#b8dbc8] bg-[#f0f9f4] text-[#115e3c] shadow-2xs transition-colors hover:border-[#176b49] hover:bg-[#176b49] hover:text-white focus-visible:outline-2 focus-visible:outline-[#176b49]"
												>
													<Eye size={15} strokeWidth={2} aria-hidden="true" />
												</button>
											</form>
										{:else}
											<span
												title={!article.revision?.sources?.length ? "Perlu sumber rujukan sebelum publikasi" : "Perlu ditinjau sebelum publikasi"}
												aria-label="Publikasi tidak tersedia"
												class="inline-flex h-8 w-8 cursor-not-allowed items-center justify-center rounded-lg border border-[#e2e8e4] bg-[#f5f8f6] text-[#8fa097]"
											>
												<Eye size={15} strokeWidth={2} aria-hidden="true" />
											</span>
										{/if}

										<!-- Archive -->
										{#if article.publication_status !== 'draft'}
											<form method="POST" action="?/deactivate" use:enhance class="inline">
												<input type="hidden" name="id" value={article.id} />
												<input type="hidden" name="reason" value="Mengarsipkan Artikel Panduan" />
												<button
													type="submit"
													title="Arsipkan artikel"
													aria-label="Arsipkan artikel"
													class="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-[#d6e0db] bg-white text-[#455c51] shadow-2xs transition-colors hover:border-[#8b2635] hover:bg-[#fff5f6] hover:text-[#8b2635] focus-visible:outline-2 focus-visible:outline-[#8b2635]"
												>
													<Archive size={15} strokeWidth={2} aria-hidden="true" />
												</button>
											</form>
										{:else}
											<span
												title="Artikel draft tidak dapat diarsipkan"
												class="inline-flex h-8 w-8 cursor-not-allowed items-center justify-center rounded-lg border border-[#e2e8e4] bg-[#f5f8f6] text-[#8fa097]"
											>
												<Archive size={15} strokeWidth={2} aria-hidden="true" />
											</span>
										{/if}
									</div>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>

			<!-- Mobile Card Layout (< md) -->
			<div class="divide-y divide-[#e8edea] md:hidden">
				{#each data.articles.items as article}
					<div class="flex flex-col gap-3 p-4">
						<!-- Top row: Title and Status Badge -->
						<div class="flex items-start justify-between gap-3">
							<div class="min-w-0 flex-1">
								<strong class="block text-sm font-semibold text-[#17241f] leading-snug">{article.revision.title}</strong>
								<div class="mt-1 flex flex-wrap items-center gap-1.5">
									<code class="rounded bg-[#edf2ef] px-1.5 py-0.5 font-mono text-[0.72rem] font-semibold text-[#243d30]">{article.article_key}</code>
									<span class="text-xs text-[#52655c]">· v{article.revision.revision}</span>
								</div>
							</div>
							<div class="shrink-0">
								{#if article.publication_status === 'active'}
									<span class="inline-flex items-center rounded-full border border-[#b7dfcb] bg-[#eaf6f0] px-2.5 py-0.5 text-xs font-semibold text-[#0f5436]">
										Publik: Aktif
									</span>
								{:else if article.publication_status === 'inactive'}
									<span class="inline-flex items-center rounded-full border border-[#f2c7ce] bg-[#fdf2f4] px-2.5 py-0.5 text-xs font-semibold text-[#861f2f]">
										Publik: Nonaktif
									</span>
								{:else}
									<span class="inline-flex items-center rounded-full border border-[#f0dfad] bg-[#fffaf0] px-2.5 py-0.5 text-xs font-semibold text-[#764b07]">
										Publik: Draft
									</span>
								{/if}
							</div>
						</div>

						<!-- Summary if present -->
						{#if article.revision.summary}
							<p class="m-0 text-xs leading-relaxed text-[#44574f] line-clamp-2">{article.revision.summary}</p>
						{/if}

						<!-- Meta box -->
						<div class="grid grid-cols-2 gap-2.5 rounded-lg border border-[#e2e8e4] bg-[#f8faf9] p-3 text-xs">
							<div>
								<span class="block text-[0.68rem] font-bold uppercase tracking-wider text-[#566a60]">Kategori</span>
								<span class="mt-0.5 block font-medium text-[#1e3228]">{categoryLabel(article.revision.category)}</span>
							</div>
							<div>
								<span class="block text-[0.68rem] font-bold uppercase tracking-wider text-[#566a60]">Locale</span>
								<span class="mt-0.5 block font-medium text-[#1e3228]">{localeLabel(article.locale)}</span>
							</div>
							<div>
								<span class="block text-[0.68rem] font-bold uppercase tracking-wider text-[#566a60]">Review</span>
								<span class="mt-0.5 block font-medium text-[#1e3228]">{reviewed(article) ? 'Sudah ditinjau' : 'Perlu ditinjau'}</span>
							</div>
							<div>
								<span class="block text-[0.68rem] font-bold uppercase tracking-wider text-[#566a60]">Pasangan</span>
								<span class="mt-0.5 block font-medium text-[#1e3228]">{pairingState(article)}</span>
							</div>
							<div class="col-span-2 border-t border-[#e2e8e4] pt-2">
								<span class="block text-xs text-[#52655c]">
									Revisi terbaru: v{article.revision.revision} · {statusLabel(article.revision.status)}
								</span>
								{#if article.active_revision}
									<span class="mt-0.5 block text-xs text-[#52655c]">Publik saat ini: v{article.active_revision.revision}</span>
								{/if}
							</div>
						</div>

						<!-- Action buttons for Mobile -->
						<div class="flex items-center justify-end gap-2 pt-1">
							<!-- Edit Button -->
							<a
								href="/articles/{article.id}/edit"
								class="inline-flex h-9 items-center gap-1.5 rounded-lg border border-[#cfdad4] bg-white px-3 text-xs font-semibold text-[#213d30] shadow-2xs hover:border-[#176b49] hover:bg-[#edf5f1] hover:text-[#176b49]"
							>
								<Pencil size={14} strokeWidth={2} aria-hidden="true" />
								<span>Edit</span>
							</a>

							<!-- Publish / Unpublish Button -->
							{#if isActive(article)}
								<form method="POST" action="?/deactivate" use:enhance class="inline">
									<input type="hidden" name="id" value={article.id} />
									<input type="hidden" name="reason" value="Menarik Artikel Panduan dari publikasi" />
									<button
										type="submit"
										class="inline-flex h-9 items-center gap-1.5 rounded-lg border border-[#f3c2c8] bg-[#fff5f6] px-3 text-xs font-semibold text-[#932333] shadow-2xs hover:border-[#8b2635] hover:bg-[#8b2635] hover:text-white"
									>
										<EyeOff size={14} strokeWidth={2} aria-hidden="true" />
										<span>Tarik</span>
									</button>
								</form>
							{:else if canPublishAction(article)}
								<form method="POST" action={publishAction(article)} use:enhance class="inline">
									<input type="hidden" name="id" value={article.id} />
									<input type="hidden" name="reason" value="Publikasi Artikel Panduan yang telah ditinjau" />
									<button
										type="submit"
										class="inline-flex h-9 items-center gap-1.5 rounded-lg border border-[#b8dbc8] bg-[#f0f9f4] px-3 text-xs font-semibold text-[#115e3c] shadow-2xs hover:border-[#176b49] hover:bg-[#176b49] hover:text-white"
									>
										<Eye size={14} strokeWidth={2} aria-hidden="true" />
										<span>Publikasi</span>
									</button>
								</form>
							{:else}
								<span
									title={!article.revision?.sources?.length ? "Perlu sumber rujukan sebelum publikasi" : "Perlu ditinjau sebelum publikasi"}
									class="inline-flex h-9 cursor-not-allowed items-center gap-1.5 rounded-lg border border-[#e2e8e4] bg-[#f5f8f6] px-3 text-xs font-semibold text-[#8fa097]"
								>
									<Eye size={14} strokeWidth={2} aria-hidden="true" />
									<span>Publikasi</span>
								</span>
							{/if}

							<!-- Archive Button -->
							{#if article.publication_status !== 'draft'}
								<form method="POST" action="?/deactivate" use:enhance class="inline">
									<input type="hidden" name="id" value={article.id} />
									<input type="hidden" name="reason" value="Mengarsipkan Artikel Panduan" />
									<button
										type="submit"
										title="Arsipkan artikel"
										aria-label="Arsipkan artikel"
										class="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-[#d6e0db] bg-white text-[#455c51] shadow-2xs hover:border-[#8b2635] hover:bg-[#fff5f6] hover:text-[#8b2635]"
									>
										<Archive size={15} strokeWidth={2} aria-hidden="true" />
									</button>
								</form>
							{/if}
						</div>
					</div>
				{/each}
			</div>
		{:else}
			<div class="empty py-12 text-center text-sm text-[#52655c]">Belum ada Artikel Panduan pada filter ini.</div>
		{/if}
		<TablePagination count={data.articles.total} page={data.articles.page} perPage={data.articles.page_size} onChange={updatePage} />
	</section>
</AdminShell>
