function initBrowserUpdate() {
   window.$buoop = {
      required: {
         e: -3,
         f: -3,
         o: -3,
         s: -1,
         c: 129
      },
      insecure: true,
      api: 2024.09
   }
   var e = document.createElement("script")
   e.src = "//browser-update.org/update.min.js"
   document.body.appendChild(e)
}
try {
   document.addEventListener("DOMContentLoaded", initBrowserUpdate, false)
} catch (e) {
   window.attachEvent("onload", initBrowserUpdate)
}
