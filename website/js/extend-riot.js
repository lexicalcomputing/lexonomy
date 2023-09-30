import {install} from 'riot'

install(function(component) {
   component.store = window.store
   component.dictData = window.store.data
   component.auth = window.auth
   component.authData = window.auth.data
   component.boundFunctions = {}

   let oldOnMounted = component.onMounted
   let oldOnBeforeUnmount = component.onBeforeUnmount
   let oldOnUpdated = component.onUpdated

   component.onMounted = () => {
      oldOnMounted.apply(component)
      if(component.bindings){
         let boundFunction
         component.bindings.forEach(b => {
            boundFunction = component[b[2]].bind(component)
            component[b[0]].on(b[1], boundFunction)
            component.boundFunctions[`${b[1]}_${b[2]}`] = boundFunction
         })
      }
      initTooltipDebounced()
   }
   component.onBeforeUnmount = () => {
      component.destroyTooltips()
      if(component.bindings){
         component.bindings.forEach(b => {
            component[b[0]].off(b[1], component.boundFunctions[`${b[1]}_${b[2]}`])
         })
      }
      oldOnBeforeUnmount.apply(component)
   }

   component.onUpdated = () => {
      oldOnUpdated.apply(component)
      initTooltipDebounced()
   }

   component.destroyTooltips = destroyTooltips

   return component
})

function destroyTooltips(){
   $('.tooltipped', this.root).each((idx, el) => {
      if(M.Tooltip.getInstance(el)){
         M.Tooltip.getInstance(el).destroy()
      }
   })
}

function initTooltipDebounced(){
   this.tooltipDebounceTimer && clearTimeout(this.tooltipDebounceTimer)
   this.tooltipDebounceTimer = setTimeout(() => {
       clearTimeout(this.tooltipDebounceTimer)
       $('.tooltipped').tooltip({
         enterDelay: 800
       })
   }, 100)
}
