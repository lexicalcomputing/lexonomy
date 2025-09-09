{
   diagramURL: 'https://cloud.sketchengine.eu/index.php/s/QZTTQoPSfHTo7Mj/download',


   editor: function(options) {
      this.node = $(options.node)
      this.entry = options.entry
      this.onEntryFlagChangedBound = this._onEntryFlagChanged.bind(this)
      window.store.on("entryFlagChanged", this.onEntryFlagChangedBound)
      this._render()
   },

   getValue: function() {
      return this.entry
   },

   update: function() {
   },

   destroy: function() {
      window.store.off("entryFlagChanged", this.onEntryFlagChangedBound)
   },

   _render: function() {
      $("<img>", {
         src: this.diagramURL,
         id: "img_instructions",
         style: "max-height: calc(100vh - 200px)"
      }).appendTo(this.node)
   },

   _loadEntry: function(entryId) {
      return window.connection.post({
         url: `${window.API_URL}${window.store.data.dictId}/entryread.json`,
         data: {
            id: entryId
         }
      })
   },

   _updateEntryCompleted: function(entryId, flags) {
      this._loadEntry(entryId)
         .done(response => {
            if (response.success) {
               let completed = flags.length
               let nvh = response.nvh
               let lines = nvh.split("\n")
               lines = lines.filter(line => !line.trim().startsWith("__lexonomy__complete:"))
               if (completed) {
                  let indentSize = window.nvhStore.guessNvhIndentSize(nvh)
                  lines.push(`${" ".repeat(indentSize)}__lexonomy__complete: 1`)
               }
               nvh = lines.join("\n")

               return window.connection.post({
                     url: `${window.API_URL}${window.store.data.dictId}/entryupdate.json`,
                     data: {
                        id: entryId,
                        nvh: nvh
                     },
                     failMessage: "Could not toggle entry completed status."
                  })
                  .always(response => {
                     if (response.success) {
                        window.store.reloadStats()
                        let entryInEntryList = window.store.data.entryList.find(e => e.id == response.id)
                        if (entryInEntryList) {
                           entryInEntryList.is_completed = completed
                           window.store.trigger("entryListChanged")
                        }
                     }
                  })
            }
         })
   },

   _onEntryFlagChanged: function(entryId, flags) {
      if (entryId == window.store.data.entryId) {
         this._updateEntryCompleted(entryId, flags)
      } else {
         this._loadEntry(entryId)
            .done(response => {
               if (response.success) {
                  this._updateEntryCompleted(entryId, flags)
               }
            })
      }
   }
}