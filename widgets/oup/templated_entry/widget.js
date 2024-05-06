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
         POS_OPTIONS: ["abbreviation", "adjective", "adposition", "adverb", "affix", "article", "clitic", "conjunction", "contraction", "determiner", "ideophone", "interjection", "noun", "numeral", "particle", "phrase", "predeterminer", "pronoun", "punctuation", "symbol", "verb", "other"]
      }
      this._render()
      this._validate()
   },

   getValue: function() {
      return this.entry
   },

   update: function(entry) {
      this.entry = entry
      this._render()
      this._validate()
   },

   _render: function() {
      this.contentNode.empty()
      this._renderForm()
      window.initFormSelects(this.contentNode)
   },

   _renderForm() {
      let formNode = $(`<div class=""></div>`).appendTo(this.contentNode)
      this.headword = ""
      this.pos = ""
      if(this.entry.value){
         let entryParts = this.entry.value.split("-")
         this.headword = entryParts[0]
         this.pos = entryParts[1]
      }
      let transcription = this._getChildValue(this.entry, "transcription")
      let senses = this._getChildElements(this.entry, "sense")
      let headNode = $(`<div class="grey lighten-4 p-4"></div>`).appendTo(formNode)
      let entryNode = $(`<div class="entryBar displayFlex" style="gap: 10px"></div>`).appendTo(headNode )
      let headwordNode = $(`<div class="input-field el_headword">
         <input name="headword" value="${this.headword}" ${this.options.readOnly ? ' disabled' : ''}/>
         <label>Headword</label>
      </div`).appendTo(entryNode)
      let optionNodes = `<option ${this.pos == "" ? 'selected' : ''} value="">-not set-</option>`
          + this.const.POS_OPTIONS.map(option => `<option value="${option}" ${this.pos == option ? 'selected' : ''}>${option}</option>`)
             .join("")
      let partOfSpeechSelect = $(`<div class="input-field el_pos">
               <select name="pos" ${this.options.readOnly ? ' disabled' : ''}>
                  ${optionNodes}
               </select>
               <label>Part of speech</label>
            </div`).appendTo(entryNode)
      headwordNode.find("input").on("input", this._onEntryInput.bind(this))
         .on("change", this.options.onChange.bind(this))
      partOfSpeechSelect.find("select").on("change", evt => {
         this._onEntryInput(evt)
         this.options.onChange()
      })

      let transcriptionNode = $(`<div class="input-field el_transcription">
         <input name="transcription" value="${transcription}" ${this.options.readOnly ? ' disabled' : ''}/>
         <label>Transcription</label>
      </div`).appendTo(headNode)
      transcriptionNode.find("input").on("input", this._onTranscriptionInput.bind(this))
            .on("change", this.options.onChange.bind(this))

      $(`<h3 class="grey-text">Senses</h3>`).appendTo(formNode)
      if(senses.length){
         for(sense of senses){
            let definition = this._getChildValue(sense, "definition")
            let translation = this._getChildValue(sense, "translation")
            let sense_transcription = this._getChildValue(sense, "sense_transcription")
            let senseNode = $(`<div class="displayFlex ml-4 mb-6" style="align-items: top; gap: 20px; "></div>`).appendTo(formNode)
            let senseContent = $(`<div class="grey lighten-4 p-4 ml-4" style="width: 100%;'"></div>`).appendTo(senseNode )
            !this.options.readOnly && $(`<button class="btn btn-flat btn-floating">
                  <i class="material-icons left">delete</i>
               </button>`).appendTo(senseNode)
                  .click(this._removeSense.bind(this, sense))
            this._renderSenseTextBox(sense, "definition", senseContent, "Definition")
            this._renderSenseTextBox(sense, "translation", senseContent, "Translation")
            this._renderSenseTextBox(sense, "sense_transcription", senseContent, "Transcription")
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

   _onEntryInput(evt){
     this[evt.target.name] = evt.target.value
     this.entry.value = `${this.headword}-${this.pos}`
     this._validate()
   },

   _getChildElement(parent, childName){
      return window.nvhStore.findElement(e => e.name == childName, parent)
   },

   _getChildElements(parent, childName){
      return window.nvhStore.findElements(e => e.name == childName, parent)
   },

   _getChildValue: function(parent, childName, defaultValue = "") {
      let child = this._getChildElement(parent, childName)
      return child ? child.value : defaultValue
   },

   _createChildElement: function(parent, childElementName){
     let child = {
         name: childElementName,
         value: "",
         parent: parent,
         children: []
      }
      parent.children.push(child)
      return child
   },

   _addSense: function(){
      this._createChildElement(this.entry, "sense")
      this._render()
      this._validate()
      this.options.onChange()
   },

   _removeSense(sense) {
      this.entry.children = this.entry.children.filter(child => child != sense)
      this._render()
      this._validate()
      this.options.onChange()
   },

   _onTranscriptionInput: function(evt){
      let child = this._getChildElement(this.entry, "transcription") || this._createChildElement(this.entry, "transcription")
      child.value = evt.target.value
   },

   _onSenseChildInput: function(sense, childName, evt) {
      let child = this._getChildElement(sense, childName) || this._createChildElement(sense, childName)
      child.value = evt.target.value
      this._validate()
   },

   _validate: function() {
      let wasValid = this.isValid
      this.isValid = !!this.headword
         && !!this.pos
         && this.pos != "-not set-"
         && ($(".el_definition input, .el_translation input").filter(function() {
         return this.value == ""
      }).length == 0)
      if (wasValid != this.isValid) {
         this.options.onValidChange(this.isValid)
      }
   }
}
