<script lang="ts">
	import { enhance } from "$app/forms";
	import { ArrowLeft, BookOpen, Sparkles, AlertCircle } from "lucide-svelte";
	import AdminShell from "$lib/components/AdminShell.svelte";
	import BlockEditor from "$lib/components/BlockEditor.svelte";
	import BannerUploader from "$lib/components/BannerUploader.svelte";
	import { calculateNextSortOrder } from "$lib/sortOrder";

	export let data: {
		user: App.Locals["user"];
		existingBreedKeys: string[];
		categorySortOrders: Record<string, number[]>;
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
			is_breed_profile?: boolean;
			breed_key?: string;
			banner_image_url?: string | null;
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

	const breeds = [
		{ key: "pasundan", label: "Sapi Pasundan" },
		{ key: "bali", label: "Sapi Bali" },
		{ key: "po", label: "Sapi PO (Peranakan Ongole)" },
		{ key: "madura", label: "Sapi Madura" },
		{ key: "limusin", label: "Sapi Limusin" },
		{ key: "aceh", label: "Sapi Aceh" },
		{ key: "brahman", label: "Sapi Brahman" },
		{ key: "brangus", label: "Sapi Brangus" },
	];

	let isBreedProfile = form?.values?.is_breed_profile ?? false;
	let selectedBreedKey = form?.values?.breed_key ?? "";
	let titleInput = form?.values?.title ?? "";
	let summaryInput = form?.values?.summary ?? "";
	let bannerImageUrl = form?.values?.banner_image_url ?? "";
	let categoryInput = form?.values?.category ?? "app_usage";
	let sortOrderInput =
		form?.values?.sort_order ??
		calculateNextSortOrder(categoryInput, data.categorySortOrders?.[categoryInput] ?? []);
	let blockEditorRef: any;

	function updateSortOrderForCategory(cat: string) {
		sortOrderInput = calculateNextSortOrder(cat, data.categorySortOrders?.[cat] ?? []);
	}

	function handleTypeChange(type: "standard" | "breed_profile") {
		isBreedProfile = type === "breed_profile";
		if (isBreedProfile) {
			// Find first available breed that doesn't have a profile
			const firstAvailable = breeds.find((b) => !data.existingBreedKeys.includes(b.key));
			if (firstAvailable && !selectedBreedKey) {
				onSelectBreed(firstAvailable.key);
			} else if (selectedBreedKey) {
				onSelectBreed(selectedBreedKey);
			}
		} else {
			selectedBreedKey = "";
			categoryInput = "app_usage";
			updateSortOrderForCategory("app_usage");
		}
	}

	function onSelectBreed(key: string) {
		selectedBreedKey = key;
		categoryInput = key;
		const breed = breeds.find((b) => b.key === key);
		if (breed) {
			titleInput = `Profil ${breed.label}`;
			summaryInput = `Kelebihan, kekurangan, dan karakteristik visual ${breed.label} untuk informasi pendukung hasil identifikasi.`;
			updateSortOrderForCategory(key);
			blockEditorRef?.loadBreedProfileTemplate();
		}
	}

	$: isSelectedBreedTaken = Boolean(selectedBreedKey && data.existingBreedKeys.includes(selectedBreedKey));
</script>

<svelte:head><title>Tambah Artikel Panduan — SapiKenal Admin</title></svelte:head>
<AdminShell title="Tambah Artikel Panduan" eyebrow="Konten dan publikasi" active="/articles" user={data.user}>
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
		<p class="muted mt-3">Buat artikel panduan umum baru atau artikel profil resmi jenis sapi.</p>
	</section>

	{#if form?.error}
		<p class="error" role="alert">{form.error}</p>
	{/if}

	<!-- Pilihan Tipe Artikel (Segmented Toggle) -->
	<div class="mt-4 flex max-w-4xl rounded-xl border border-slate-300 bg-slate-100 p-1.5 shadow-2xs">
		<button
			type="button"
			class="group flex flex-1 items-center justify-center gap-2 rounded-lg py-2.5 text-xs font-bold transition-all {!isBreedProfile ? 'bg-white text-slate-950 shadow-2xs border border-slate-200/80' : 'bg-transparent text-slate-700 hover:bg-slate-200 hover:text-slate-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-900 focus-visible:bg-slate-200 focus-visible:text-slate-950'}"
			on:click={() => handleTypeChange("standard")}
		>
			<BookOpen size={15} class={!isBreedProfile ? "text-[#155e3d]" : "text-slate-600 transition-colors group-hover:text-slate-950 group-focus-visible:text-slate-950"} />
			Artikel Panduan Umum
		</button>
		<button
			type="button"
			class="group flex flex-1 items-center justify-center gap-2 rounded-lg py-2.5 text-xs font-bold transition-all {isBreedProfile ? 'bg-[#155e3d] text-white shadow-2xs border border-[#155e3d]' : 'bg-transparent text-slate-700 hover:bg-slate-200 hover:text-slate-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-900 focus-visible:bg-slate-200 focus-visible:text-slate-950'}"
			on:click={() => handleTypeChange("breed_profile")}
		>
			<Sparkles size={15} class={isBreedProfile ? "text-white" : "text-slate-600 transition-colors group-hover:text-slate-950 group-focus-visible:text-slate-950"} />
			Profil Resmi Jenis Sapi (1 Profil per Jenis)
		</button>
	</div>

	<section class="panel mt-4 max-w-4xl p-6 border border-slate-200 shadow-2xs rounded-xl bg-white">
		<form class="space-y-6" method="POST" action="?/create" use:enhance>
			<input type="hidden" name="is_breed_profile" value={isBreedProfile ? "true" : "false"} />
			<input type="hidden" name="breed_key" value={selectedBreedKey} />

			<!-- Konfigurasi Khusus Profil Jenis Sapi -->
			{#if isBreedProfile}
				<div class="rounded-xl border border-emerald-200 bg-emerald-50/50 p-4.5 space-y-3.5 shadow-2xs">
					<div class="flex items-center gap-2">
						<Sparkles size={16} class="text-emerald-800" />
						<span class="text-sm font-bold text-emerald-950">Pembuatan Profil Resmi Jenis Sapi</span>
					</div>
					<p class="text-xs text-emerald-900 leading-relaxed">
						Artikel ini akan langsung ditautkan secara kanonikal ke kartu hasil identifikasi jenis sapi di aplikasi mobile. Sistem menerapkan aturan <strong>hanya 1 profil per jenis sapi</strong>.
					</p>

					<div class="grid gap-4 sm:grid-cols-2">
						<label class="sm:col-span-2">
							<span class="font-bold text-slate-900">Pilih Rumpun Sapi Target</span>
							<select
								class="border border-emerald-300 bg-white font-semibold text-slate-900 shadow-2xs rounded-lg p-2.5 focus:border-emerald-700 focus:ring-2 focus:ring-emerald-700/20"
								value={selectedBreedKey}
								on:change={(e) => onSelectBreed(e.currentTarget.value)}
								required
							>
								<option value="" disabled>-- Pilih jenis sapi --</option>
								{#each breeds as breed}
									{@const alreadyExists = data.existingBreedKeys.includes(breed.key)}
									<option value={breed.key} disabled={alreadyExists}>
										{breed.label} {alreadyExists ? "(Sudah ada profil terdaftar)" : ""}
									</option>
								{/each}
							</select>
							<small class="text-[.75rem] text-slate-600 font-medium">
								Jenis sapi yang sudah memiliki artikel profil dinonaktifkan untuk mencegah duplikasi.
							</small>
						</label>
					</div>

					{#if isSelectedBreedTaken}
						<div class="flex items-start gap-2.5 rounded-xl border border-amber-300 bg-amber-50 p-3.5 text-xs text-amber-950">
							<AlertCircle size={16} class="shrink-0 mt-0.5 text-amber-700" />
							<div>
								<strong class="font-bold text-amber-950">Profil untuk jenis sapi ini sudah terdaftar.</strong>
								<p class="mt-0.5 text-amber-900">
									Untuk mengubah informasinya, silakan edit profil yang sudah ada dari daftar artikel.
								</p>
							</div>
						</div>
					{/if}
				</div>
			{/if}

			<!-- Atribut Umum -->
			<div class="grid gap-4 sm:grid-cols-2 pb-4 border-b border-slate-200">
				{#if !isBreedProfile}
					<label>
						<span class="font-semibold text-slate-900">Kategori</span>
						<select
							name="category"
							bind:value={categoryInput}
							on:change={() => updateSortOrderForCategory(categoryInput)}
							required
						>
							{#each categories as category}
								<option value={category.value}>
									{category.label}
								</option>
							{/each}
						</select>
						<small class="text-[.75rem] font-normal text-slate-600">Pilih panduan umum aplikasi atau kategori artikel.</small>
					</label>
				{:else}
					<input type="hidden" name="category" value={categoryInput} />
					<label>
						<span class="font-semibold text-slate-900">Kunci Artikel (Kanonikal)</span>
						<input value={selectedBreedKey ? `${selectedBreedKey}_1` : "-"} readonly class="bg-slate-50 border border-slate-200 text-slate-700 font-mono text-xs font-semibold" />
						<small class="text-[.75rem] font-normal text-slate-600">Otomatis diselaraskan dengan kontrak mobile.</small>
					</label>
				{/if}

				<label>
					<span class="font-semibold text-slate-900">Urutan Tampilan</span>
					<div class="flex items-center gap-2">
						<input
							name="sort_order"
							type="number"
							min="0"
							max="100000"
							required
							bind:value={sortOrderInput}
							class="flex-1"
						/>
						<button
							type="button"
							class="button secondary !min-h-10 !py-2 !px-3 text-xs font-semibold shrink-0 text-slate-700 border-slate-300 hover:bg-slate-100 hover:text-slate-900"
							title="Hitung ulang urutan otomatis berdasarkan kategori saat ini"
							on:click={() => updateSortOrderForCategory(categoryInput)}
						>
							Otomatis
						</button>
					</div>
					<small class="text-[.75rem] font-normal text-slate-600">
						Urutan otomatis terisi kelipatan 100 per rumpun (atau 10 untuk panduan umum). Anda tetap dapat mengubah angka ini manual.
					</small>
				</label>

				<label class="sm:col-span-2">
					<span class="font-semibold text-slate-900">
						Sumber Rujukan (satu URL per baris)
						<span class="text-xs font-normal text-slate-500">(Opsional)</span>
					</span>
					<textarea
						name="sources"
						placeholder="https://sumber-tepercaya.example/pedoman (kosongkan jika tidak ada)"
					>{form?.values?.sources ?? ""}</textarea>
					<small class="text-[.75rem] font-normal text-slate-600">Opsional. Masukkan tautan referensi berawalan http:// atau https:// jika ada.</small>
				</label>
			</div>

			<!-- Banner Gambar Artikel -->
			<div class="pb-4 border-b border-slate-200">
				<BannerUploader bind:bannerImageUrl />
			</div>

			<!-- Judul & Ringkasan -->
			<div class="grid gap-4">
				<label>
					<span class="font-semibold text-slate-900">Judul Artikel</span>
					<input
						name="title"
						bind:value={titleInput}
						maxlength="120"
						placeholder="Contoh: Karakteristik dan Ciri Fisik Sapi Pasundan"
						required
					/>
				</label>

				<label>
					<span class="font-semibold text-slate-900">Ringkasan Singkat</span>
					<textarea
						name="summary"
						maxlength="500"
						placeholder="Ringkasan singkat mengenai isi artikel..."
						required
						bind:value={summaryInput}
					></textarea>
				</label>

				<!-- Block-based Notion Editor -->
				<div>
					<span class="block text-xs font-bold text-slate-900 mb-2">Isi Konten Artikel</span>
					<BlockEditor
						bind:this={blockEditorRef}
						isBreedProfile={isBreedProfile}
						initialBody={form?.values?.body ?? ""}
					/>
				</div>
			</div>

			<!-- Footer Buttons -->
			<div class="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 pt-5">
				<p class="m-0 text-xs font-medium text-slate-500">
					{isBreedProfile ? "Kunci profil disesuaikan dengan standar kanonikal identifikasi jenis sapi." : "Kunci artikel dibuat otomatis dari judul."}
				</p>
				<div class="flex items-center gap-2.5">
					<a
						href="/articles"
						class="button secondary !min-h-10 font-bold text-slate-800 border-slate-300 hover:bg-slate-900 hover:text-white hover:border-slate-900 focus-visible:bg-slate-900 focus-visible:text-white focus-visible:ring-2 focus-visible:ring-slate-900 focus-visible:outline-none transition-all"
					>
						Batal
					</a>
					<button
						type="submit"
						name="action_type"
						value="draft"
						class="button secondary !min-h-10 font-bold text-slate-800 border-slate-300 hover:bg-slate-900 hover:text-white hover:border-slate-900 focus-visible:bg-slate-900 focus-visible:text-white focus-visible:ring-2 focus-visible:ring-slate-900 focus-visible:outline-none transition-all"
						disabled={isBreedProfile && isSelectedBreedTaken}
					>
						Simpan Draft
					</button>
					<button
						type="submit"
						name="action_type"
						value="publish"
						class="button !min-h-10 font-bold bg-[#155e3d] hover:bg-[#0f462d] text-white shadow-2xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#155e3d] focus-visible:ring-offset-2 transition-all"
						disabled={isBreedProfile && isSelectedBreedTaken}
					>
						Simpan & Publikasikan
					</button>
				</div>
			</div>
		</form>
	</section>
</AdminShell>
