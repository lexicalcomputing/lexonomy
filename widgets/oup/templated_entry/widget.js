{
   editor: function(options) {
      // options = {
      //   node: the node into which you should render the editor
      //   entry = JSON object representing the entry
      //   readOnly = true if we want the entry to be uneditable
      //   onChange = method to call if data changes
      //   onValidChange - method to call if data state changes from valid to invalid or vice versa
      // }
      this.options = options
      this.node = $(options.node)
      this.entry = options.entry
      let editorNode = $("<div class='myEditor p-2'></div>").appendTo(this.node)
      this.contentNode = $('<div class="myEditorContentNode"></div>').appendTo(editorNode)
      this.isValid = null
      this.const = {
         ENTRY_TYPE_OPTIONS: ["main", "derivative", "phrase"],
         POS_OPTIONS: ["abbreviation", "adjective", "adposition", "adverb", "affix", "article", "clitic", "conjunction", "contraction", "determiner", "ideophone", "interjection", "noun", "numeral", "particle", "phrase", "predeterminer", "pronoun", "punctuation", "symbol", "verb", "other"],
         SENSITIVITY_OPTIONS: ["derogatory", "offensive", "vulgar"]
      }
      this._addEntryTypeIfNeeded()
      this._render()
      this._validate()
   },

   getValue: function() {
      return this.entry
   },

   update: function(entry) {
      this.entry = entry
      this._addEntryTypeIfNeeded()
      this._render()
      this._validate()
   },

   _render: function() {
      this.contentNode.empty()
      this._renderForm()
      this._renderLexonomyNotes()
      window.initFormSelects(this.contentNode)
   },

   _renderForm: function() {
      let formNode = $(`<div class=""></div>`).appendTo(this.contentNode)
      this.headword = ""
      this.pos = ""
      if (this.entry.value) {
         let idx = this.entry.value.lastIndexOf('-')
         this.headword = this.entry.value.substr(0, idx)
         this.pos = this.entry.value.substr(idx + 1)
      }
      let transcription = this._getChildValue(this.entry, "transcription")
      let senses = this._getChildElements(this.entry, "sense")
      let headNode = $(`<div class="grey lighten-4 p-4"></div>`).appendTo(formNode)
      let entryNode = $(`<div class="entryBar displayFlex" style="gap: 10px"></div>`).appendTo(headNode)
      let headwordNode = $(`<div class="input-field el_headword">
         <input name="headword"
               value="${this.headword}"
               ${this.options.readOnly ? ' disabled' : ''}/>
         <label>Headword*</label>
      </div`).appendTo(entryNode)
      headwordNode.find("input").on("input", this._onEntryInput.bind(this))
         .on("change", this.options.onChange.bind(this))
      this._renderPartOfSpeech(entryNode)
      this._renderSensitivity(this.entry, entryNode, "register")
      let entryTypeDiv = $(`<div class="displayFlex" style="gap: 10px"></div>`).appendTo(headNode)
      this._renderEntryType(entryTypeDiv)
      this._renderEntryGroup(entryTypeDiv)

      let transcriptionNode = $(`<div class="input-field el_transcription">
         <input name="transcription" value="${transcription}" ${this.options.readOnly ? ' disabled' : ''}/>
         <label>Transcription</label>
      </div`).appendTo(headNode)
      transcriptionNode.find("input").on("input", this._onTranscriptionInput.bind(this))
         .on("change", this.options.onChange.bind(this))

      $(`<h3 class="grey-text">Senses</h3>`).appendTo(formNode)
      if (senses.length) {
         for (sense of senses) {
            let definition = this._getChildValue(sense, "definition")
            let translation = this._getChildValue(sense, "translation")
            let sense_transcription = this._getChildValue(sense, "sense_transcription")
            let senseNode = $(`<div class="displayFlex ml-4 mb-6" style="align-items: top; gap: 20px; "></div>`).appendTo(formNode)
            let senseContent = $(`<div class="grey lighten-4 p-4 ml-4" style="width: 100%;'"></div>`).appendTo(senseNode)
            !this.options.readOnly && $(`<button class="btn btn-flat btn-floating">
                  <i class="material-icons left">delete</i>
               </button>`).appendTo(senseNode)
               .click(this._removeSense.bind(this, sense))
            this._renderSenseTextBox(sense, "definition", senseContent, "Definition*")
            this._renderSenseTextBox(sense, "translation", senseContent, "Translation*")
            this._renderSenseTextBox(sense, "sense_transcription", senseContent, "Transcription")
            this._renderSensitivity(sense, senseContent, "sense_register")
         }
      } else {
         $(`<h4 class="grey-text ml-4">no senses</h4>`).appendTo(formNode)
      }
      !this.options.readOnly && $(`<button class="btn btn-secondary ml-8">
            <i class="material-icons left">add</i>
            add sense
         </button>`).appendTo(formNode)
         .click(this._addSense.bind(this))
   },

   _renderPartOfSpeech: function(parent) {
      let optionNodes = `<option ${this.pos == "" ? 'selected' : ''} value="">-not set-</option>` +
         this.const.POS_OPTIONS.map(option => `<option value="${option}" ${this.pos == option ? 'selected' : ''}>${option}</option>`)
         .join("")
      let partOfSpeechSelect = $(`<div class="input-field el_pos">
               <select name="pos"
                  ${this.options.readOnly ? ' disabled' : ''}>
                  ${optionNodes}
               </select>
               <label>Part of speech*</label>
            </div`).appendTo(parent)
      partOfSpeechSelect.find("select").on("change", evt => {
         this._onEntryInput(evt)
         this.options.onChange()
      })
   },

   _renderEntryType: function(parent) {
      let entryType = this._getChildValue(this.entry, "entry_type", "main")
      let optionNodes = this.const.ENTRY_TYPE_OPTIONS.map(option => `<option value="${option}" ${entryType == option ? 'selected' : ''}>${option}</option>`)
         .join("")
      let entryTypeSelect = $(`<div class="input-field el_entryType">
               <select name="entry_type"
                  ${this.options.readOnly ? ' disabled' : ''}>
                  ${optionNodes}
               </select>
               <label>Entry type</label>
            </div`).appendTo(parent)
      entryTypeSelect.find("select").on("change", this._onEntryTypeChange.bind(this))
   },

   _renderEntryGroup: function(parent) {
      let entry_type = this._getChildValue(this.entry, "entry_type", "main")
      let inputDiv = $(`<div class="el_entrygroup input-field displayFlex positionRelative ${entry_type == "main" ? "hide" : ""}"></div`).appendTo(parent)
      let entrygroup_lexid = this._getChildValue(this.entry, "entrygroup_lexid")
      let entrygroup_label = this._getChildValue(this.entry, "entrygroup_label")
      $(`<label>Entry group*</label>`).appendTo(inputDiv)
      $(`<input class="el_entrygroup_label"
          value="${entrygroup_label}"
          disabled/>
          <button class="openEntryGroupDropdownBtn btn btb-flat ${this.options.readOnly ? 'hide' : ''}">
             <i class="material-icons">search</i></button>
          <i class="entryGroupPreloader material-icons spin grey-text ml-2"
                style="display: none;">donut_large</i>
          <small class="el_entrygroup_lexid grey-text">${entrygroup_lexid ? 'ID: ' + entrygroup_lexid : ''}</small>
          <div class="entryGroupDropdownContainer z-depth-3"
                style="display: none;">
             <div class="input-field"
                   style="margin: 15px;">
                <input class="entrySearch"
                   placeholder="entry search"
                   style="margin-bottom: 0;"/>
             </div>
             <div class="entryMenu"></div>
          </div>
      `)
         .appendTo(inputDiv)
      $(".entrySearch").on("input", this._onEntryGroupSearchInput.bind(this))
         .on("keydown", this._onEntrySearchKeyDown.bind(this))
      $(".el_entrygroup button").on("click", this._openEntryGroupsDropdown.bind(this))
   },

   _onEntryTypeChange: function(evt) {
      let showEntryGroup = evt.target.value != "main" && evt.target.value != ""
      if (!showEntryGroup) {
         $(".el_entrygroup_lexid").html("")
         $(".el_entrygroup_label").val("")
         entrygroup_lexidElement = this._getChildElement(this.entry, "entrygroup_lexid")
         if (entrygroup_lexidElement) {
            entrygroup_lexidElement.value = ""
         }
         entrygroup_labelElement = this._getChildElement(this.entry, "entrygroup_label")
         if (entrygroup_labelElement) {
            entrygroup_labelElement.value = ""
         }
      }
      $(".el_entrygroup").toggleClass("hide", !showEntryGroup)

      let entryType = this._getOrCreateChildElement(this.entry, "entry_type")
      entryType.value = evt.target.value
      this._validate()
      this.options.onChange()
   },

   _onEntryGroupSearchInput: function(evt) {
      this.entrySearchDebounceTimer && clearTimeout(this.entrySearchDebounceTimer)
      this.entrySearchDebounceTimer = setTimeout(() => {
         clearTimeout(this.entrySearchDebounceTimer)
         let query = $(".entrySearch").val()
         if (query !== "") {
            this._openEntryGroupsDropdown()
            let advance_query = `entry~=".*${query}.*" and entry_type="main"`
            this._setLoadingEntryGroupsDropdown()
            window.store.loadEntries({
                  howmany: 500,
                  advance_query: advance_query,
                  offset: 0
               })
               .done(response => {
                  if (!response.error) {
                     this._updateEntryGroupsDropdownMenu(response.entries)
                  }
               })
         }
      }, 200)
   },

   _onEntrySearchKeyDown: function(evt) {
      if (evt.keyCode == 27) {
         this._closeEntryGroupsDropdown()
      }
   },

   _openEntryGroupsDropdown: function() {
      if (!$(".entryGroupDropdownContainer").is(":visible")) {
         $(".entryGroupDropdownContainer").show()
         $(".entryGroupDropdownContainer input").focus()
         $(".openEntryGroupDropdownBtn").attr("disabled", "disabled")
         document.addEventListener("click", this._handleClickOutside.bind(this))
      }
   },

   _closeEntryGroupsDropdown: function() {
      $(".entryGroupDropdownContainer").hide()
      $(".openEntryGroupDropdownBtn").attr("disabled", null)
      document.removeEventListener("click", this._handleClickOutside.bind(this))
   },

   _handleClickOutside: function(evt) {
      if ($(evt.target).closest(".el_entrygroup").length == 0) {
         this._closeEntryGroupsDropdown()
      }
   },

   _setLoadingEntryGroupsDropdown: function() {
      let entryMenu = $(".entryMenu")
      entryMenu.empty()
      $(`<div class="grey-text p-4">Loading...</div>`).appendTo(entryMenu)
   },

   _updateEntryGroupsDropdownMenu: function(entries) {
      let entryMenu = $(".entryMenu")
      entryMenu.empty()
      if (entries.length) {
         let menu = "<ul>"
         entries.forEach(entry => {
            menu += `<li id="${entry.id}">${entry.title}</li>`
         })
         menu += "<ul>"
         $(menu).appendTo(entryMenu)
         entryMenu.find("li").each(function(idx, el) {
            $(el).click(evt => {
               this._closeEntryGroupsDropdown()
               $(".entryGroupPreloader").show()
               $(".el_entrygroup_lexid").hide()
               $.ajax({
                  url: `${window.API_URL}${window.store.data.dictId}/entryread.json`,
                  method: "POST",
                  data: {
                     id: $(el).attr("id")
                  }
               }).done(response => {
                  if (!response.error) {
                     let entry = window.nvhStore.nvhToJson(response.nvh)
                     let entrygroup_lexid = ""
                     let entrygroup_lexidEl = nvhStore.findElement(el => el.name == "entrygroup_lexid", entry)
                     if(entrygroup_lexidEl){
                        entrygroup_lexid = entrygroup_lexidEl.value
                     }
                     let entrygroup_lexidElement = this._getOrCreateChildElement(this.entry, "entrygroup_lexid")
                     entrygroup_lexidElement.value = entrygroup_lexid
                     let entrygroup_labelElement = this._getOrCreateChildElement(this.entry, "entrygroup_label")
                     entrygroup_labelElement.value = entry.value
                     $(".el_entrygroup_label").val(entry.value)
                     $(".el_entrygroup_lexid").html(`ID: ${entrygroup_lexid}`)
                     this._validate()
                     this.options.onChange()
                  }
               }).always(response => {
                  $(".entryGroupPreloader").hide()
                  $(".el_entrygroup_lexid").show()
               })
            })
         }.bind(this))
      } else {
         $(`<div class="grey-text p-4">Nothing found...</div>`).appendTo(entryMenu)
      }
   },

   _renderSensitivity: function(parent, sensitivityElementName) {
      let sensitivity = this._getChildValue(this.entry, sensitivityElementName, "")
      let optionNodes = `<option ${sensitivity  == "" ? 'selected' : ''} value="">-not set-</option>` +
         this.const.SENSITIVITY_OPTIONS.map(option => `<option value="${option}" ${sensitivity == option ? 'selected' : ''}>${option}</option>`)
         .join("")
      let sensitivitySelect = $(`<div class="input-field el_sensitivity ml-auto">
               <select name="pos"
                  ${this.options.readOnly ? ' disabled' : ''}>
                  ${optionNodes}
               </select>
               <label>Sensitivity</label>
            </div`).appendTo(parentNode)
      sensitivitySelect.find("select").on("change", evt => {
         let sensitivity = this._getOrCreateChildElement(parentElement, sensitivityElementName)
         sensitivity.value = evt.target.value
         this._validate()
         this.options.onChange()
      })
   },

   _renderSenseTextBox: function(sense, childName, parentNode, label = "", readOnly = false) {
      let inputDiv = $(`<div class="input-field el_${childName}"></div`).appendTo(parentNode)
      let value = this._getChildValue(sense, childName)
      $(`<label>${label}</label>`).appendTo(inputDiv)
      $(`<input value="${value}"
          ${this.options.readOnly ? ' disabled' : ''}/>`)
         .appendTo(inputDiv)
         .on("input", this._onSenseChildInput.bind(this, sense, childName))
         .on("change", this.options.onChange)
   },

   _renderLexonomyNotes: function() {
      $(`<h3 class="grey-text">Notes</h3>`).appendTo(this.contentNode)
      let lexonomy_notes = this.entry.children.filter(e => e.name == "lexonomy_note")
      if (lexonomy_notes.length) {
         lexonomy_notes.forEach((lexonomy_note, idx) => {
            if(lexonomy_note.value !== ""){
               let lexonomy_noteRow = $(`<div class="lexonomy_noteRow displayFlex alignCenter pl-8"></div>`).appendTo(this.contentNode)
               let infoLength = lexonomy_note.value.substr(21).indexOf(":") + 21 + 1
               let info = lexonomy_note.value.substring(0, infoLength)
               let value = lexonomy_note.value.substr(infoLength)
               $(`<div>
                  <span class="grey-text">${info}</span>
                  <span>${value}</span>
               </div>`).appendTo(lexonomy_noteRow)
               let resolveDiv = $(`<div class="ml-4"></div>`).appendTo(lexonomy_noteRow)
               if(lexonomy_note.children.filter(e => e.name == "lexonomy_note_status").length == 0) {
                  $(`<button class="btn btn-secondary" style="height: 20px;line-height: 20px;">resolve</button>`)
                     .on("click", this._resolveLexonomyNote.bind(this, idx))
                     .appendTo(resolveDiv)
               }
               else {
                  $(`<i>(resolved)</i>`).appendTo(resolveDiv)
               }
            }
         })
      } else {
         $(`<div class="grey-text ml-8">no notes</div>`).appendTo(this.contentNode)
      }
      $(`<button class="btn btn-secondary ml-8 mt-2"><i class="material-icons left">add</i>add note</button>`).appendTo(this.contentNode)
         .click(this._addLexonomyNote.bind(this))
   },

   _addLexonomyNote() {
      if(lexonomy_note_value = prompt("Enter your note:")) {
         lexonomy_note_value = new Date().toLocaleString('en-GB') + " " + window.auth.data.email + ": " + lexonomy_note_value
         this.entry.children.push({
            name: "lexonomy_note",
            value: lexonomy_note_value,
            parent: this.entry,
            children: []
         })
         this._updateNotesInDB()
         this._render()
         this._validate()
         this.options.onChange()
      }
   },

   _resolveLexonomyNote(idx) {
       let lexonomy_notes = this.entry.children.filter(e => e.name == "lexonomy_note")
       lexonomy_notes[idx].children.push({
          name: "lexonomy_note_status",
          value: "resolved",
          parent: lexonomy_notes[idx],
          children: []
       })
       this._updateNotesInDB()
       this._render()
       this._validate()
       this.options.onChange()
   },

   _updateNotesInDB(){
     let entry = window.nvhStore.nvhToJson(window.store.data.entry.nvh)
     entry.children = entry.children.filter(c => c.name != "lexonomy_note")
     this.entry.children.filter(e => e.name == "lexonomy_note").forEach(note => {
        let new_note = {
           name: "lexonomy_note",
           value: note.value,
           parent: entry,
           children: []
        }
        note.children.forEach(noteChild => {
           new_note.children.push({
              name: noteChild.name,
              value: noteChild.value,
              parent: new_note,
              children: []
           })
        })
        entry.children.push(new_note)
     })
     window.store.updateEntry(window.nvhStore.jsonToNvh(entry))
   },

   _onEntryInput: function(evt) {
      this[evt.target.name] = evt.target.value
      this.entry.value = `${this.headword}-${this.pos}`
      this._validate()
   },

   _getChildElement: function(parent, childName) {
      return window.nvhStore.findElement(e => e.name == childName, parent)
   },

   _getOrCreateChildElement: function(parent, childName){
      return this._getChildElement(parent, childName) || this._createChildElement(parent, childName)
   },

   _getChildElements: function(parent, childName) {
      return window.nvhStore.findElements(e => e.name == childName, parent)
   },

   _getChildValue: function(parent, childName, defaultValue = "") {
      let child = this._getChildElement(parent, childName)
      return child ? child.value : defaultValue
   },

   _createChildElement: function(parent, childElementName) {
      let child = {
         name: childElementName,
         value: "",
         parent: parent,
         children: []
      }
      parent.children.push(child)
      return child
   },

   _addSense: function() {
      this._createChildElement(this.entry, "sense")
      this._render()
      this._validate()
      this.options.onChange()
   },

   _removeSense: function(sense) {
      this.entry.children = this.entry.children.filter(child => child != sense)
      this._render()
      this._validate()
      this.options.onChange()
   },

   _onTranscriptionInput: function(evt) {
      let child = this._getOrCreateChildElement(this.entry, "transcription")
      child.value = evt.target.value
   },

   _onSenseChildInput: function(sense, childName, evt) {
      let child = this._getOrCreateChildElement(sense, childName)
      child.value = evt.target.value
      this._validate()
   },

   _addEntryTypeIfNeeded: function(){
      if(window.store.data.entryId == "new"){
         this._getOrCreateChildElement(this.entry, "entry_type").value = "main"
         this._getOrCreateChildElement(this.entry, "entrygroup_lexid").value = "lxnm_" + Math.floor(Date.now() / 1000)
      }
   },

   _validate: function() {
      let wasValid = this.isValid
      this.isValid = !!this.headword &&
         !!this.pos &&
         this.pos != "-not set-" &&
         ($(".el_definition input, .el_translation input").filter(function() {
            return this.value == ""
         }).length == 0) &&
         this._getChildValue(this.entry, "entry_type") == "main" || this._getChildValue(this.entry, "entrygroup_lexid", "") != ""
      if (wasValid != this.isValid) {
         this.options.onValidChange(this.isValid)
      }
   }
}
