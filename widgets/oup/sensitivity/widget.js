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
      let editorNode = $("<div class='myEditor'></div>").appendTo(this.node)
      this.contentNode = $('<div class="myEditorContentNode"></div>').appendTo(editorNode)
      this.isValid = null
      this.const = {
         TRANSLATION_REGISTER_OPTIONS: ["literal", "figurative", "derogatory", "informal"]
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

   _addTranslationRegistersToTranslationGroups: function(){
      window.nvhStore.findElements((e => e.name == "translationgroup"), this.entry)
         .forEach(translationgroup => {
            if(!translationgroup.children.find(c => c.name == "translation_register")){
               translationgroup.children.push({
                  name: "translation_register",
                  value: "",
                  parent: translationgroup,
                  children: []
               })
            }
         })
    },

   _render: function() {
      this.contentNode.empty()
      this._renderHeader()
      this._renderSenses()
      window.initFormSelects(this.contentNode)
   },

   _renderHeader() {
      let register = this._getChildValue(this.entry, "register", "-not set-")
      let domain = this._getChildValue(this.entry, "domain", "-not set-")
      let region = this._getChildValue(this.entry, "region", "-not set-")
      $(`<div class="displayFlex alignCenter" style="gap:10px;">
        <h2>${this.entry.value}</h2>
        <span class="ml-auto"></span>
        <span class="grey-text">register</span>
        <span>${register}</span>
        <span class="grey-text">domain</span>
        <span>${domain}</span>
        <span class="grey-text">region</span>
        <span>${region}</span>
      </div>`).appendTo(this.contentNode)
   },

   _renderSenses: function() {
      $(`<h3 class="grey-text">Senses</h3>`).appendTo(this.contentNode)
      for (sense of this.entry.children.filter(e => e.name == "sense")) {
         let senseWrapper = $(`<div class="senseWrapper mb-4 ml-6"></div>`).appendTo(this.contentNode)
         let senseHeader = $(`<div class="senseHeader grey lighten-3 pl-4 pr-4"></div>`).appendTo(senseWrapper)
         let senseContainer = $(`<div class="senseContainer grey lighten-4 p-4"></div>`).appendTo(senseWrapper)
         let definition = this._getChildValue(sense, "definition", "-not set-")
         let sense_indicator = this._getChildValue(sense, "sense_indicator", "-not set-")
         let sense_register = this._getChildValue(sense, "sense_register", "-not set-")
         let sense_domain = this._getChildValue(sense, "sense_domain", "-not set-")
         let sense_region = this._getChildValue(sense, "sense_region", "-not set-")
         let translationgroup = window.nvhStore.findElement(e => e.name == "translationgroup", sense)
         $(`<div class="displayFlex alignCenter" style="gap:10px;">
         <h3>${sense.value}</h3>
         <span class="ml-auto"></span>
         <span class="grey-text">indicator</span>
         <span>${sense_indicator}</span>
         <span class="grey-text">register</span>
         <span>${sense_register}</span>
         <span class="grey-text">domain</span>
         <span>${sense_domain}</span>
         <span class="grey-text">region</span>
         <span>${sense_region}</span>
       </div>`).appendTo(senseHeader)
         $(`<label class="displayFlex alignCenter mt-2">definition</label>`).appendTo(senseContainer)
         $(`<div class="grey-text pl-8">${definition}</div>`).appendTo(senseContainer)

         if (translationgroup) {
            $(`<label class="displayFlex alignCenter mt-2">translations</label>`).appendTo(senseContainer)
            for (translation of translationgroup.children.filter(e => e.name == "translation")) {
               let translationRow = $(`<div class="translationRow displayFlex alignCenter pl-8"></div>`).appendTo(senseContainer)
               $(`<div>${translation.value}</div>`).appendTo(translationRow)
            }

            $(`<label class="displayFlex alignCenter mt-2">examples</label>`).appendTo(senseContainer)
            let examples = translationgroup.children.filter(e => e.name == "example")
            if (examples.length) {
               for (example of examples) {
                  let exampleRow = $(`<div class="exampleRow pl-8"></div>`).appendTo(senseContainer)
                  $(`<div>${example.value}</div>`).appendTo(exampleRow)
                  for (example_translation of example.children.filter(e => e.name == "example_translation")) {
                     let example_translationRow = $(`<div class="example_translationRow displayFlex alignCenter pl-8"></div>`).appendTo(exampleRow)
                     $(`<div>${example_translation.value}</div>`).appendTo(example_translationRow)
                  }
               }
            } else {
               $(`<div class="grey-text ml-16">no example translations</div>`).appendTo(senseContainer)
            }

            $(`<label class="displayFlex alignCenter mt-2">translation register</label>`).appendTo(senseContainer)
            let translation_register = translationgroup.children.find(child => child.name == "translation_register")
            if (translation_register) {
               $(`<div class="grey-text ml-8">${translation_register.value}</div>`).appendTo(senseContainer)
            } else {
               $(`<div class="grey-text ml-8">no translation register</div>`).appendTo(senseContainer)
            }

            $(`<label class="displayFlex alignCenter mt-2">translation indicator</label>`).appendTo(senseContainer)
            let translation_indicator = translationgroup.children.find(child => child.name == "translation_indicator")
            if (translation_indicator) {
               $(`<div class="grey-text ml-8">${translation_indicator.value}</div>`).appendTo(senseContainer)
            } else {
               $(`<div class="grey-text ml-8">no translation indicator</div>`).appendTo(senseContainer)
            }
         } else {
            $(`<div class="grey-text ml-8">no translations</div>`).appendTo(senseContainer)
         }

         $(`<label class="displayFlex alignCenter mt-2">xrefs</label>`).appendTo(senseContainer)
         let xrefs = sense.children.filter(e => e.name == "xref")
         if (xrefs.length) {
            for (xref of xrefs) {
               let xrefRow = $(`<div class="xrefRow displayFlex alignCenter pl-8"></div>`).appendTo(senseContainer)
               $(`<div class="grey-text">${xref.value}</div>`).appendTo(xrefRow)
            }
         } else {
            $(`<div class="grey-text ml-16">no xrefs</div>`).appendTo(senseContainer)
         }

      }
   },

   _renderTextBox: function(element, parentNode, label = "", readOnly = true) {
      let inputDiv = $(`<div class="input-field el_${element.name}""></div`).appendTo(parentNode)
      $(`<label>${label}</label>`).appendTo(inputDiv)
      $(`<input ${readOnly? "disabled" : ""}
       value="${element.value}"/>`)
         .appendTo(inputDiv)
         .on("input", this._onInput.bind(this, element))
         .on("change", this.options.onChange)
   },

   _renderSelectBox: function(element, parentNode, options, label = "", readOnly = true) {
      let optionNodes = options.map(option => `<option value="${option}" ${element.value == option ? 'selected' : ''}>${option}</option>`)
      let selectContainer = $(`<div class="el_${element.name}"></div`).appendTo(parentNode)
      $(`<select ${readOnly ? "disabled" : ""}>
           <option ${element.value == "" ? 'selected' : ''}>-not set-</option>
           ${optionNodes}
         </select>`).appendTo(selectContainer)
            .on("change", (evt) => {
               element.value = evt.target.value
               this._validate()
               this.options.onChange()
            })
   },

   _getChildValue: function(parent, childName, defaultValue = "") {
      let child = window.nvhStore.findElement(e => e.name == childName, parent)
      return child ? child.value : defaultValue
   },

   _onInput: function(element, evt) {
      element.value = evt.target.value
      this._validate()
   },

   _validate: function() {
      // TODO
      let wasValid = this.isValid
      this.isValid = $(".el_translation input, .el_example_translation input").filter(function() {
         return this.value == ""
      }).length == 0
      if (wasValid != this.isValid) {
         this.options.onValidChange(this.isValid)
      }
   }
}
