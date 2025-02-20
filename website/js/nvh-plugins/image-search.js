window.nvhPlugins.imageSearch = {
   isActive: function(element){
      let config = window.store.data.config
      let elementType = window.store.schema.getElementByPath(element.path)?.type
      return ((config.gapi.apikey && config.gapi.cx) || config.gapi.pixabaykey)
            && elementType == 'med'
   },

   onPluginButtonClick: function(element, evt){
      evt.stopPropagation()
      var headword = window.nvhStore.findElement(e => e.path == window.store.data.config.titling.headword).value
      if(headword) {
         window.nvhStore.trigger("toggleWidgetPanelLoading", true, "Searching...")
         window.nvhStore.trigger("toggleWidgetPanelOpen", true, "Image Search")

         window.connection.get({
            url: `${window.API_URL}/${window.store.data.dictId}/getmedia/${headword}`,
            failMessage: "Could not load images."
         })
               .done(json => {
                  if(json.images && json.images.length > 0) {
                     let content = $("<div class=\"nvh-gmedia-container\"></div>")
                     json.images.forEach(image => {
                        let imageHtml = $(`<div class="mb-2"></div>`).appendTo(content)
                        $(`<img src="${image.thumb}" class="pointer">`)
                              .click(function(image, element, evt){
                                    window.nvhStore.changeElementValue(element, image.url)
                                    $(".nvh-gmedia-container .nvh-gmedia-selected").removeClass("nvh-gmedia-selected")
                                    $(evt.target).addClass("nvh-gmedia-selected")
                                 }.bind(this, image, element))
                              .appendTo(imageHtml)
                        $(`<div class="nvh-gmedia-description">${image.title}</div>`).appendTo(imageHtml)
                     })
                     window.nvhStore.trigger("updateWidgetPanelContent", content)
                  } else {
                     window.nvhStore.trigger("updateWidgetPanelContent", "<div>no results found</div>")
                  }
                  window.nvhStore.trigger("toggleWidgetPanelLoading", false)
               })
      } else {
         M.toast({html: "No headword set"})
      }
   }
}



