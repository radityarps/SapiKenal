<script lang="ts">
	import { tick } from "svelte";
	import { Crop, ZoomIn, ZoomOut, RotateCcw, Check, X, Loader2 } from "lucide-svelte";

	export let open: boolean = false;
	export let imageSrc: string | null = null;
	export let isUploading: boolean = false;
	export let onConfirm: (blob: Blob) => Promise<void> | void;
	export let onCancel: () => void;

	let dialog: HTMLDialogElement | undefined;
	let canvas: HTMLCanvasElement | undefined;
	let container: HTMLDivElement | undefined;

	let img: HTMLImageElement | null = null;
	let naturalWidth = 0;
	let naturalHeight = 0;

	// Crop frame logical dimensions (16:9)
	const cropWidth = 640;
	const cropHeight = 360;

	let baseScale = 1;
	let zoom = 1;
	let offsetX = 0;
	let offsetY = 0;

	let isDragging = false;
	let dragStartX = 0;
	let dragStartY = 0;

	// Pinch-to-zoom tracking
	let initialPinchDistance = 0;
	let initialPinchZoom = 1;

	$: if (typeof window !== "undefined" && open && imageSrc) {
		openModal();
	} else if (typeof window !== "undefined" && !open && dialog?.open) {
		dialog.close();
	}

	async function openModal() {
		await tick();
		if (typeof window === "undefined") return;
		if (dialog && !dialog.open) {
			dialog.showModal();
		}
		loadImage();
	}

	function loadImage() {
		if (typeof window === "undefined" || !imageSrc) return;
		const image = new window.Image();
		image.crossOrigin = "anonymous";
		image.onload = () => {
			img = image;
			naturalWidth = image.naturalWidth;
			naturalHeight = image.naturalHeight;

			// Base scale so the image completely fills the 16:9 crop frame (cover mode)
			baseScale = Math.max(cropWidth / naturalWidth, cropHeight / naturalHeight);
			zoom = 1;

			// Center the image initially
			const renderedW = naturalWidth * baseScale;
			const renderedH = naturalHeight * baseScale;
			offsetX = (cropWidth - renderedW) / 2;
			offsetY = (cropHeight - renderedH) / 2;

			drawCanvas();
		};
		image.src = imageSrc;
	}

	function getScale() {
		return baseScale * zoom;
	}

	function clampOffsets(x: number, y: number, currentZoom = zoom) {
		const scale = baseScale * currentZoom;
		const renderedW = naturalWidth * scale;
		const renderedH = naturalHeight * scale;

		const minX = cropWidth - renderedW;
		const maxX = 0;
		const minY = cropHeight - renderedH;
		const maxY = 0;

		const clampedX = Math.min(maxX, Math.max(minX, x));
		const clampedY = Math.min(maxY, Math.max(minY, y));

		return { x: clampedX, y: clampedY };
	}

	function drawCanvas() {
		if (!canvas || !img) return;
		const ctx = canvas.getContext("2d");
		if (!ctx) return;

		// Set internal resolution
		canvas.width = cropWidth;
		canvas.height = cropHeight;

		ctx.clearRect(0, 0, cropWidth, cropHeight);

		const scale = getScale();
		const renderedW = naturalWidth * scale;
		const renderedH = naturalHeight * scale;

		// Draw the image
		ctx.drawImage(img, offsetX, offsetY, renderedW, renderedH);

		// Draw rule-of-thirds grid overlay
		ctx.strokeStyle = "rgba(255, 255, 255, 0.35)";
		ctx.lineWidth = 1;

		const thirdW = cropWidth / 3;
		const thirdH = cropHeight / 3;

		ctx.beginPath();
		// Vertical grid lines
		ctx.moveTo(thirdW, 0);
		ctx.lineTo(thirdW, cropHeight);
		ctx.moveTo(thirdW * 2, 0);
		ctx.lineTo(thirdW * 2, cropHeight);
		// Horizontal grid lines
		ctx.moveTo(0, thirdH);
		ctx.lineTo(cropWidth, thirdH);
		ctx.moveTo(0, thirdH * 2);
		ctx.lineTo(cropWidth, thirdH * 2);
		ctx.stroke();

		// Draw outer subtle border inside canvas
		ctx.strokeStyle = "rgba(255, 255, 255, 0.6)";
		ctx.lineWidth = 2;
		ctx.strokeRect(1, 1, cropWidth - 2, cropHeight - 2);
	}

	function setZoom(newZoom: number) {
		if (!img) return;
		const targetZoom = Math.min(3.0, Math.max(1.0, newZoom));
		if (targetZoom === zoom) return;

		// Keep center of crop frame pinned
		const cx = cropWidth / 2;
		const cy = cropHeight / 2;

		const oldScale = getScale();
		const imgX = (cx - offsetX) / oldScale;
		const imgY = (cy - offsetY) / oldScale;

		zoom = targetZoom;
		const newScale = getScale();

		const rawX = cx - imgX * newScale;
		const rawY = cy - imgY * newScale;

		const clamped = clampOffsets(rawX, rawY, zoom);
		offsetX = clamped.x;
		offsetY = clamped.y;

		drawCanvas();
	}

	function onZoomSliderInput(e: Event) {
		const val = parseFloat((e.target as HTMLInputElement).value);
		setZoom(val);
	}

	function zoomIn() {
		setZoom(zoom + 0.2);
	}

	function zoomOut() {
		setZoom(zoom - 0.2);
	}

	function resetPosition() {
		if (!img) return;
		zoom = 1;
		const renderedW = naturalWidth * baseScale;
		const renderedH = naturalHeight * baseScale;
		offsetX = (cropWidth - renderedW) / 2;
		offsetY = (cropHeight - renderedH) / 2;
		drawCanvas();
	}

	function handleWheel(e: WheelEvent) {
		e.preventDefault();
		const delta = e.deltaY < 0 ? 0.1 : -0.1;
		setZoom(zoom + delta);
	}

	// Mouse drag handlers
	function onMouseDown(e: MouseEvent) {
		if (isUploading || !img) return;
		isDragging = true;
		dragStartX = e.clientX - offsetX;
		dragStartY = e.clientY - offsetY;
	}

	function onMouseMove(e: MouseEvent) {
		if (!isDragging || !img) return;
		const rawX = e.clientX - dragStartX;
		const rawY = e.clientY - dragStartY;
		const clamped = clampOffsets(rawX, rawY);
		offsetX = clamped.x;
		offsetY = clamped.y;
		drawCanvas();
	}

	function onMouseUp() {
		isDragging = false;
	}

	// Touch handlers for mobile/tablet admin support
	function onTouchStart(e: TouchEvent) {
		if (isUploading || !img) return;
		if (e.touches.length === 1) {
			isDragging = true;
			dragStartX = e.touches[0].clientX - offsetX;
			dragStartY = e.touches[0].clientY - offsetY;
		} else if (e.touches.length === 2) {
			isDragging = false;
			initialPinchDistance = Math.hypot(
				e.touches[0].clientX - e.touches[1].clientX,
				e.touches[0].clientY - e.touches[1].clientY
			);
			initialPinchZoom = zoom;
		}
	}

	function onTouchMove(e: TouchEvent) {
		if (!img) return;
		if (e.touches.length === 1 && isDragging) {
			e.preventDefault();
			const rawX = e.touches[0].clientX - dragStartX;
			const rawY = e.touches[0].clientY - dragStartY;
			const clamped = clampOffsets(rawX, rawY);
			offsetX = clamped.x;
			offsetY = clamped.y;
			drawCanvas();
		} else if (e.touches.length === 2 && initialPinchDistance > 0) {
			e.preventDefault();
			const currentDistance = Math.hypot(
				e.touches[0].clientX - e.touches[1].clientX,
				e.touches[0].clientY - e.touches[1].clientY
			);
			const factor = currentDistance / initialPinchDistance;
			setZoom(initialPinchZoom * factor);
		}
	}

	function onTouchEnd() {
		isDragging = false;
		initialPinchDistance = 0;
	}

	async function handleApplyCrop() {
		if (!img || isUploading) return;

		const scale = getScale();

		// Source coordinates in the original unscaled image
		const cropSourceX = Math.max(0, -offsetX / scale);
		const cropSourceY = Math.max(0, -offsetY / scale);
		const cropSourceW = Math.min(naturalWidth - cropSourceX, cropWidth / scale);
		const cropSourceH = Math.min(naturalHeight - cropSourceY, cropHeight / scale);

		// Target high-definition output size (16:9 ratio)
		const targetW = Math.min(1600, Math.max(960, Math.round(cropSourceW)));
		const targetH = Math.round(targetW * (9 / 16));

		const exportCanvas = document.createElement("canvas");
		exportCanvas.width = targetW;
		exportCanvas.height = targetH;
		const exportCtx = exportCanvas.getContext("2d");

		if (!exportCtx) return;

		exportCtx.imageSmoothingEnabled = true;
		exportCtx.imageSmoothingQuality = "high";
		exportCtx.drawImage(
			img,
			cropSourceX,
			cropSourceY,
			cropSourceW,
			cropSourceH,
			0,
			0,
			targetW,
			targetH
		);

		exportCanvas.toBlob(
			(blob) => {
				if (blob) {
					onConfirm(blob);
				}
			},
			"image/jpeg",
			0.92
		);
	}

	function handleCancel() {
		if (isUploading) return;
		dialog?.close();
		onCancel();
	}

	function closeFromBackdrop(event: MouseEvent) {
		if (event.target === dialog && !isUploading) {
			handleCancel();
		}
	}
