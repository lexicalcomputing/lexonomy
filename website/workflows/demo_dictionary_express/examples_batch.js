{
   texts: {
      en: {
         examples: "Examples",
         example: "Example",
         exampleFlag_no_ok: "wrong",
         exampleFlag_ok: "correct",
         moreExamples: "Show more examples",
         errorNotEnoughOkExamples: `You must select at least one correct examples.`
      }
   },

   editor: function(options) {
      this.expandBy = 10
      this.options = options
      this.node = $(options.node)
      this.entry = options.entry
      this.isValid = null
      this.contentNode = $('<div class="myEditorContentNode"></div>').appendTo(this.node)
      this._render()
      this._validate()
      this.options.onValidChange(true)
   },

   getValue: function() {
      let lexonomyCompleteElement = this._getChildElement(this.entry, "__lexonomy__complete")
      if(this.isValid && !lexonomyCompleteElement) {
         lexonomyCompleteElement = this._createChildElement(this.entry, "__lexonomy__complete")
         lexonomyCompleteElement.value = 1
      }
      if(!this.isValid && lexonomyCompleteElement) {
         this._removeElement(lexonomyCompleteElement)
      }
      return this.entry
   },

   update: function(entry) {
      this.entry = entry
      this._render()
      this._validate()
   },

   destroy: function() {
   },

   _: function(id){
      return this.texts.en[id] ||
         (id.startsWith('postitle_') && id.substring('postitle_'.length)) ||
         id
   },

   _getChildElement: function(parent, childName) {
      return window.nvhStore.findElement(e => e.name == childName, parent)
   },

   _getOrCreateChildElement: function(parent, childName) {
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
         path: parent ? parent.path + "." + childElementName : childElementName,
         value: "",
         parent: parent,
         children: []
      }
      parent.children.push(child)
      return child
   },

   _callOnChange: function() {
      this._validate()
      this.options.onChange()
   },

   _renderErrorMessageBar: function() {
      if(!this.options.readOnly){
         $(`
            <div id="errorMessageBar"
               class="errorMessageBar red lighten-4 pt-2 pb-2 pl-4 pr-4"
               style="display: none;">
               <div id="errorMessage"
                  class="errorMessage">
               </div>
            </div>`).appendTo(this.contentNode)
      }
   },

   _updateErrorMessage: function(error) {
      $("#errorMessage").html(error)
      $("#errorMessageBar").toggle(!!error)
   },

   _render: function() {
      this.disabledAttr = this.options.readOnly ? 'disabled' : ''
      this._hideReadOnlyClass = this.options.readOnly ? 'hide' : ''
      this.contentNode.empty()
      this._renderErrorMessageBar()
      this._renderHeader()
      this._renderExamples()
   },

   _renderHeader: function() {
      let lemma = this._getChildValue(this.entry, "lemma")
      let pos = this._getChildValue(this.entry, "pos")
      let postitle = this._getChildValue(this.entry, "postitle")
      $(`
         <div class="displayFlex alignCenter borderBottom positionRelative">
            <span>
               <h1 class="inlineBlock">${lemma}</h1>
               <span class="ml-2 grey-text">${postitle}</span>
            </span>
         </div>`).appendTo(this.contentNode)
   },

   _renderExamples: function() {
      let exampleContainer = $(`<div class="examples"></div>`).appendTo(this.contentNode)
      $(`<h3>${this._("examples")}</h3>`).appendTo(exampleContainer)
      let examples = this._getChildElements(this.entry, "example")
      let expandUntil = Math.max(this.expandBy-1, examples.findLastIndex((el) => this._getChildValue(el, "flag") != 'no_ok'))
      if(examples.length){

         examples.forEach((example, idx) => {
            let flag = this._getChildValue(example, "flag", "no_ok")
            let exampleNode = $(`
               <div class="example example_${flag} card-panel ml-8 ${this.options.readOnly ? '' : 'mr-16'} mb-8 positionRelative ${idx > expandUntil ? 'exampleCollapsed' : ''}">
                  <span class="exampleNum">${idx + 1}.</span>
                  <div class="displayFlex alignStart">
                     <div class="exampleText">
                        ${example.value}
                     </div>
                  </div>
                  <div class="displayFlex alignStart">
                     <label class="mr-4">
                        <input type="radio"
                           id="example_${idx}_rb_no_ok"
                           name="example_${idx}_rb"
                           value="no_ok"
                           ${this.disabledAttr}
                           ${flag == "no_ok" ? 'checked' : ''}/>
                        <span>${this._("exampleFlag_no_ok")}</span>
                     </label>
                     <label class="mr-4">
                        <input type="radio"
                           id="example_${idx}_rb_ok"
                           name="example_${idx}_rb"
                           value="ok"
                           ${this.disabledAttr}
                           ${flag == "ok" ? 'checked' : ''}/>
                        <span>${this._("exampleFlag_ok")}</span>
                     </label>
                  </div>
               </div>`).appendTo(exampleContainer)
            exampleNode.find("input[name=\"example_" + idx + "_rb\"]").on("change", this._onFlagChange.bind(this, example))
         })
         $(`<button class="moreExamplesButton btn ml-8 ${this.options.readOnly ? 'hide' : ''}">
               <i class="material-icons left">add</i>
               ${this._("moreExamples")}
            </button>`)
               .appendTo(exampleContainer)
               .click(this._onMoreExamplesClick.bind(this))
      } else {
         $(`<h2 class="grey-text center-align pt-8 ">This entry does not contain any examples</h2>`).appendTo(exampleContainer)
      }
   },

   _onMoreExamplesClick: function(evt) {
      $('.examples .exampleCollapsed').slice(0, this.expandBy).toggleClass("exampleCollapsed")
   },

   _onFlagChange: function(example, evt) {
      if(!evt.target.checked) return // the radio button being unselected
      let flagElement = this._getOrCreateChildElement(example, "flag")
      flagElement.value = evt.target.value
      $(evt.target).closest(".example").removeClass("example_no_ok example_ok").addClass("example_" + evt.target.value)
      this._validate()
      this._callOnChange()
   },

   _validate: function() {
      let error = ""
      let examples = $(".myEditorContentNode .example").toArray()
      if(examples.length
            && examples.filter(example => {
               return $(example).find("input[type='radio'][value='ok']:checked").length
            }).length == 0
       ){
           error = this._("errorNotEnoughOkExamples")
      }

      this.isValid = !this.error
      this._updateErrorMessage(error)
   }
}