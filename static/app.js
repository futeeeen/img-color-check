const form = document.querySelector("#palette-form");
const imageInput = document.querySelector("#image-input");
const fileName = document.querySelector("#file-name");
const imageMeta = document.querySelector("#image-meta");
const statusNode = document.querySelector("#status");
const resultImage = document.querySelector("#result-image");
const emptyState = document.querySelector("#empty-state");
const downloadLink = document.querySelector("#download-link");
const hexStrip = document.querySelector("#hex-strip");
const layoutGuide = document.querySelector("#layout-guide");
const layoutSize = document.querySelector("#layout-size");
const layoutSwatches = document.querySelector("#layout-swatches");
const layoutInputs = [
  form.elements.canvas_width,
  form.elements.image_height,
  form.elements.swatch_height,
  form.elements.palette_count,
  form.elements.padding,
  form.elements.gutter,
];

function readNumber(name, fallback, minimum = 1) {
  const value = Number(form.elements[name].value);
  return Number.isFinite(value) && value >= minimum ? value : fallback;
}

function resetPreviewToGuide() {
  resultImage.classList.remove("is-visible");
  layoutGuide.classList.remove("is-hidden");
  emptyState.classList.remove("is-hidden");
  downloadLink.classList.add("is-disabled");
}

function updateLayoutGuide() {
  const width = readNumber("canvas_width", 1179);
  const imageHeight = readNumber("image_height", 650);
  const swatchHeight = readNumber("swatch_height", 214);
  const padding = readNumber("padding", 8, 0);
  const gutter = readNumber("gutter", 8, 0);
  const swatchCount = Math.round(readNumber("palette_count", 10));
  const totalHeight = imageHeight + swatchHeight + padding * 2 + gutter;

  layoutGuide.style.aspectRatio = `${width} / ${totalHeight}`;
  layoutGuide.style.gridTemplateRows = `${imageHeight}fr ${swatchHeight}fr`;
  layoutGuide.style.padding = `${Math.min(padding, 24)}px`;
  layoutGuide.style.gap = `${Math.min(gutter, 24)}px`;
  layoutSwatches.style.gap = `${Math.min(gutter, 24)}px`;
  layoutSize.textContent = `輸出：${width} x ${totalHeight} px`;

  const currentCount = layoutSwatches.children.length;
  if (currentCount !== swatchCount) {
    layoutSwatches.replaceChildren(
      ...Array.from({ length: swatchCount }, (_, index) => {
        const swatch = document.createElement("span");
        swatch.style.setProperty("--swatch-index", index);
        return swatch;
      })
    );
  }
}

layoutInputs.forEach((input) => {
  input.addEventListener("input", () => {
    updateLayoutGuide();
    resetPreviewToGuide();
  });
});

imageInput.addEventListener("change", () => {
  const file = imageInput.files[0];
  fileName.textContent = file ? file.name : "選擇圖片";
  imageMeta.textContent = "";
  if (file) {
    const objectUrl = URL.createObjectURL(file);
    const image = new Image();
    image.onload = () => {
      imageMeta.textContent = `原圖：${image.naturalWidth} x ${image.naturalHeight} px`;
      URL.revokeObjectURL(objectUrl);
    };
    image.onerror = () => {
      imageMeta.textContent = "無法讀取圖片尺寸";
      URL.revokeObjectURL(objectUrl);
    };
    image.src = objectUrl;
  }
  resetPreviewToGuide();
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  statusNode.textContent = "處理中";
  downloadLink.classList.add("is-disabled");

  const formData = new FormData(form);
  try {
    const response = await fetch("/generate", {
      method: "POST",
      body: formData,
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "產生失敗");
    }

    resultImage.src = `${payload.image_url}?t=${Date.now()}`;
    resultImage.classList.add("is-visible");
    layoutGuide.classList.add("is-hidden");
    emptyState.classList.add("is-hidden");
    downloadLink.href = payload.download_url;
    downloadLink.classList.remove("is-disabled");
    hexStrip.replaceChildren(
      ...payload.colors.map((hex) => {
        const swatch = document.createElement("span");
        swatch.className = "mini-swatch";
        swatch.style.backgroundColor = hex;
        swatch.title = hex;
        return swatch;
      })
    );
    statusNode.textContent = "完成";
  } catch (error) {
    statusNode.textContent = error.message;
  }
});

updateLayoutGuide();
