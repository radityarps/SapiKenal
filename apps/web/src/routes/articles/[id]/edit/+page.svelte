<script lang="ts">
	import { enhance } from "$app/forms";
	import { ArrowLeft } from "lucide-svelte";
	import AdminShell from "$lib/components/AdminShell.svelte";

	export let data: {
		user: App.Locals["user"];
		article: any;
	};
	export let form: { error?: string } | null;

	const categories = [
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
	const localeLabel = (locale: string) =>
		({ "id-ID": "Indonesia (id-ID)", "en-US": "English (en-US)" })[locale] ?? locale;

	const a = data.article;
</script>

<svelte:head><title>Edit Artikel — {a.revision.title} — SapiKenal Admin</title></svelte:head>
<AdminShell
	title="Edit Artikel Panduan"
	eyebrow="Konten dan publikasi"
	active="/articles"
	user={data.user}
>
	<section class="page-intro">
		<div class="flex items-center gap-3">
			<a class="button secondary flex items-center gap-1.5 !min-h-9 !py-1.5 !px-3 text-xs" href="/articles">
				<ArrowLeft size={15} aria-hidden="true" />
				Kembali ke daftar artikel
			</a>
		</div>
		<p class="muted mt-3">
			Mengedit artikel <strong>{a.revision.title}</strong> (<code>{a.article_key}</code>) · {localeLabel(a.locale)}.
			Menyimpan perubahan akan membuat revisi draft baru yang memerlukan review dan aktivasi ulang.
		</p>
	</section>

	{#if form?.error}
		<p class="error" role="alert">{form.error}</p>
	{/if}

	<section class="panel mt-4 max-w-4xl p-6">
		<form class="space-y-5" method="POST" action="?/revise" use:enhance>
			<div class="grid gap-4 sm:grid-cols-2 pb-4 border-b border-[#e0e7e3]">
				<label>
					<span>Kunci artikel</span>
					<input value={a.article_key} readonly aria-readonly="true" class="opacity-60" />
					<small class="text-[.72rem] font-normal text-[#66766f]">Kunci tidak dapat diubah setelah artikel dibuat.</small>
				</label>
				<label>
					<span>Locale</span>
					<input value={localeLabel(a.locale)} readonly aria-readonly="true" class="opacity-60" />
				</label>
				<label>
					<span>Kategori</span>
					<select name="category" required>
						{#each categories as category}
							<option value={category.value} selected={a.revision.category === category.value}>{category.label}</option>
						{/each}
					</select>
				</label>
				<label>
					<span>Urutan</span>
					<input name="sort_order" type="number" min="0" max="100000" value={a.revision.sort_order} required />
					<small class="text-[.72rem] font-normal text-[#66766f]">Angka lebih kecil muncul lebih awal.</small>
				</label>
				<label class="sm:col-span-2">
					<span>Sumber Rujukan (satu URL per baris)</span>
					<textarea name="sources" placeholder="https://sumber-tepercaya.example/artikel">{a.revision.sources.join("\n")}</textarea>
					<small class="text-[.72rem] font-normal text-[#66766f]">Minimal satu tautan referensi valid.</small>
				</label>
			</div>

			<label>
				<span>Judul</span>
				<input name="title" value={a.revision.title} maxlength="120" required />
			</label>
			<label>
				<span>Ringkasan</span>
				<textarea name="summary" maxlength="500" required>{a.revision.summary}</textarea>
			</label>
			<label>
				<span>Isi Artikel</span>
				<textarea name="body" maxlength="50000" class="min-h-64" required>{a.revision.body}</textarea>
			</label>

			<div class="notice !py-2 !px-3 text-xs">
				Menyimpan akan membuat <strong>revisi draft baru (v{a.revision.revision + 1})</strong>. Kembali ke halaman artikel untuk me-review dan mengaktifkannya.
			</div>

			<div class="flex flex-wrap items-center justify-between gap-3 border-t border-[#e5ebe8] pt-4">
				<a href="/articles" class="button secondary">Batal</a>
				<button type="submit">Simpan Revisi</button>
			</div>
		</form>
	</section>
</AdminShell>
