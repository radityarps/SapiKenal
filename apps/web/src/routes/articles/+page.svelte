<script lang="ts">
	import { enhance } from "$app/forms";
	import { goto } from "$app/navigation";
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
		{ value: "bali", label: "Bali" },
		{ value: "brahman", label: "Brahman" },
		{ value: "brangus", label: "Brangus" },
		{ value: "limusin", label: "Limusin" },
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

	let selected: any = null;

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
		<div><h2 class="m-0 text-lg font-bold text-[#263a30]">Artikel terdaftar</h2><p class="mt-1 text-sm text-[#66766f]">{data.articles.total ?? 0} artikel pada hasil filter.</p></div>
		<details class="panel w-full max-w-3xl p-4">
			<summary class="cursor-pointer font-semibold">Tambah Artikel Panduan</summary>
			<form class="mt-4 grid gap-3 sm:grid-cols-2" method="POST" action="?/create" use:enhance>
				<label>Kunci artikel<input name="article_key" pattern="[a-z0-9]+([_-][a-z0-9]+)*" maxlength="64" required placeholder="panduan-identifikasi" /></label>
				<label>Locale<select name="locale" required><option value="id-ID">Indonesia (id-ID)</option><option value="en-US">English (en-US)</option></select></label>
				<label>Kategori<select name="category" required>{#each categories.slice(1) as category}<option value={category.value}>{category.label}</option>{/each}</select></label>
				<label>Ikon<input name="icon" maxlength="16" value="📖" required /></label>
				<label>Urutan<input name="sort_order" type="number" min="0" max="100000" value="0" required /></label>
				<label>Judul<input name="title" maxlength="120" required /></label>
				<label class="sm:col-span-2">Ringkasan<textarea name="summary" maxlength="500" required></textarea></label>
				<label class="sm:col-span-2">Isi artikel<textarea name="body" maxlength="50000" required></textarea></label>
				<label class="sm:col-span-2">Sumber (satu URL per baris)<textarea name="sources" placeholder="https://sumber-tepercaya.example/artikel" required></textarea></label>
				<p class="m-0 text-xs font-normal leading-5 text-[#66766f] sm:col-span-2">Simpan sebagai draft. Review dan aktivasi dilakukan terpisah.</p>
				<button class="sm:col-span-2" type="submit">Simpan sebagai draft</button>
			</form>
		</details>
	</div>

	<div class="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
		<AdminFilterSelect label="Kategori" value={data.filters.category} items={categories} placeholder="Semua kategori" onChange={(value) => updateFilter("category", value)} />
		<AdminFilterSelect label="Locale" value={data.filters.locale} items={locales} placeholder="Semua locale" onChange={(value) => updateFilter("locale", value)} />
		<AdminFilterSelect label="Status publikasi" value={data.filters.publication_status} items={publicationStatuses} placeholder="Semua publikasi" onChange={(value) => updateFilter("publication_status", value)} />
		<AdminFilterSelect label="Status revisi terbaru" value={data.filters.revision_status} items={revisionStatuses} placeholder="Semua revisi terbaru" onChange={(value) => updateFilter("revision_status", value)} />
	</div>

	<section class="panel mt-3 p-0">
		{#if data.articles.items.length}
			<table class="table-fixed"><thead><tr><th>Artikel</th><th>Kategori</th><th>Locale</th><th>Status</th><th>Review dan pasangan</th><th class="text-right">Aksi</th></tr></thead><tbody>
				{#each data.articles.items as article}
					<tr>
						<td class="whitespace-normal"><strong class="block text-sm text-[#263a30]">{article.revision.icon} {article.revision.title}</strong><code class="text-xs text-[#829088]">{article.article_key} · v{article.revision.revision}</code><p class="m-0 mt-1 text-xs text-[#66766f]">{article.revision.summary}</p></td>
						<td class="whitespace-normal text-sm">{categoryLabel(article.revision.category)}</td>
						<td class="text-sm">{localeLabel(article.locale)}</td>
						<td class="whitespace-normal text-sm"><span class:!bg-[#f9e9ec]={article.publication_status === 'inactive'} class:!text-[#8b2635]={article.publication_status === 'inactive'} class="badge">Publik: {statusLabel(article.publication_status)}</span><span class="mt-1 block text-xs text-[#66766f]">Revisi terbaru: v{article.revision.revision} · {statusLabel(article.revision.status)}</span>{#if article.active_revision}<span class="block text-xs text-[#66766f]">Publik saat ini: v{article.active_revision.revision}</span>{/if}</td>
						<td class="whitespace-normal text-sm"><span>{reviewed(article) ? 'Sudah ditinjau' : 'Perlu ditinjau'}</span><span class="block text-xs text-[#66766f]">{pairingState(article)}</span></td>
						<td class="text-right"><button class="secondary" type="button" onclick={() => selected = article}>Kelola</button></td>
					</tr>
				{/each}
			</tbody></table>
		{:else}<div class="empty">Belum ada Artikel Panduan pada filter ini.</div>{/if}
		<TablePagination count={data.articles.total} page={data.articles.page} perPage={data.articles.page_size} onChange={updatePage} />
	</section>
</AdminShell>

{#if selected}
	<dialog open class="m-auto max-h-[calc(100dvh-2rem)] w-[min(92vw,46rem)] overflow-y-auto rounded-xl border border-[#dbe4df] bg-white p-0 text-[#17241f] shadow-[0_24px_70px_rgba(23,36,31,.22)]" aria-labelledby="article-detail-title">
		<div class="flex items-start justify-between gap-4 border-b border-[#e5ebe8] px-5 py-4"><div><p class="mb-1 text-xs font-bold uppercase tracking-wider text-[#6f7e76]">Artikel Panduan · {localeLabel(selected.locale)}</p><h2 id="article-detail-title" class="m-0 text-lg font-bold">{selected.revision.title}</h2><code class="text-xs text-[#66766f]">{selected.article_key}</code></div><button class="secondary" type="button" onclick={() => selected = null}>Tutup</button></div>
		<form class="grid gap-3 px-5 py-5 sm:grid-cols-2" method="POST" action="?/revise" use:enhance>
			<input type="hidden" name="id" value={selected.id} />
			<label>Kunci artikel<input value={selected.article_key} readonly aria-readonly="true" /></label>
			<label>Locale<input value={localeLabel(selected.locale)} readonly aria-readonly="true" /></label>
			<label>Kategori<select name="category" required>{#each categories.slice(1) as category}<option value={category.value} selected={selected.revision.category === category.value}>{category.label}</option>{/each}</select></label>
			<label>Ikon<input name="icon" value={selected.revision.icon} maxlength="16" required /></label>
			<label>Urutan<input name="sort_order" type="number" min="0" max="100000" value={selected.revision.sort_order} required /></label>
			<label>Judul<input name="title" value={selected.revision.title} maxlength="120" required /></label>
			<label class="sm:col-span-2">Ringkasan<textarea name="summary" maxlength="500" required>{selected.revision.summary}</textarea></label>
			<label class="sm:col-span-2">Isi artikel<textarea name="body" maxlength="50000" required>{selected.revision.body}</textarea></label>
			<label class="sm:col-span-2">Sumber (satu URL per baris)<textarea name="sources" required>{selected.revision.sources.join('\n')}</textarea></label>
			<p class="m-0 text-xs leading-5 text-[#66766f] sm:col-span-2">Menyimpan perubahan membuat revisi draft baru dan memerlukan review ulang.</p>
			<button class="sm:col-span-2" type="submit">Simpan revisi</button>
		</form>
		<form class="grid gap-3 border-t border-[#e5ebe8] px-5 py-4" method="POST" action="?/review" use:enhance>
			<input type="hidden" name="id" value={selected.id} />
			<label class="inline-flex items-center gap-2 text-sm font-normal"><input type="checkbox" name="content_reviewed" value="true" required /> Saya sudah meninjau isi dan sumber tersimpan</label>
			<button type="submit">Simpan review</button>
		</form>
		<div class="flex flex-wrap justify-end gap-2 border-t border-[#e5ebe8] px-5 py-4">
			<form method="POST" action="?/activate" use:enhance><input type="hidden" name="id" value={selected.id} /><input type="hidden" name="reason" value="Publikasi Artikel Panduan yang telah ditinjau" /><button type="submit">Aktifkan</button></form>
			<form method="POST" action="?/deactivate" use:enhance><input type="hidden" name="id" value={selected.id} /><input type="hidden" name="reason" value="Menarik Artikel Panduan dari publikasi" /><button class="danger" type="submit">Nonaktifkan</button></form>
		</div>
	</dialog>
{/if}
