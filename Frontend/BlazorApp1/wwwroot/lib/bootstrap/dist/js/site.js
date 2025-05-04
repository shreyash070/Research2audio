// Function to set a session storage helper
window.sessionStorageHelper = {
  setItem: function (key, value) {
    sessionStorage.setItem(key, value);
  },
  getItem: function (key) {
    return sessionStorage.getItem(key);
  },
  removeItem: function (key) {
    sessionStorage.removeItem(key);
  },
};

// Function to set a cookie
window.setCookie = function (name, value, days) {
  let expires = "";
  if (days) {
    let date = new Date();
    date.setTime(date.getTime() + days * 24 * 60 * 60 * 1000);
    expires = "; expires=" + date.toUTCString();
  }
  document.cookie = name + "=" + value + ";" + expires + "; path=/";
};

window.downloadFile = (fileUrl, fileName) => {
  var a = document.createElement("a");
  a.href = fileUrl;
  a.download = fileName;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
};

window.BlazorDownloadFile = (fileName, contentType, byteArray) => {
  const blob = new Blob([new Uint8Array(byteArray)], { type: contentType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  link.click();
  URL.revokeObjectURL(url);
};
