window.nvhPlugins.links = {

   isActive: function(element){
      let config = window.store.data.config
      return config.linking[element.name]
   },

   onPluginButtonClick: function(element){
      window.modal.open({
         tag: "nvh-links-dialog",
         class: "overflowVisible",
         small: true,
         showCloseButton: false,
         props: {
            element: element
         }
      })
   }
}
