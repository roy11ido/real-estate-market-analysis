import { MAX_UPLOAD_BYTES } from "./types";

/** Shrinks large images (e.g. iPhone photos) to fit the upload limit. Non-images are returned as-is. */
export async function fitForUpload(file: File): Promise<File> {
  if (file.size <= MAX_UPLOAD_BYTES || !file.type.startsWith("image/")) return file;
  const bitmap = await createImageBitmap(file).catch(() => null);
  if (!bitmap) return file;
  for (const [maxDim, quality] of [
    [2560, 0.85],
    [2048, 0.8],
    [1600, 0.75],
  ] as const) {
    const scale = Math.min(1, maxDim / Math.max(bitmap.width, bitmap.height));
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(bitmap.width * scale);
    canvas.height = Math.round(bitmap.height * scale);
    canvas.getContext("2d")!.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    const blob = await new Promise<Blob | null>((r) => canvas.toBlob(r, "image/jpeg", quality));
    if (blob && blob.size <= MAX_UPLOAD_BYTES) {
      return new File([blob], file.name.replace(/\.[^.]+$/, "") + ".jpg", { type: "image/jpeg" });
    }
  }
  return file;
}
