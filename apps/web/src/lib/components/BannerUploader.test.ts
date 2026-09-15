import { render } from "svelte/server";
import { describe, expect, it } from "vitest";
import BannerUploader from "./BannerUploader.svelte";
import ImageCropModal from "./ImageCropModal.svelte";

describe("BannerUploader component", () => {
	it("renders dropzone and helper text when no banner is active", () => {
		const { body } = render(BannerUploader, {
			props: {
				bannerImageUrl: null,
			},
		});

		expect(body).toContain("Banner Gambar Artikel");
		expect(body).toContain("Klik untuk memilih gambar atau seret berkas ke sini");
		expect(body).toContain("16:9");
		expect(body).not.toContain("Banner aktif");
	});

	it("renders banner preview card and Crop Ulang button when banner is active", () => {
		const { body } = render(BannerUploader, {
			props: {
				bannerImageUrl: "/media/banners/banner_aceh.jpg",
			},
		});

		expect(body).toContain("Banner aktif");
		expect(body).toContain("/media/banners/banner_aceh.jpg");
		expect(body).toContain("Crop Ulang");
		expect(body).toContain("Ganti Gambar");
		expect(body).toContain("Hapus");
	});
});

describe("ImageCropModal component", () => {
	it("renders crop dialog title, 16:9 ratio label, and zoom controls", () => {
		const { body } = render(ImageCropModal, {
			props: {
				open: true,
				imageSrc: "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
				onConfirm: () => {},
				onCancel: () => {},
			},
		});

		expect(body).toContain("Atur Potongan Banner (16:9)");
		expect(body).toContain("Rasio 16:9 · Geser untuk memposisikan");
		expect(body).toContain("Perbesaran:");
		expect(body).toContain("Terapkan");
		expect(body).toContain("Batal");
	});
});
