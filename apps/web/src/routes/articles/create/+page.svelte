<script lang="ts">
	import { enhance } from "$app/forms";
	import { ArrowLeft } from "lucide-svelte";
	import AdminShell from "$lib/components/AdminShell.svelte";

	export let data: {
		user: App.Locals["user"];
	};
	export let form: {
		error?: string;
		values?: {
			category?: string;
			sort_order?: number;
			sources?: string;
			title?: string;
			summary?: string;
			body?: string;
			article_key?: string;
		};
	} | null;

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
</script>

<svelte:head><title>Tambah Artikel Panduan — SapiKenal Admin</title></svelte:head>
<AdminShell title="Tambah Artikel Panduan" eyebrow="Konten dan publikasi" active="/articles" user={data.user}>
	<section class="page-intro">
		<div class="flex items-center gap-3">
			<a class="button secondary flex items-center gap-1.5 !min-h-9 !py-1.5 !px-3 text-xs" href="/articles">
				<ArrowLeft size={15} aria-hidden="true" />
				Kembali ke daftar artikel
			</a>
		</div>
		<p class="muted mt-3">Buat artikel panduan baru untuk aplikasi atau profil jenis sapi.</p>
	</section>

	{#if form?.error}
		<p class="error" role="alert">{form.error}</p>
	{/if}

	<section class="panel mt-4 max-w-4xl p-6">
		<form class="space-y-6" method="POST" action="?/create" use:enhance>
			<!-- Atribut Umum -->
			<div class="grid gap-4 sm:grid-cols-2 pb-4 border-b border-[#e0e7e3]">
				<label>
					<span>Kategori</span>
					<select name="category" required>
						{#each categories as category}
							<option value={category.value} selected={(form?.values?.category ?? "app_usage") === category.value}>
								{category.label}
							</option>
						{/each}
					</select>
					<small class="text-[.72rem] font-normal text-[#66766f]">Pilih panduan umum aplikasi atau jenis sapi.</small>
				</label>

				<label>
					<span>Urutan</span>
					<input
						name="sort_order"
						type="number"
						min="0"
						max="100000"
						required
						value={form?.values?.sort_order ?? 0}
					/>
					<small class="text-[.72rem] font-normal text-[#66766f]">Nomor urut tampilan artikel (angka lebih kecil muncul lebih awal).</small>
				</label>

				<label class="sm:col-span-2">
					<span>Sumber Rujukan (satu URL per baris)</span>
					<textarea
						name="sources"
						placeholder="https://sumber-tepercaya.example/artikel"
						required
					>{form?.values?.sources ?? ""}</textarea>
					<small class="text-[.72rem] font-normal text-[#66766f]">Masukkan minimal satu tautan referensi valid berawalan http:// atau https://.</small>
				</label>
			</div>

			<!-- Konten Artikel -->
			<div class="grid gap-4">
				<label>
					<span>Judul</span>
					<input
						name="title"
						value={form?.values?.title ?? ""}
						maxlength="120"
						placeholder="Contoh: Karakteristik dan Ciri Fisik Sapi Bali"
						required
					/>
				</label>

				<label>
					<span>Ringkasan</span>
					<textarea
						name="summary"
						maxlength="500"
						placeholder="Ringkasan singkat mengenai isi artikel..."
						required
					>{form?.values?.summary ?? ""}</textarea>
				</label>

				<label>
					<span>Isi Artikel</span>
					<textarea
						name="body"
						class="min-h-48"
						maxlength="50000"
						placeholder="Tuliskan isi lengkap artikel..."
						required
					>{form?.values?.body ?? ""}</textarea>
				</label>
			</div>

			<!-- Opsi Publikasi -->
			<div class="rounded-lg border border-[#e0e7e3] bg-[#f8faf8] p-4">
				<label class="flex items-start gap-3 cursor-pointer">
					<input
						type="checkbox"
						name="publish_immediately"
						value="true"
						class="mt-1 h-4 w-4 rounded border-[#b2c2b9] text-[#176b49] focus:ring-[#176b49]"
						checked
					/>
					<div>
						<span class="text-sm font-semibold text-[#17241f]">Langsung publikasikan artikel (aktif)</span>
						<p class="mt-0.5 text-xs text-[#66766f]">
							Jika dicentang atau menekan "Simpan & Publikasikan", artikel akan otomatis disetujui (review) dan diaktifkan sehingga langsung tersinkronisasi ke aplikasi mobile.
						</p>
					</div>
				</label>
			</div>

			<!-- Footer Buttons -->
			<div class="mt-2 flex flex-wrap items-center justify-between gap-3 border-t border-[#e5ebe8] pt-4">
				<p class="m-0 text-xs font-normal text-[#66766f]">
					Kunci artikel dibuat otomatis di belakang layar dari judul artikel.
				</p>
				<div class="flex items-center gap-2">
					<a href="/articles" class="button secondary">Batal</a>
					<button type="submit" name="action_type" value="draft" class="secondary">Simpan Draft</button>
					<button type="submit" name="action_type" value="publish">Simpan & Publikasikan</button>
				</div>
			</div>
		</form>
	</section>
</AdminShell>
