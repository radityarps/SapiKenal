<script lang="ts">
	import { enhance } from "$app/forms";
	import { ArrowLeft, Sparkles } from "lucide-svelte";
	import AdminShell from "$lib/components/AdminShell.svelte";
	import BlockEditor from "$lib/components/BlockEditor.svelte";
	import BannerUploader from "$lib/components/BannerUploader.svelte";

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
	const a = data.article;
	let bannerImageUrl = a.revision.banner_image_url || "";
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
			<a
				class="button secondary flex items-center gap-1.5 !min-h-9 !py-1.5 !px-3 text-xs font-bold text-slate-800 border-slate-300 hover:bg-slate-900 hover:text-white hover:border-slate-900 focus-visible:bg-slate-900 focus-visible:text-white focus-visible:ring-2 focus-visible:ring-slate-900 focus-visible:outline-none transition-all"
				href="/articles"
			>
				<ArrowLeft size={15} aria-hidden="true" />
				Kembali ke daftar artikel
			</a>
		</div>
		<p class="muted mt-3">
			Mengedit artikel <strong>{a.revision.title}</strong> (<code>{a.article_key}</code>).
			Menyimpan perubahan akan membuat revisi draft baru yang dapat langsung dipublikasikan dari halaman daftar artikel.
		</p>
	</section>

	{#if form?.error}
		<p class="error" role="alert">{form.error}</p>
	{/if}

	<section class="panel mt-4 max-w-4xl p-6 border border-slate-200 shadow-2xs rounded-xl bg-white">
		<form class="space-y-5" method="POST" action="?/revise" use:enhance>
			{#if a.is_breed_profile}
				<div class="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-xs text-emerald-950 font-bold shadow-2xs">
					<Sparkles size={16} class="text-emerald-800" />
					<span>Artikel ini adalah Profil Resmi Jenis Sapi ({a.breed_key?.toUpperCase()}).</span>
				</div>
			{/if}

			<div class="grid gap-4 sm:grid-cols-2 pb-4 border-b border-slate-200">
				<label class="sm:col-span-2">
					<span class="font-semibold text-slate-900">Kunci artikel</span>
					<input value={a.article_key} readonly aria-readonly="true" class="bg-slate-50 border border-slate-200 text-slate-700 font-mono text-xs font-semibold" />
					<small class="text-[.75rem] font-normal text-slate-600">Kunci tidak dapat diubah setelah artikel dibuat.</small>
				</label>
				<label>
					<span class="font-semibold text-slate-900">Kategori</span>
					<select name="category" required>
						{#each categories as category}
							<option value={category.value} selected={a.revision.category === category.value}>{category.label}</option>
						{/each}
					</select>
				</label>
				<label>
					<span class="font-semibold text-slate-900">Urutan</span>
					<input name="sort_order" type="number" min="0" max="100000" value={a.revision.sort_order} required />
					<small class="text-[.75rem] font-normal text-slate-600">Angka lebih kecil muncul lebih awal.</small>
				</label>
				<label class="sm:col-span-2">
					<span class="font-semibold text-slate-900">
						Sumber Rujukan (satu URL per baris)
						<span class="text-xs font-normal text-slate-500">(Opsional)</span>
					</span>
					<textarea name="sources" placeholder="https://sumber-tepercaya.example/artikel (kosongkan jika tidak ada)">{a.revision.sources.join("\n")}</textarea>
					<small class="text-[.75rem] font-normal text-slate-600">Opsional. Masukkan tautan referensi berawalan http:// atau https:// jika ada.</small>
				</label>
			</div>

			<!-- Banner Gambar Artikel -->
			<div class="pb-4 border-b border-slate-200">
				<BannerUploader bind:bannerImageUrl />
			</div>

			<label>
				<span class="font-semibold text-slate-900">Judul</span>
				<input name="title" value={a.revision.title} maxlength="120" required />
			</label>
			<label>
				<span class="font-semibold text-slate-900">Ringkasan</span>
				<textarea name="summary" maxlength="500" required>{a.revision.summary}</textarea>
			</label>

			<!-- Notion-like Block Editor -->
			<div>
				<span class="block text-xs font-bold text-slate-900 mb-2">Isi Konten Artikel</span>
				<BlockEditor
					initialBlocks={a.revision.content_blocks || []}
					initialBody={a.revision.body || ""}
					isBreedProfile={a.is_breed_profile}
				/>
			</div>

			<div class="rounded-xl border border-slate-200 bg-slate-50/90 p-4 text-xs font-medium text-slate-800 shadow-2xs leading-relaxed">
				Menyimpan akan membuat <strong>revisi draft baru (v{a.revision.revision + 1})</strong>. Kembali ke halaman artikel untuk mengaktifkan/mempublikasikannya.
			</div>

			<div class="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 pt-5">
				<a
					href="/articles"
					class="button secondary !min-h-10 font-bold text-slate-800 border-slate-300 hover:bg-slate-900 hover:text-white hover:border-slate-900 focus-visible:bg-slate-900 focus-visible:text-white focus-visible:ring-2 focus-visible:ring-slate-900 focus-visible:outline-none transition-all"
				>
					Batal
				</a>
				<button
					type="submit"
					class="button !min-h-10 font-bold bg-[#155e3d] hover:bg-[#0f462d] text-white shadow-2xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#155e3d] focus-visible:ring-offset-2 transition-all"
				>
					Simpan Revisi
				</button>
			</div>
		</form>
	</section>
</AdminShell>
