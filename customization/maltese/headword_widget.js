{
   editor: function(options) {
      this.node = $(options.node)
      this.entry = options.entry
      this._render()
      this.EXAMPLE_ELEMENT_PATH = "entry.example"
      this.onEntryFlagChangedBound = this._onEntryFlagChanged.bind(this)
      this.onDocumentKeyDownBound = this._onDocumentKeyDown.bind(this)

      window.store.on("entryFlagChanged", this.onEntryFlagChangedBound)
   },

   destroy: function() {
      window.store.off("entryFlagChanged", this.onEntryFlagChangedBound)
      document.removeEventListener("keydown", this.onDocumentKeyDownBound)
   },

   getValue: function() {
      return this.entry
   },

   update: function() {
      this._render()
   },

   _render: function() {
      this.node.empty()
      $("<img>", {
         src: "/customization/czech/headwords_diagram.png",
         id: "img_instructions",
         style: "max-height: calc(100vh - 200px)"
      }).appendTo(this.node)
   },

   _onEntryFlagChanged: function(entryId, flags) {
      if (this.ignoreNextFlagUpdate) {
         this.ignoreNextFlagUpdate = false
         return // function was called after changing flag from this dialog, do not open it again
      }
      let exampleElements = window.nvhStore.findElements(el => el.path == this.EXAMPLE_ELEMENT_PATH)
      if (exampleElements.length == 0) {
         return // no examples, nothing to show
      }
      if (flags.length == 1 && !["ok", "name"].includes(flags[0])) {
         this.entryId = entryId
         let examplesHtml = ""
         let flagButtonsHtml = ""
         exampleElements.forEach(el => {
            examplesHtml += `<li class="example">${el.value}</li>`
         })
        if(examplesHtml){
          examplesHtml = `<ul class="exampleList browser-default">${examplesHtml}</ul>`
        }
         window.store.data.config.flagging.flags.forEach(flag => {
            flagButtonsHtml += `<button class="btnSetFlag btn" style="background-color: ${flag.color}" data-flag="${flag.name}">${flag.label} (${flag.key})</button>`
         })
         window.modal.open({
            title: "Are you sure?",
            tag: "raw-html",
            props: {
               content: `<div>Examples of headword usage:</div>
                  ${examplesHtml}
                  <div class="mt-2">You can change the flag to: </div>
                  <div class="buttons">${flagButtonsHtml}</div>`
            },
            onOpen: () => {
               document.querySelectorAll(".btnSetFlag").forEach(button => {
                  button.onclick = (evt) => {
                     this._changeFlag(evt.target.dataset.flag)
                  }
               })
               document.addEventListener("keydown", this.onDocumentKeyDownBound)
            },
            onCloseStart: () => {
               document.removeEventListener("keydown", this.onDocumentKeyDownBound)
            }
         })
      }
   },

   _onDocumentKeyDown: function(evt) {
      if (!evt.ctrlKey &&
         !evt.altKey &&
         !evt.metaKey) {
         let flag = window.store.data.config.flagging.flags.find(f => f.key == evt.key)
         this._changeFlag(flag?.name)
      }
   },

   _changeFlag: function(flag) {
      if (flag) {
         this.ignoreNextFlagUpdate = true
         window.store.setEntryFlag(this.entryId, [flag])
         window.modal.close()
      }
   }
}
