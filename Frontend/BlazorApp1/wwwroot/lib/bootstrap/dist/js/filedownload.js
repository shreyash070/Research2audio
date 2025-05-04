window.BlazorDownloadFile = (fileName, contentType, byteArray) => {
  const blob = new Blob([new Uint8Array(byteArray)], { type: contentType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  link.click();
  URL.revokeObjectURL(url);
};