</script>

<svelte:window on:mouseup={onMouseUp} />

<dialog
	bind:this={dialog}
	class="m-auto max-h-[calc(100dvh-2rem)] w-[min(94vw,42rem)] overflow-hidden rounded-2xl border border-slate-200 bg-white p-0 text-slate-900 shadow-[0_24px_70px_rgba(15,23,42,.25)] backdrop:bg-slate-900/60 backdrop:backdrop-blur-xs"
	aria-labelledby="crop-dialog-title"
	onclick={closeFromBackdrop}
	onclose={handleCancel}
>
	<div class="flex items-center justify-between border-b border-slate-200 px-5 py-3.5 bg-slate-50/70">
		<div class="flex items-center gap-2.5">
			<div class="flex size-8 items-center justify-center rounded-lg bg-emerald-100 text-emerald-800">
				<Crop size={17} strokeWidth={2.2} />
			</div>
			<div>
				<h2 id="crop-dialog-title" class="m-0 text-sm font-bold text-slate-900">
					Atur Potongan Banner (16:9)
				</h2>
				<p class="m-0 text-[11px] text-slate-500 font-medium">
					Geser dan atur perbesaran untuk menyesuaikan area banner yang akan ditampilkan.
				</p>
			</div>
		</div>
		<button
			type="button"
			class="grid size-8 place-items-center rounded-lg text-slate-500 hover:bg-slate-200 hover:text-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-900 transition-colors"
			onclick={handleCancel}
			disabled={isUploading}
			aria-label="Tutup pemotongan"
		>
			<X size={17} />
		</button>
	</div>

	<div class="p-5 space-y-4">
		<!-- Canvas Viewport Frame (16:9 Aspect Ratio) -->
		<div class="relative overflow-hidden rounded-xl bg-slate-950 border border-slate-800 shadow-inner flex items-center justify-center select-none touch-none">
			<!-- svelte-ignore a11y-no-static-element-interactions -->
			<div
				bind:this={container}
				class="relative w-full aspect-[16/9] flex items-center justify-center cursor-grab active:cursor-grabbing overflow-hidden"
				onmousedown={onMouseDown}
				onmousemove={onMouseMove}
				onwheel={handleWheel}
				ontouchstart={onTouchStart}
				ontouchmove={onTouchMove}
				ontouchend={onTouchEnd}
			>
				<canvas
					bind:this={canvas}
					class="w-full h-full block object-contain pointer-events-none"
				></canvas>
			</div>

			<div class="absolute bottom-2 left-2 rounded-md bg-slate-900/80 backdrop-blur-xs px-2 py-1 text-[11px] font-semibold text-white/90 pointer-events-none border border-white/10 shadow-xs">
				Rasio 16:9 · Geser untuk memposisikan
			</div>
		</div>

		<!-- Control Toolbar: Zoom Slider, Zoom Buttons, Reset -->
		<div class="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 bg-slate-50/80 px-4 py-2.5">
			<div class="flex items-center gap-3 flex-1 min-w-[200px]">
				<span class="text-xs font-bold text-slate-700 shrink-0">Perbesaran:</span>
				<button
					type="button"
					class="grid size-7 place-items-center rounded-md border border-slate-300 bg-white text-slate-700 hover:bg-slate-100 hover:text-slate-900 disabled:opacity-40 transition-all"
					onclick={zoomOut}
					disabled={zoom <= 1.0 || isUploading}
					aria-label="Perkecil"
				>
					<ZoomOut size={14} />
				</button>
				<input
					type="range"
					min="1.0"
					max="3.0"
					step="0.05"
					value={zoom}
					oninput={onZoomSliderInput}
					disabled={isUploading}
					class="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-[#155e3d]"
					aria-label="Tingkat zoom gambar"
				/>
				<button
					type="button"
					class="grid size-7 place-items-center rounded-md border border-slate-300 bg-white text-slate-700 hover:bg-slate-100 hover:text-slate-900 disabled:opacity-40 transition-all"
					onclick={zoomIn}
					disabled={zoom >= 3.0 || isUploading}
					aria-label="Perbesar"
				>
					<ZoomIn size={14} />
				</button>
				<span class="text-xs font-mono font-semibold text-slate-600 w-12 text-right">
					{Math.round(zoom * 100)}%
				</span>
			</div>

			<button
				type="button"
				class="inline-flex items-center gap-1.5 rounded-md border border-slate-300 bg-white px-2.5 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-100 hover:text-slate-900 transition-all shrink-0"
				onclick={resetPosition}
				disabled={isUploading}
			>
				<RotateCcw size={13} />
				<span>Reset</span>
			</button>
		</div>
	</div>

	<!-- Modal Footer -->
	<div class="flex items-center justify-end gap-2.5 border-t border-slate-200 px-5 py-3.5 bg-slate-50/50">
		<button
			type="button"
			class="button secondary !min-h-9 !py-1.5 !px-3.5 text-xs font-bold text-slate-800 border-slate-300 hover:bg-slate-900 hover:text-white hover:border-slate-900 transition-all"
			onclick={handleCancel}
			disabled={isUploading}
		>
			Batal
		</button>
		<button
			type="button"
			class="button inline-flex items-center gap-1.5 !min-h-9 !py-1.5 !px-4 text-xs font-bold bg-[#155e3d] hover:bg-[#0f462d] text-white shadow-2xs focus-visible:ring-2 focus-visible:ring-[#155e3d] focus-visible:outline-none transition-all disabled:opacity-60"
			onclick={handleApplyCrop}
			disabled={isUploading}
		>
			{#if isUploading}
				<Loader2 size={14} class="animate-spin" />
				<span>Mengunggah...</span>
			{:else}
				<Check size={14} strokeWidth={2.5} />
				<span>Terapkan & Unggah</span>
			{/if}
		</button>
	</div>
</dialog>
