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


window.editorNeedsSaving = (evt) => {
   if(Screenful && Screenful.Editor && Screenful.Editor.needsSaving){
      if(!confirm(Screenful.Loc.unsavedConfirm)){
         if(evt){
            evt.stopImmediatePropagation()
            evt.stopPropagation()
            evt.preventDefault()
         }
         return true
      } else {
         Screenful.Editor.needsSaving = false
         return false
      }
   }
   return false
}
