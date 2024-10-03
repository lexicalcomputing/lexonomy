window.nvhPlugins.voiceRss = {

   isActive: function(element){
      let config = window.store.data.config
      return element.path == config.titling.headword
            && config.gapi.voicekey
            && config.gapi.voicelang != ''
            && !!window.nvhStore.findElement(e => e.path == window.store.data.config.titling.headword).value
   },

   onPluginButtonClick: function(){
      let gapi = window.store.data.config.gapi
      let headword = window.nvhStore.findElement(e => e.path == window.store.data.config.titling.headword).value
      let audio = new Audio(`https://api.voicerss.org/?key=${gapi.voicekey}&hl=${gapi.voicelang}&src=${headword}`)
      audio.play()
   }
}
