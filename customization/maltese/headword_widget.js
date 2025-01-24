{
   editor: function(options) {
      this.node = $(options.node)
      this.entry = options.entry
      this._render()
      this.CONCORDANCE_ELEMENT_PATH = "entry.conc"
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
         src: "/customization/maltese/headwords_diagram.png",
         id: "img_instructions",
         style: "max-height: calc(100vh - 200px)"
      }).appendTo(this.node)
   },

   _onEntryFlagChanged: function(entryId, flags) {
      if(entryId != window.store.data.entryId){
          window.store.one("entryChanged", this._showDialog.bind(this, entryId, flags))
          window.store.changeEntryId(entryId)
      } else{
         this._showDialog(entryId, flags)
      }
   },

   _showDialog(entryId, flags){
      if (this.ignoreNextFlagUpdate) {
         this.ignoreNextFlagUpdate = false
         return // function was called after changing flag from this dialog, do not open it again
      }
      let concLines = window.nvhStore.findElements(el => el.path == this.CONCORDANCE_ELEMENT_PATH)
      if (concLines.length == 0) {
         return // no concordance lines, nothing to show
      }
      if (flags.length == 1 && !["ok", "name"].includes(flags[0])) {
         this.entryId = entryId
         let concHtml = ""
         let flagButtonsHtml = ""
         concLines.forEach(el => {
            line = el.value
            kwicValue = this._getChildElement(el, "kwic").value
            let [undefined, kwic, kwicOrder] = kwicValue.match(/^(.*?)(?:#([^#]*))?$/)
            kwicOrder = kwicOrder ? parseInt(kwicOrder) : 1
            kwicPos = this._indexOfNth(line, kwic, kwicOrder)
            left = line.substring(0, kwicPos)
            right = line.substring(kwicPos + kwic.length)
            concHtml += `<li class="concLine">${left}<strong>${kwic}</strong>${right}</li>`
         })
         if(concHtml){
           concHtml = `<ul class="concLines browser-default">${concHtml}</ul>`
         }
         let selectedFlagColor = ""
         let selectedFlagTextColor = ""
         window.store.data.config.flagging.flags.forEach(flag => {
           if(flag.name != flags[0]){
              let color = this._getContrastColor(flag.color)
              flagButtonsHtml += `<button class="btnSetFlag btn" style="background-color: ${flag.color}; color: ${color};" data-flag="${flag.name}">${flag.label} (${flag.key})</button>`
           } else {
             selectedFlagColor = flag.color
             selectedFlagTextColor = this._getContrastColor(flag.color)
           }
         })
         this.selectedEntry = document.querySelector(".entry-list a.focused")
         let selectedFlagLabel = window.store.data.config.flagging.flags.find(flag => flag.name == flags[0])?.label || flags[0]
         window.modal.open({
            title: "Are you sure?",
            tag: "raw-html",
            props: {
               content: `<div class="grey-text">You have selected "<span class="black-text"><b>${selectedFlagLabel}</b></span>".</div> <div class="grey-text">Examples of headword usage are:</div>
                  ${concHtml}
                  <div class="mt-2 grey-text">You can change the flag to: </div>
                  <div class="buttons" style="flex-wrap: wrap">${flagButtonsHtml}</div>`
            },
            onOpen: () => {
               let closeBtn = document.querySelector(".modal-close")
               closeBtn.innerHTML = `Keep: ${selectedFlagLabel} (esc)`;
               closeBtn.style.backgroundColor = selectedFlagColor
               closeBtn.style.color = selectedFlagTextColor
               document.querySelectorAll(".btnSetFlag").forEach(button => {
                  button.addEventListener("click", (evt) => {
                     this._changeFlag(evt.target.dataset.flag)
                  })
               })
               document.addEventListener("keydown", this.onDocumentKeyDownBound)
            },
            onCloseStart: () => {
               document.removeEventListener("keydown", this.onDocumentKeyDownBound)
            },
            onClose: () => {
              this.selectedEntry.click() // set focus back to the entry list
           }
         })
      }
   },

   _onDocumentKeyDown: function(evt) {
      if (!evt.ctrlKey &&
         !evt.altKey &&
         !evt.metaKey) {
         let flag = window.store.data.config.flagging.flags.find(f => f.key == evt.key)
         if(!window.store.data.entryList.find(e => e.id == this.entryId).isSaving){
           this._changeFlag(flag?.name)
         }
         if(flag?.name){
           this.ignoreNextFlagUpdate = true
           window.modal.close()
         }
      }
   },

   _changeFlag: function(flag) {
      if (flag) {
         this.ignoreNextFlagUpdate = true
         window.store.setEntryFlag(this.entryId, [flag])
         window.modal.close()
      }
   },

   _getChildElement: function(parent, childName) {
      return window.nvhStore.findElement(e => e.name == childName, parent)
   },

   _getContrastColor: function(bgColor) {
      bgColor = bgColor.replace('#', '');
      let r = parseInt(bgColor.substring(0, 2), 16);
      let g = parseInt(bgColor.substring(2, 4), 16);
      let b = parseInt(bgColor.substring(4, 6), 16);

      let yiq = ((r*299) + (g*587) + (b*114)) / 1000;
      return (yiq >= 128) ? '#000' : '#fff';
   },

   _indexOfNth(inString, searchString, n) {
     let start = inString.indexOf(searchString)
     while(start >= 0 && n-- > 1) start = inString.indexOf(searchString, start+1)
     return start
   }
}
