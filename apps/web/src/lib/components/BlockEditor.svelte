<script context="module" lang="ts">
	export type BlockType = "paragraph" | "heading" | "bullet_list" | "callout" | "disclaimer";

	export interface ContentBlock {
		id: string;
		type: BlockType;
		content: string;
		items: string[];
	}
</script>

<script lang="ts">
	import {
		Plus,
		Trash2,
		ArrowUp,
		ArrowDown,
		Type,
		Heading2,
		List,
		AlertCircle,
		ShieldAlert,
		Sparkles,
		Eye,
		Edit3
	} from "lucide-svelte";

	export let initialBlocks: ContentBlock[] = [];
	export let initialBody: string = "";
	export let isBreedProfile: boolean = false;

	let viewMode: "editor" | "preview" = "editor";

	function createId(): string {
		return "block-" + Math.random().toString(36).substring(2, 9);
	}

	function parseBodyToBlocks(raw: string): ContentBlock[] {
		if (!raw.trim()) return [];
		const lines = raw.split("\n");
		const parsed: ContentBlock[] = [];
		let currentBulletItems: string[] = [];

		function flushBullets() {
			if (currentBulletItems.length > 0) {
				parsed.push({
					id: createId(),
					type: "bullet_list",
					content: "",
					items: [...currentBulletItems]
				});
				currentBulletItems = [];
			}
		}

		for (const line of lines) {
			const trimmed = line.trim();
			if (!trimmed) {
				flushBullets();
				continue;
			}

			if (trimmed.startsWith("•") || trimmed.startsWith("-") || trimmed.startsWith("*")) {
				const item = trimmed.replace(/^[•\-*]\s*/, "");
				if (item) currentBulletItems.push(item);
			} else if (trimmed.startsWith("## ") || trimmed.startsWith("### ")) {
				flushBullets();
				parsed.push({
					id: createId(),
					type: "heading",
					content: trimmed.replace(/^#{2,3}\s*/, ""),
					items: []
				});
			} else if (trimmed.startsWith("> ")) {
				flushBullets();
				parsed.push({
					id: createId(),
					type: "callout",
					content: trimmed.replace(/^>\s*/, ""),
					items: []
				});
			} else if (
				trimmed.toLowerCase().includes("bukan bukti silsilah") ||
				trimmed.toLowerCase().includes("rekomendasi mutlak")
			) {
				flushBullets();
				parsed.push({
					id: createId(),
					type: "disclaimer",
					content: trimmed,
					items: []
				});
			} else {
				flushBullets();
				parsed.push({
					id: createId(),
					type: "paragraph",
					content: trimmed,
					items: []
				});
			}
		}
		flushBullets();
		return parsed;
	}

	function getInitialBlocks(): ContentBlock[] {
		if (initialBlocks && initialBlocks.length > 0) {
			return initialBlocks.map((b) => ({
				id: b.id || createId(),
				type: b.type || "paragraph",
				content: b.content || "",
				items: Array.isArray(b.items) ? [...b.items] : []
			}));
		}
		if (initialBody.trim()) {
			return parseBodyToBlocks(initialBody);
		}
		if (isBreedProfile) {
			return getBreedProfileTemplate();
		}
		return [
			{
				id: createId(),
				type: "paragraph",
				content: "",
				items: []
			}
		];
	}

	function getBreedProfileTemplate(): ContentBlock[] {
		return [
			{
				id: createId(),
				type: "heading",
				content: "Ringkasan Profil",
				items: []
			},
			{
				id: createId(),
				type: "paragraph",
				content: "Tuliskan ciri fisik utama, proporsi tubuh, dan karakteristik visual penting...",
				items: []
			},
			{
				id: createId(),
				type: "heading",
				content: "Kelebihan",
				items: []
			},
			{
				id: createId(),
				type: "bullet_list",
				content: "",
				items: [
					"Adaptasi tinggi terhadap lingkungan setempat",
					"Ciri visual khas yang mudah dikenali"
				]
			},
			{
				id: createId(),
				type: "heading",
				content: "Kekurangan",
				items: []
			},
			{
				id: createId(),
				type: "bullet_list",
				content: "",
				items: [
					"Variasi warna atau bentuk dapat terjadi antar individu"
				]
			},
			{
				id: createId(),
				type: "disclaimer",
				content: "Ciri ini bersifat umum, bukan bukti silsilah atau rekomendasi mutlak.",
				items: []
			}
		];
	}

	let blocks: ContentBlock[] = getInitialBlocks();

	export function loadBreedProfileTemplate() {
		blocks = getBreedProfileTemplate();
	}

	function addBlock(type: BlockType = "paragraph", afterIndex: number = blocks.length - 1) {
		const newBlock: ContentBlock = {
			id: createId(),
			type,
			content: type === "disclaimer" ? "Ciri ini bersifat umum, bukan bukti silsilah atau rekomendasi mutlak." : "",
			items: type === "bullet_list" ? ["Poin baru"] : []
		};
		blocks = [
			...blocks.slice(0, afterIndex + 1),
			newBlock,
			...blocks.slice(afterIndex + 1)
		];
	}

	function removeBlock(index: number) {
		if (blocks.length <= 1) {
			blocks = [{ id: createId(), type: "paragraph", content: "", items: [] }];
			return;
		}
		blocks = blocks.filter((_, i) => i !== index);
	}

	function moveUp(index: number) {
		if (index === 0) return;
		const copy = [...blocks];
		const temp = copy[index - 1];
		copy[index - 1] = copy[index];
		copy[index] = temp;
		blocks = copy;
	}

	function moveDown(index: number) {
		if (index === blocks.length - 1) return;
		const copy = [...blocks];
		const temp = copy[index + 1];
		copy[index + 1] = copy[index];
		copy[index] = temp;
		blocks = copy;
	}

	function addBulletItem(blockIndex: number) {
		const block = blocks[blockIndex];
		if (!block) return;
		block.items = [...block.items, ""];
		blocks = [...blocks];
	}

	function removeBulletItem(blockIndex: number, itemIndex: number) {
		const block = blocks[blockIndex];
		if (!block) return;
		block.items = block.items.filter((_, i) => i !== itemIndex);
		if (block.items.length === 0) {
			block.items = [""];
		}
		blocks = [...blocks];
	}

	function updateBulletItem(blockIndex: number, itemIndex: number, val: string) {
		const block = blocks[blockIndex];
		if (!block) return;
		block.items[itemIndex] = val;
		blocks = [...blocks];
	}

	$: markdownBody = blocks
		.map((b) => {
			if (b.type === "heading") return `## ${b.content.trim()}`;
			if (b.type === "bullet_list") return b.items.filter(i => i.trim()).map(i => `• ${i.trim()}`).join("\n");
			if (b.type === "callout") return `> ${b.content.trim()}`;
			if (b.type === "disclaimer") return b.content.trim();
			return b.content.trim();
		})
		.filter(Boolean)
		.join("\n\n");

	$: blocksJson = JSON.stringify(blocks);
</script>

<div class="block-editor space-y-4">
	<!-- Hidden Inputs for Form Submission -->
	<input type="hidden" name="content_blocks" value={blocksJson} />
	<input type="hidden" name="body" value={markdownBody} />

	<!-- Editor Header Controls -->
	<div class="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 bg-slate-50/80 px-4 py-2.5 shadow-2xs">
		<div class="flex items-center gap-2.5">
			<span class="text-xs font-bold uppercase tracking-wider text-slate-700">
				Editor Blok Konten
			</span>
			<span class="rounded-full bg-slate-200 px-2.5 py-0.5 text-xs font-bold text-slate-800">
				{blocks.length} blok
			</span>
		</div>

		<div class="flex items-center gap-2">
			{#if isBreedProfile}
				<button
					type="button"
					class="group flex items-center gap-1.5 rounded-lg border border-emerald-300 bg-white px-3 py-1.5 text-xs font-bold text-emerald-800 shadow-2xs transition-all hover:bg-[#155e3d] hover:text-white hover:border-[#155e3d] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#155e3d] focus-visible:ring-offset-1 focus-visible:bg-[#155e3d] focus-visible:text-white focus-visible:border-[#155e3d]"
					on:click={loadBreedProfileTemplate}
				>
					<Sparkles size={14} class="text-emerald-700 transition-colors group-hover:text-white group-focus-visible:text-white" />
					Muat Template Profil Sapi
				</button>
			{/if}

			<div class="flex items-center rounded-lg border border-slate-300 bg-slate-100 p-0.5 shadow-2xs">
				<button
					type="button"
					class="flex items-center gap-1.5 rounded-md px-3 py-1 text-xs font-bold transition-all {viewMode === 'editor' ? 'bg-slate-900 text-white shadow-2xs' : 'bg-transparent text-slate-700 hover:bg-slate-200 hover:text-slate-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-900 focus-visible:bg-slate-200 focus-visible:text-slate-950'}"
					on:click={() => (viewMode = "editor")}
				>
					<Edit3 size={13} class="transition-colors {viewMode === 'editor' ? 'text-white' : 'text-slate-600'}" />
					Edit
				</button>
				<button
					type="button"
					class="flex items-center gap-1.5 rounded-md px-3 py-1 text-xs font-bold transition-all {viewMode === 'preview' ? 'bg-slate-900 text-white shadow-2xs' : 'bg-transparent text-slate-700 hover:bg-slate-200 hover:text-slate-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-900 focus-visible:bg-slate-200 focus-visible:text-slate-950'}"
					on:click={() => (viewMode = "preview")}
				>
					<Eye size={13} class="transition-colors {viewMode === 'preview' ? 'text-white' : 'text-slate-600'}" />
					Pratinjau
				</button>
			</div>
		</div>
	</div>

	<!-- Editor Mode -->
	{#if viewMode === "editor"}
		<div class="space-y-3">
			{#each blocks as block, index (block.id)}
				<div class="group relative rounded-xl border border-slate-200 bg-white p-4 shadow-2xs transition-all hover:border-slate-300 hover:shadow-sm">
					<!-- Block Header Toolbar -->
					<div class="mb-3 flex items-center justify-between border-b border-slate-100 pb-2.5">
						<div class="flex items-center gap-2.5">
							<span class="flex h-5 w-5 items-center justify-center rounded bg-slate-100 text-[11px] font-bold text-slate-700">
								{index + 1}
							</span>
							<select
								class="!min-h-8 !py-1 !px-2.5 text-xs font-semibold text-slate-800 border border-slate-200 rounded-lg bg-white shadow-2xs focus:border-[#155e3d] focus:ring-1 focus:ring-[#155e3d]"
								bind:value={block.type}
							>
								<option value="paragraph">Paragraf Deskripsi</option>
								<option value="heading">Judul Seksi (Heading)</option>
								<option value="bullet_list">Daftar Poin (Kelebihan / Kekurangan)</option>
								<option value="callout">Catatan / Callout</option>
								<option value="disclaimer">Disclaimer Resmi</option>
							</select>
						</div>

						<div class="flex items-center gap-1">
							<button
								type="button"
								class="flex h-7 w-7 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-700 shadow-2xs transition-all hover:bg-slate-900 hover:text-white hover:border-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-900 focus-visible:bg-slate-900 focus-visible:text-white focus-visible:border-slate-900 disabled:opacity-30 disabled:pointer-events-none disabled:bg-slate-100 disabled:text-slate-400 disabled:border-slate-200"
								disabled={index === 0}
								on:click={() => moveUp(index)}
								title="Pindah ke atas"
								aria-label="Pindah blok ke atas"
							>
								<ArrowUp size={14} class="transition-colors" />
							</button>
							<button
								type="button"
								class="flex h-7 w-7 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-700 shadow-2xs transition-all hover:bg-slate-900 hover:text-white hover:border-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-900 focus-visible:bg-slate-900 focus-visible:text-white focus-visible:border-slate-900 disabled:opacity-30 disabled:pointer-events-none disabled:bg-slate-100 disabled:text-slate-400 disabled:border-slate-200"
								disabled={index === blocks.length - 1}
								on:click={() => moveDown(index)}
								title="Pindah ke bawah"
								aria-label="Pindah blok ke bawah"
							>
								<ArrowDown size={14} class="transition-colors" />
							</button>
							<button
								type="button"
								class="flex h-7 w-7 items-center justify-center rounded-lg border border-rose-200 bg-rose-50 text-rose-700 shadow-2xs transition-all hover:bg-rose-700 hover:text-white hover:border-rose-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-700 focus-visible:bg-rose-700 focus-visible:text-white focus-visible:border-rose-700"
								on:click={() => removeBlock(index)}
								title="Hapus blok"
								aria-label="Hapus blok"
							>
								<Trash2 size={14} class="transition-colors" />
							</button>
						</div>
					</div>

					<!-- Block Body Content based on Type -->
					{#if block.type === "paragraph"}
						<textarea
							class="w-full resize-y rounded-lg border border-transparent p-2 text-sm text-slate-900 leading-relaxed placeholder:text-slate-400 focus:border-slate-200 focus:bg-slate-50/40 focus:outline-none focus:ring-2 focus:ring-[#155e3d]/15 min-h-20 transition"
							placeholder="Tuliskan deskripsi paragraf di sini..."
							bind:value={block.content}
						></textarea>
					{:else if block.type === "heading"}
						<div class="flex items-center gap-2">
							<Heading2 size={18} class="text-emerald-700 shrink-0" />
							<input
								type="text"
								class="w-full rounded-lg border border-transparent p-1.5 text-base font-bold text-slate-900 placeholder:text-slate-400 focus:border-slate-200 focus:bg-slate-50/40 focus:outline-none focus:ring-2 focus:ring-[#155e3d]/15 transition"
								placeholder="Judul Seksi (contoh: Ringkasan Profil, Kelebihan, dll.)..."
								bind:value={block.content}
							/>
						</div>
					{:else if block.type === "bullet_list"}
						<div class="space-y-2">
							{#each block.items as item, itemIndex}
								<div class="flex items-center gap-2">
									<span class="text-base font-bold text-emerald-700 leading-none">•</span>
									<input
										type="text"
										class="w-full rounded-lg border border-slate-200 p-2 text-sm text-slate-900 font-medium placeholder:text-slate-400 focus:border-[#155e3d] focus:outline-none focus:ring-2 focus:ring-[#155e3d]/15 shadow-2xs transition"
										placeholder="Isi butir poin kelebihan atau kekurangan..."
										value={item}
										on:input={(e) => updateBulletItem(index, itemIndex, e.currentTarget.value)}
										on:keydown={(e) => {
											if (e.key === 'Enter') {
												e.preventDefault();
												addBulletItem(index);
											}
										}}
									/>
									<button
										type="button"
										class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-500 shadow-2xs transition-all hover:bg-rose-700 hover:text-white hover:border-rose-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-700 focus-visible:bg-rose-700 focus-visible:text-white focus-visible:border-rose-700"
										on:click={() => removeBulletItem(index, itemIndex)}
										title="Hapus butir"
										aria-label="Hapus butir poin"
									>
										<Trash2 size={14} class="transition-colors" />
									</button>
								</div>
							{/each}
							<button
								type="button"
								class="group inline-flex items-center gap-1.5 rounded-lg border border-emerald-300 bg-emerald-50/70 px-3 py-1.5 text-xs font-bold text-emerald-900 shadow-2xs transition-all hover:bg-[#155e3d] hover:text-white hover:border-[#155e3d] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#155e3d] focus-visible:ring-offset-1 focus-visible:bg-[#155e3d] focus-visible:text-white focus-visible:border-[#155e3d] mt-1"
								on:click={() => addBulletItem(index)}
							>
								<Plus size={13} class="text-emerald-700 transition-colors group-hover:text-white group-focus-visible:text-white" />
								Tambah Butir Poin
							</button>
						</div>
					{:else if block.type === "callout"}
						<div class="flex gap-3 rounded-xl border border-teal-200/90 bg-teal-50/70 p-3.5">
							<AlertCircle size={18} class="mt-0.5 text-teal-700 shrink-0" />
							<textarea
								class="w-full resize-y border-0 bg-transparent p-0 text-sm font-medium text-teal-950 placeholder:text-teal-700/60 focus:outline-none leading-relaxed"
								placeholder="Tuliskan catatan penting atau saran perawatan..."
								bind:value={block.content}
							></textarea>
						</div>
					{:else if block.type === "disclaimer"}
						<div class="flex gap-3 rounded-xl border border-amber-200/90 bg-amber-50/80 p-3.5">
							<ShieldAlert size={18} class="mt-0.5 text-amber-700 shrink-0" />
							<textarea
								class="w-full resize-y border-0 bg-transparent p-0 text-xs font-medium italic text-amber-950 placeholder:text-amber-700/60 focus:outline-none leading-relaxed"
								placeholder="Ciri ini bersifat umum, bukan bukti silsilah atau rekomendasi mutlak."
								bind:value={block.content}
							></textarea>
						</div>
					{/if}
				</div>
			{/each}
		</div>

		<!-- Add New Block Buttons Toolbar -->
		<div class="flex flex-wrap items-center justify-center gap-2 rounded-xl border border-dashed border-slate-300 bg-slate-50/80 p-3.5 shadow-2xs">
			<span class="text-xs font-bold text-slate-700 mr-1 flex items-center gap-1">
				<Plus size={14} class="text-slate-600" />
				Tambah Blok:
			</span>
			<button
				type="button"
				class="group flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-bold text-slate-800 shadow-2xs transition-all hover:bg-slate-900 hover:text-white hover:border-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-900 focus-visible:ring-offset-1 focus-visible:bg-slate-900 focus-visible:text-white focus-visible:border-slate-900"
				on:click={() => addBlock("paragraph")}
			>
				<Type size={13} class="text-slate-600 transition-colors group-hover:text-white group-focus-visible:text-white" />
				Paragraf
			</button>
			<button
				type="button"
				class="group flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-bold text-slate-800 shadow-2xs transition-all hover:bg-slate-900 hover:text-white hover:border-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-900 focus-visible:ring-offset-1 focus-visible:bg-slate-900 focus-visible:text-white focus-visible:border-slate-900"
				on:click={() => addBlock("heading")}
			>
				<Heading2 size={13} class="text-slate-600 transition-colors group-hover:text-white group-focus-visible:text-white" />
				Judul
			</button>
			<button
				type="button"
				class="group flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-bold text-slate-800 shadow-2xs transition-all hover:bg-slate-900 hover:text-white hover:border-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-900 focus-visible:ring-offset-1 focus-visible:bg-slate-900 focus-visible:text-white focus-visible:border-slate-900"
				on:click={() => addBlock("bullet_list")}
			>
				<List size={13} class="text-slate-600 transition-colors group-hover:text-white group-focus-visible:text-white" />
				Daftar Poin
			</button>
			<button
				type="button"
				class="group flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-bold text-slate-800 shadow-2xs transition-all hover:bg-slate-900 hover:text-white hover:border-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-900 focus-visible:ring-offset-1 focus-visible:bg-slate-900 focus-visible:text-white focus-visible:border-slate-900"
				on:click={() => addBlock("callout")}
			>
				<AlertCircle size={13} class="text-slate-600 transition-colors group-hover:text-white group-focus-visible:text-white" />
				Catatan
			</button>
			<button
				type="button"
				class="group flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-bold text-slate-800 shadow-2xs transition-all hover:bg-slate-900 hover:text-white hover:border-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-900 focus-visible:ring-offset-1 focus-visible:bg-slate-900 focus-visible:text-white focus-visible:border-slate-900"
				on:click={() => addBlock("disclaimer")}
			>
				<ShieldAlert size={13} class="text-slate-600 transition-colors group-hover:text-white group-focus-visible:text-white" />
				Disclaimer
			</button>
		</div>
	{:else}
		<!-- Preview Mode -->
		<div class="rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
			<div class="space-y-4">
				{#each blocks as block}
					{#if block.type === "heading"}
						<h2 class="text-lg font-bold text-slate-950 border-b border-slate-200 pb-2">
							{block.content}
						</h2>
					{:else if block.type === "paragraph"}
						<p class="text-sm leading-relaxed text-slate-800">
							{block.content}
						</p>
					{:else if block.type === "bullet_list"}
						<ul class="space-y-1.5 pl-5 list-disc text-sm text-slate-800">
							{#each block.items.filter(i => i.trim()) as item}
								<li>{item}</li>
							{/each}
						</ul>
					{:else if block.type === "callout"}
						<div class="rounded-xl border-l-4 border-teal-600 bg-teal-50/70 p-4 text-sm font-medium text-teal-950 leading-relaxed">
							{block.content}
						</div>
					{:else if block.type === "disclaimer"}
						<div class="rounded-xl border border-amber-200 bg-amber-50/80 p-4 text-xs font-medium italic text-amber-950 leading-relaxed">
							{block.content}
						</div>
					{/if}
				{/each}
			</div>
		</div>
	{/if}
</div>
