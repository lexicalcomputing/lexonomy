window.showTooltip = (selector, message, delay, options) => {
   let node = $(selector)
   let instance = M.Tooltip.getInstance(node)
   if(instance){
      instance.destroy()
   }


   node.tooltip(Object.assign({
      enterDelay: delay || 0,
      exitDelay: 500,
      html: message
   }, options || {}))
   let tooltip = M.Tooltip.getInstance(node)
   setTimeout(function(node){
      if($(node).is(":hover")){
         let tooltip = M.Tooltip.getInstance(node)
         tooltip && tooltip.open()
      }
   }.bind(null, node), delay || 0)
   node.one("mouseleave", function(){
      !this.isOpen && this.destroy()
   }.bind(tooltip))

   return tooltip
}

window.isEmail = (str) => {
   return new RegExp(/^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/).test(str)
}

window.scrollToTheEndOfInput = (selector) => {
   setTimeout(() => {
      let el = $(selector)[0]
      if(el){
         if(el.getAttribute("contenteditable")){
            window.getSelection().selectAllChildren(el)
            window.getSelection().collapseToEnd()
         } else if(el.value){
            let l = el.value.length
            el.setSelectionRange(l, l)
            el.scrollLeft = el.scrollWidth
         }
      }
   }, 0)
}

window.shortenText = (str, max) => {
   return str.substr(0, max) + (str.length > max ? "…" : "")
}

window.numToRomanNum = (num) => {
   let romanNumbers = {
      M: 1000,
      CM: 900,
      D: 500,
      CD: 400,
      C: 100,
      XC: 90,
      L: 50,
      XL: 40,
      X: 10,
      IX: 9,
      V: 5,
      IV: 4,
      I: 1
   }
   let ret = ""
   for (let i in romanNumbers) {
      while(num >= romanNumbers[i]) {
         ret += i
         num -= romanNumbers[i]
      }
   }
   return ret
}

window.numToAlphabet = n => {
   // 1->a, 25->z, 26->aa...
   n--
   let s = ""
   while(n >= 0) {
      s = String.fromCharCode(n % 26 + 97) + s
      n = Math.floor(n / 26) - 1
   }
   return s
}

window.getInputValueWidth = (el) => {
   const canvas = getInputValueWidth.canvas || (getInputValueWidth.canvas = document.createElement("canvas"))
   const context = canvas.getContext("2d")
   const computedStyle = window.getComputedStyle(el, null)
   const fontWeight = computedStyle.getPropertyValue('font-weight') || 'normal'
   const fontSize = computedStyle.getPropertyValue('font-size') || '16px'
   const fontFamily = computedStyle.getPropertyValue('font-family') || 'Helvetica'
   context.font = `${fontWeight} ${fontSize} ${fontFamily}`
   return context.measureText(el.value).width
}

window.makeElementDraggable = (element, dragHandle) => {
   let diffX = 0
   let diffY = 0
   let lastX = 0
   let lastY = 0
   element = $(element)[0]
   element.style.position = "fixed"
   dragHandle = dragHandle ? $(dragHandle)[0] : element
   dragHandle.onmousedown = onMouseDown
   dragHandle.style.cursor = "move"

   function onMouseDown(evt) {
      evt.preventDefault()
      lastX = evt.clientX
      lastY = evt.clientY
      document.onmouseup = onMouseUp
      document.onmousemove = onMouseMove
   }

   function onMouseMove(evt) {
      evt.preventDefault();
      diffX = lastX - evt.clientX
      diffY = lastY - evt.clientY
      lastX = evt.clientX
      lastY = evt.clientY
      let BR = element.getBoundingClientRect()
      if ((BR.y > 5 || diffY < 0) &&
         (BR.y < (window.innerHeight - 50) || diffY > 0)){
         element.style.top = (element.offsetTop - diffY) + "px"
      }
      if((BR.x > 5 || diffX < 0) &&
         (BR.x < (window.innerWidth - BR.width) || diffX > 0)) {
         element.style.left = (element.offsetLeft - diffX) + "px"
      }
   }

   function onMouseUp() {
      document.onmouseup = null
      document.onmousemove = null
   }
}

window.dateToTimeAgo = (date) => {
   let seconds = Math.floor((new Date() - date) / 1000)
   let interval = seconds / 31536000

   if (interval > 1) {
      return Math.floor(interval) + " years ago"
   }
   interval = seconds / 2592000
   if (interval > 1) {
      return Math.floor(interval) + " months ago"
   }
   interval = seconds / 86400
   if (interval > 1) {
      return Math.floor(interval) + " days ago"
   }
   interval = seconds / 3600
   if (interval > 1) {
      return Math.floor(interval) + " hours ago"
   }
   interval = seconds / 60
   if (interval > 1) {
      return Math.floor(interval) + " minutes ago"
   }
   if(seconds < 5){ // seconds may be less than 0
      return "few seconds ago"
   }
   return Math.floor(seconds) + " seconds ago"
}

window.stopEvtPropagation = (evt) => {
   evt.stopPropagation()
}

window.getCookie = (name) => {
   let decodedCookie = decodeURIComponent(document.cookie)
   let cookies = decodedCookie.split(';')
   for(let i = 0; i < cookies.length; i++) {
      let cookie = cookies[i].trim()
      if (cookie.startsWith(`${name}=`)) {
         return cookie.substring(name.length + 1, cookie.length)
      }
   }
   return ""
}

window.setCookie = (name, value, expirationDays) => {
   let date = new Date()
   expirationDays = expirationDays || 365 * 2 // Chrome maximum is 400 days, Firefox 2 years
   date.setTime(date.getTime() + (expirationDays * 24 * 60 * 60 * 1000))
   let expires = "expires="+ date.toUTCString()
   document.cookie = name + "=" + value + ";" + expires + ";path=/"
}

window.removeCookie = (name) => {
   document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:01 GMT`
}

window.capitalize = (str) => {
   return str.charAt(0).toUpperCase() + str.slice(1);
}

window.trim = (str, max) => {
   if(!str){
      return ""
   }
   return (str + "").length > max ? ((str + "").substr(0, max) + "…") : str
}

window.initFormSelects = (context, selector) => {
   return $(selector || "select", context).formSelect({
      dropdownOptions: {
         coverTrigger: false,
         constrainWidth: false
      }
   })
}

window.getProgressColorClass = progress => {
   if(progress == 100){
      return "green"
   }
   if(progress < 50){
      return "red"
   }
   return "orange"
}


window.stopEvtPropagation = (evt) => {
   evt.stopPropagation()
}


window.idEscape = str => {
   return encodeURIComponent(str).replace(/\W/g,'_') // valid HTML and jQuery ID
}

