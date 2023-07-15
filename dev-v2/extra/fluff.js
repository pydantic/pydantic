async function set_download_count(el) {
  const r = await fetch('https://errors.pydantic.dev/download-count.txt');
  if (r.status === 200) {
    el.innerText = await r.text();
  }
}

const download_count = document.getElementById('download-count');
if (download_count) {
  set_download_count(download_count)
}
