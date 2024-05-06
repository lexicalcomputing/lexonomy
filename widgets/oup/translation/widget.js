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

   _render: function() {
      this.contentNode.empty()
      this._renderHeader()
      this._renderSenses()
      window.initFormSelects(this.contentNode)
   },

   _renderHeader() {
      let register = this._getChildValue(this.entry, "register", "-not set-")
      let domain = this._getChildValue(this.entry, "domain", "-not set-")
      $(`<div class="displayFlex alignCenter" style="gap:10px;">
        <h2>${this.entry.value}</h2>
        <span class="ml-auto"></span>
        <span class="grey-text">register</span>
        <span>${register}</span>
        <span class="grey-text">domain</span>
        <span>${domain}</span>
      </div>`).appendTo(this.contentNode)
   },

   _renderSenses: function() {
      $(`<h3 class="grey-text">Senses</h3>`).appendTo(this.contentNode)
      for (sense of this._getChildElements(this.entry, "sense")) {
         let senseWrapper = $(`<div class="senseWrapper mb-4 ml-6"></div>`).appendTo(this.contentNode)
         let senseHeader = $(`<div class="senseHeader grey lighten-3 pl-4 pr-4"></div>`).appendTo(senseWrapper)
         let senseContainer = $(`<div class="senseContainer grey lighten-4 p-4"></div>`).appendTo(senseWrapper)
         let definition = this._getChildValue(sense, "definition", "-not set-")
         let sense_register = this._getChildValue(sense, "sense_register", "-not set-")
         let sense_domain = this._getChildValue(sense, "sense_domain", "-not set-")
         let translationgroup = window.nvhStore.findElement(e => e.name == "translationgroup", sense)
         $(`<div class="displayFlex alignCenter" style="gap:10px;">
         <h3>${sense.value}</h3>
         <span class="ml-auto"></span>
         <span class="grey-text">register</span>
         <span>${sense_register}</span>
         <span class="grey-text">domain</span>
         <span>${sense_domain}</span>
       </div>`).appendTo(senseHeader)
         $(`<label class="displayFlex alignCenter mt-2">definition</label>`).appendTo(senseContainer)
         $(`<div class="grey-text pl-8">${definition}</div>`).appendTo(senseContainer)

         if (translationgroup) {
            $(`<label class="displayFlex alignCenter mt-2">translations</label>`).appendTo(senseContainer)
            for (translation of this._getChildElements(translationgroup, "translation")) {
               let translationRow = $(`<div class="translationRow displayFlex alignCenter pl-8"></div>`).appendTo(senseContainer)
               this._renderTextBox(translation, translationRow)
               if (!translation.children.find(child => child.name == "translationunit_lexid")) {
                  $(`<button class="btn btn-flat btn-floating ml-2"><i class="material-icons">delete</i></button>`).appendTo(translationRow)
                     .click(this._removeTranslation.bind(this, translation))
               }
            }

            $(`<button class="btn btn-secondary ml-8"><i class="material-icons left">add</i>add translation</button>`).appendTo(senseContainer)
               .click(this._addTranslation.bind(this, sense))

            $(`<label class="displayFlex alignCenter mt-2">examples</label>`).appendTo(senseContainer)
            let examples = this._getChildElements(translationgroup, "example")
            if (examples.length) {
               for (example of examples) {
                  let exampleRow = $(`<div class="exampleRow pl-8"></div>`).appendTo(senseContainer)
                  $(`<div>${example.value}</div>`).appendTo(exampleRow)
                  for (example_translation of example.children.filter(e => e.name == "example_translation")) {
                     let example_translationRow = $(`<div class="example_translationRow displayFlex alignCenter pl-8"></div>`).appendTo(exampleRow)
                     this._renderTextBox(example_translation, example_translationRow)
                     if (!example_translation.children.find(child => child.name == "example_translationunit_lexid")) {
                        $(`<button class="btn btn-flat btn-floating ml-2"><i class="material-icons">delete</i></button>`).appendTo(example_translationRow)
                           .click(this._removeExampleTranslation.bind(this, example_translation))
                     }
                  }
                  $(`<button class="btn btn-secondary ml-16"><i class="material-icons left">add</i>add example translation</button>`).appendTo(senseContainer)
                     .click(this._addExampleTranslation.bind(this, example))
               }
            } else {
               $(`<div class="grey-text ml-16">no example translations</div>`).appendTo(senseContainer)
            }



            $(`<label class="displayFlex alignCenter mt-2">translation register</label>`).appendTo(senseContainer)
            let translationRegisterContainer = $(`<div class="pl-8"></div>`).appendTo(senseContainer)
            let translation_register = this._getChildElement(translationgroup, "translation_register")
            this._renderTranslationRegisterBox(translationgroup, translationRegisterContainer)

            $(`<label class="displayFlex alignCenter mt-2">translation indicator</label>`).appendTo(senseContainer)
            let translation_indicator = this._getChildElement(translationgroup, "translation_indicator")
            if (translation_indicator) {
               $(`<div class="grey-text ml-8">${translation_indicator.value}</div>`).appendTo(senseContainer)
            } else {
               $(`<div class="grey-text ml-8">no translation indicator</div>`).appendTo(senseContainer)
            }
         } else {
            $(`<div class="grey-text ml-8">no translations</div>`).appendTo(senseContainer)
         }
      }
   },

   _renderTextBox: function(element, parentNode, label = "", readOnly = false) {
      let inputDiv = $(`<div class="input-field el_${element.name}""></div`).appendTo(parentNode)
      $(`<label>${label}</label>`).appendTo(inputDiv)
      $(`<input ${readOnly? "disabled" : ""}
       value="${element.value}"/>`)
         .appendTo(inputDiv)
         .on("input", this._onInput.bind(this, element))
         .on("change", this.options.onChange)
   },

   _renderTranslationRegisterBox: function(translationgroup, parentNode,) {
      let translation_register = this._getChildElement(translationgroup, "translation_register")
      let value = translation_register ? translation_register.value : ""
      let optionNodes = this.const.TRANSLATION_REGISTER_OPTIONS.map(option => `<option value="${option}" ${value == option ? 'selected' : ''}>${option}</option>`)
      let selectContainer = $(`<div class="el_translation_register"></div`).appendTo(parentNode)
      $(`<select>
           <option ${value == "" ? 'selected' : ''}>-not set-</option>
           ${optionNodes}
         </select>`).appendTo(selectContainer)
            .on("change", function (translationgroup, evt) {
               let translation_register = this._getChildElement(translationgroup, "translation_register") || this._createChildElement(translationgroup, "translation_register")
               translation_register .value = evt.target.value
               this._validate()
               this.options.onChange()
            }.bind(this, translationgroup))
   },

   _getChildElement(parent, childName){
      return window.nvhStore.findElement(e => e.name == childName, parent)
   },

   _getChildElements(parent, childName){
      return window.nvhStore.findElements(e => e.name == childName, parent)
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

   _getChildValue: function(parent, childName, defaultValue = "") {
      let child = window.nvhStore.findElement(e => e.name == childName, parent)
      return child ? child.value : defaultValue
   },

   _addTranslation(sense) {
      let translationgroup = sense.children.find(child => child.name == "translationgroup")
      if (!translationgroup) {
         translationgroup = {
            name: "translationgroup",
            value: "",
            parent: sense,
            children: []
         }
         sense.children.push(translationgroup)
      }
      translationgroup.children.push({
         name: "translation",
         value: "",
         parent: translationgroup,
         children: []
      })
      this._render()
      this._validate()
      this.options.onChange()
   },

   _removeTranslation(translation) {
      let translationgroup = translation.parent
      translationgroup.children = translationgroup.children.filter(child => child != translation)
      if (!translationgroup.children.lenghth) {
         // remove empty translation group
         translationgroup.parent.children.filter(child => child != translationgroup)
      }
      this._render()
      this._validate()
      this.options.onChange()
   },

   _addExampleTranslation(example) {
      example.children.push({
         name: "example_translation",
         value: "",
         parent: example,
         children: []
      })
      this._render()
      this._validate()
      this.options.onChange()
   },

   _removeExampleTranslation(example_translation) {
      let example = example_translation.parent
      example.children = example.children.filter(child => child != example_translation)
      this._render()
      this._validate()
      this.options.onChange()
   },

   _onInput: function(element, evt) {
      element.value = evt.target.value
      this._validate()
   },

   _validate: function() {
      let wasValid = this.isValid
      this.isValid = $(".el_translation input, .el_example_translation input").filter(function() {
         return this.value == ""
      }).length == 0
      if (wasValid != this.isValid) {
         this.options.onValidChange(this.isValid)
      }
   }
}
