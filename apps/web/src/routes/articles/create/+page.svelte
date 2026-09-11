<script lang="ts">
	import { enhance } from "$app/forms";
	import { ArrowLeft, Check, Globe } from "lucide-svelte";
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
			title_id?: string;
			summary_id?: string;
			body_id?: string;
			title_en?: string;
			summary_en?: string;
			body_en?: string;
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

	let activeLocale = "id-ID";

	let title_id = form?.values?.title_id ?? "";
	let summary_id = form?.values?.summary_id ?? "";
	let body_id = form?.values?.body_id ?? "";

	let title_en = form?.values?.title_en ?? "";
	let summary_en = form?.values?.summary_en ?? "";
	let body_en = form?.values?.body_en ?? "";

	$: isIdComplete = Boolean(title_id.trim() && summary_id.trim() && body_id.trim());
	$: isEnFilled = Boolean(title_en.trim() || summary_en.trim() || body_en.trim());
	$: isEnComplete = Boolean(title_en.trim() && summary_en.trim() && body_en.trim());
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
		<p class="muted mt-3">Buat artikel panduan baru untuk aplikasi atau profil jenis sapi. Anda dapat menulis konten dalam Bahasa Indonesia (wajib) dan versi Bahasa Inggris (opsional) dalam satu formulir ini.</p>
	</section>

	{#if form?.error}
		<p class="error" role="alert">{form.error}</p>
	{/if}

	<section class="panel mt-4 max-w-4xl p-6">
		<form class="space-y-6" method="POST" action="?/create" use:enhance>
			<!-- Atribut Umum (Shared across locales) -->
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

			<!-- Locale Switcher & Content Section -->
			<div>
				<div class="mb-3">
					<h3 class="text-sm font-bold text-[#17241f] m-0">Konten & Terjemahan Artikel</h3>
					<p class="text-xs text-[#66766f] mt-0.5 mb-3">
						Gunakan tab di bawah untuk beralih bahasa. Kunci artikel dibuat secara otomatis di belakang layar.
					</p>

					<!-- Tab Switcher -->
					<div class="flex items-center gap-2 border-b border-[#e5ebe8] pb-3">
						<button
							type="button"
							class="inline-flex items-center gap-1.5 rounded-lg px-3.5 py-2 text-xs font-semibold transition-all {activeLocale === 'id-ID' ? 'bg-[#176b49] text-white shadow-xs' : 'bg-[#e8f2ed] text-[#145c3e] hover:bg-[#d8e9e0]'}"
							on:click={() => activeLocale = 'id-ID'}
						>
							<Globe size={14} />
							<span>Bahasa Indonesia (ID)</span>
							<span class="rounded px-1.5 py-0.5 text-[10px] font-medium {activeLocale === 'id-ID' ? 'bg-white/20 text-white' : 'bg-[#176b49]/10 text-[#176b49]'}">Wajib</span>
							{#if isIdComplete}
								<Check size={13} class="text-[#a7f3d0]" />
							{/if}
						</button>

						<button
							type="button"
							class="inline-flex items-center gap-1.5 rounded-lg px-3.5 py-2 text-xs font-semibold transition-all {activeLocale === 'en-US' ? 'bg-[#176b49] text-white shadow-xs' : 'bg-[#e8f2ed] text-[#145c3e] hover:bg-[#d8e9e0]'}"
							on:click={() => activeLocale = 'en-US'}
						>
							<Globe size={14} />
							<span>English (EN)</span>
							<span class="rounded px-1.5 py-0.5 text-[10px] font-medium {activeLocale === 'en-US' ? 'bg-white/20 text-white' : 'bg-[#176b49]/10 text-[#176b49]'}">Opsional</span>
							{#if isEnComplete}
								<Check size={13} class="text-[#a7f3d0]" />
							{:else if isEnFilled}
								<span class="text-[10px] text-amber-600 font-medium">(Sebagian)</span>
							{/if}
						</button>
					</div>
				</div>

				<!-- Panel Bahasa Indonesia (ID) -->
				<div class="grid gap-4 {activeLocale === 'id-ID' ? 'block' : 'hidden'}">
					<div class="notice !mt-0 !py-2 !px-3 text-xs">
						Mengedit versi <strong>Bahasa Indonesia</strong> (Bahasa utama yang wajib diisi).
					</div>

					<label>
						<span>Judul (ID)</span>
						<input
							name="title_id"
							bind:value={title_id}
							maxlength="120"
							placeholder="Contoh: Karakteristik dan Ciri Fisik Sapi Bali"
						/>
					</label>

					<label>
						<span>Ringkasan (ID)</span>
						<textarea
							name="summary_id"
							bind:value={summary_id}
							maxlength="500"
							placeholder="Ringkasan singkat mengenai isi artikel dalam bahasa Indonesia..."
						></textarea>
					</label>

					<label>
						<span>Isi Artikel (ID)</span>
						<textarea
							name="body_id"
							bind:value={body_id}
							class="min-h-48"
							maxlength="50000"
							placeholder="Tuliskan isi lengkap artikel dalam bahasa Indonesia..."
						></textarea>
					</label>
				</div>

				<!-- Panel English (EN) -->
				<div class="grid gap-4 {activeLocale === 'en-US' ? 'block' : 'hidden'}">
					<div class="notice !mt-0 !py-2 !px-3 text-xs bg-[#f8f9fa] border-[#e9ecef] text-[#495057]">
						Mengedit terjemahan <strong>English</strong> (Opsional. Jika diisi, sistem otomatis membuat kedua versi ID & EN dengan kunci yang sama).
					</div>

					<label>
						<span>Title (EN)</span>
						<input
							name="title_en"
							bind:value={title_en}
							maxlength="120"
							placeholder="e.g. Physical Characteristics of Bali Cattle"
						/>
					</label>

					<label>
						<span>Summary (EN)</span>
						<textarea
							name="summary_en"
							bind:value={summary_en}
							maxlength="500"
							placeholder="Brief overview explaining what readers will learn..."
						></textarea>
					</label>

					<label>
						<span>Body Content (EN)</span>
						<textarea
							name="body_en"
							bind:value={body_en}
							class="min-h-48"
							maxlength="50000"
							placeholder="Full guide content in English..."
						></textarea>
					</label>
				</div>
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
