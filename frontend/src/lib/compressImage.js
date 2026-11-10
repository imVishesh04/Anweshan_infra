// Shrinks a phone photo in the browser before upload: longest side 2000 px,
// JPEG at 85%. A 12 MB phone photo usually becomes well under 1 MB, so it
// uploads fast on mobile data and never hits the 8 MB server limit.
// If the browser cannot read the file (for example some HEIC photos), the
// original file is returned and the server explains what to do.

const MAX_SIDE = 2000;

export const MAX_UPLOAD_MB = 8;

export async function compressImage(file, { maxSide = MAX_SIDE, quality = 0.85 } = {}) {
  if (!file || typeof createImageBitmap !== "function") return file;

  let bitmap;
  try {
    bitmap = await createImageBitmap(file, { imageOrientation: "from-image" });
  } catch (e) {
    return file;
  }

  const scale = Math.min(1, maxSide / Math.max(bitmap.width, bitmap.height));
  const width = Math.max(1, Math.round(bitmap.width * scale));
  const height = Math.max(1, Math.round(bitmap.height * scale));

  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d");
  if (!ctx) return file;
  ctx.fillStyle = "#ffffff"; // transparent PNG areas become white, not black
  ctx.fillRect(0, 0, width, height);
  ctx.drawImage(bitmap, 0, 0, width, height);
  if (typeof bitmap.close === "function") bitmap.close();

  const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", quality));
  if (!blob) return file;
  // Keep the original if it was already a small JPEG.
  if (scale === 1 && file.type === "image/jpeg" && blob.size >= file.size) return file;

  const base = (file.name || "photo").replace(/\.[^.]+$/, "");
  return new File([blob], `${base}.jpg`, { type: "image/jpeg" });
}
