<script lang="ts">
	import { Image, UploadCloud, Trash2, Loader2, AlertCircle } from "lucide-svelte";

	export let bannerImageUrl: string | null = null;
	export let disabled: boolean = false;

	let fileInput: HTMLInputElement;
	let isUploading = false;
	let errorMessage = "";
	let isDragOver = false;

	async function handleFileSelected(file: File) {
		errorMessage = "";
		const allowedTypes = ["image/jpeg", "image/png", "image/webp"];
		if (!allowedTypes.includes(file.type)) {
			errorMessage = "Format berkas tidak didukung. Gunakan format JPG, PNG, atau WebP.";
			return;
		}

		const maxSize = 5 * 1024 * 1024; // 5 MB
		if (file.size > maxSize) {
			errorMessage = "Ukuran berkas melebihi batas maksimal 5 MB.";
			return;
		}

		isUploading = true;
		const formData = new FormData();
		formData.append("file", file);

		try {
			const res = await fetch("/api/articles/upload-banner", {
				method: "POST",
				body: formData,
			});
			const data = await res.json();
			if (!res.ok) {
				errorMessage = data.error || "Gagal mengunggah banner gambar.";
			} else if (data.banner_image_url) {
				bannerImageUrl = data.banner_image_url;
			}
		} catch (err) {
			errorMessage = err instanceof Error ? err.message : "Terjadi kesalahan saat mengunggah berkas.";
		} finally {
			isUploading = false;
			if (fileInput) fileInput.value = "";
		}
	}

	function onInputChange(e: Event) {
		const target = e.target as HTMLInputElement;
		if (target.files && target.files.length > 0) {
			handleFileSelected(target.files[0]);
		}
	}

	function handleDrop(e: DragEvent) {
		e.preventDefault();
		isDragOver = false;
		if (disabled || isUploading) return;
		if (e.dataTransfer?.files && e.dataTransfer.files.length > 0) {
			handleFileSelected(e.dataTransfer.files[0]);
		}
	}

	function removeBanner() {
		bannerImageUrl = "";
		errorMessage = "";
		if (fileInput) fileInput.value = "";
	}
</script>

<div class="space-y-2">
	<!-- Hidden input for standard SvelteKit form action -->
	<input type="hidden" name="banner_image_url" value={bannerImageUrl ?? ""} />

	<!-- Hidden native file input -->
	<input
		type="file"
		accept="image/jpeg,image/png,image/webp"
		class="hidden"
		bind:this={fileInput}
		on:change={onInputChange}
		{disabled}
	/>

	<div class="flex items-center justify-between">
		<div>
			<span class="font-semibold text-slate-900 text-sm">Banner Gambar Artikel</span>
			<span class="text-xs font-normal text-slate-500 ml-1">(Opsional)</span>
		</div>
		{#if bannerImageUrl}
			<span class="text-xs font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
				Banner aktif
			</span>
		{/if}
	</div>

	{#if bannerImageUrl}
		<!-- Banner Preview Card -->
		<div class="relative overflow-hidden rounded-xl border border-slate-200 bg-slate-50 shadow-2xs group">
			<div class="w-full aspect-[21/9] sm:aspect-[24/9] max-h-56 overflow-hidden bg-slate-900 flex items-center justify-center">
				<img
					src={bannerImageUrl}
					alt="Pratinjau Banner"
					class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-[1.01]"
				/>
			</div>

			<!-- Action Overlay Bar -->
			<div class="p-3 bg-white border-t border-slate-200 flex items-center justify-between gap-3">
				<div class="flex items-center gap-2 text-xs text-slate-600 truncate">
					<Image size={15} class="text-slate-500 shrink-0" />
					<span class="truncate font-mono text-[.75rem]">{bannerImageUrl}</span>
				</div>
				<div class="flex items-center gap-2 shrink-0">
					<button
						type="button"
						class="button secondary !min-h-8 !py-1 !px-3 text-xs font-semibold text-slate-700 border-slate-300 hover:bg-slate-100 hover:text-slate-900"
						on:click={() => fileInput.click()}
						disabled={disabled || isUploading}
					>
						Ganti Gambar
					</button>
					<button
						type="button"
						class="button !min-h-8 !py-1 !px-2.5 text-xs font-semibold text-rose-700 bg-rose-50 border border-rose-200 hover:bg-rose-100 hover:text-rose-900 focus-visible:ring-rose-400"
						on:click={removeBanner}
						disabled={disabled || isUploading}
						title="Hapus banner gambar ini"
					>
						<Trash2 size={14} class="shrink-0" />
						<span class="hidden sm:inline ml-1">Hapus</span>
					</button>
				</div>
			</div>
		</div>
	{:else}
		<!-- Upload Dropzone -->
		<div
			class="relative flex flex-col items-center justify-center p-6 border-2 border-dashed rounded-xl transition-all cursor-pointer {isDragOver ? 'border-primary-500 bg-primary-50/40' : 'border-slate-300 bg-slate-50/60 hover:bg-slate-50 hover:border-slate-400'}"
			on:dragover|preventDefault={() => { if (!disabled && !isUploading) isDragOver = true; }}
			on:dragleave={() => { isDragOver = false; }}
			on:drop={handleDrop}
			on:click={() => { if (!disabled && !isUploading) fileInput.click(); }}
			role="button"
			tabindex="0"
			on:keydown={(e) => { if ((e.key === "Enter" || e.key === " ") && !disabled && !isUploading) { e.preventDefault(); fileInput.click(); } }}
		>
			{#if isUploading}
				<div class="flex flex-col items-center gap-2 py-4">
					<Loader2 size={28} class="animate-spin text-slate-700" />
					<p class="text-xs font-medium text-slate-700">Mengunggah banner gambar...</p>
				</div>
			{:else}
				<div class="flex flex-col items-center gap-2 text-center py-2">
					<div class="w-10 h-10 rounded-full bg-white shadow-2xs border border-slate-200 flex items-center justify-center text-slate-700">
						<UploadCloud size={20} />
					</div>
					<p class="text-xs font-semibold text-slate-900">
						Klik untuk memilih gambar atau seret berkas ke sini
					</p>
					<p class="text-[.75rem] text-slate-500 max-w-sm">
						Format JPG, PNG, atau WebP (maks. 5 MB). Banner akan muncul pada card dan halaman detail artikel di aplikasi mobile.
					</p>
				</div>
			{/if}
		</div>
	{/if}

	{#if errorMessage}
		<div class="flex items-center gap-2 text-xs text-rose-700 bg-rose-50 border border-rose-200 p-2.5 rounded-lg" role="alert">
			<AlertCircle size={15} class="shrink-0 text-rose-600" />
			<span>{errorMessage}</span>
		</div>
	{/if}
</div>
