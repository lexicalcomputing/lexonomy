class NVHFormattingEditorClass {
   constructor() {
      this.reset()
      this.initilaizeVisibleSections()
      observable(this);
   }

   reset() {
      this.currentLayout = {
         schema: null,
         history: null,
      }
      this.layout = {
         desktop: null,
         tablet: null,
         mobile: null,
         pdf: null,
      }
      this.isSaving = false
      this.data = {
         draggedLayoutContainer: null,
         hoveredLayoutContainer: null,
         selectedLayoutContainer: null,
         activeLayout: "desktop" /*desktop, tablet, mobile, pdf*/
      }
   }

   updateEditor() {
      this.trigger("updateEditor");
   }

   toggleSection(sectionName){
      this.visibleSections[sectionName] = !this.visibleSections[sectionName]
      window.setCookie("formattingEditorVisibleSections", Object.entries(this.visibleSections)
           .filter(([key, value]) => value)
           .map(([key]) => key)
           .join(","))
      this.trigger("updateEditor")
   }

   saveSchemas(){
      this.isSaving = true
      this.trigger("isSavingChanged")
      let layoutConfig = {}
      for (let device of ["desktop", "tablet", "mobile", "pdf"]) {
         let schema = structuredClone(this.layout[device].schema)
         this.removeParentReferenceFromSchema(schema)
         layoutConfig[device] = {
            schema: schema,
            configured: this.layout[device].configured
         }
      }
      layoutConfig.desktop.configured = true;
      window.store.updateDictionaryConfig("formatting", {layout: layoutConfig})
         .always(() => {
            this.isSaving = false
            this.trigger("isSavingChanged")
         })
   }

   generateSchemaFromStructure(){
      let addElementAndChildren = (element, parent=null, level) => {
         let schemaElement = this.createSchemaElement(element.path, parent)
         if(element.children?.length){  // element is just group, add element with its value (e.g. sense group with first child sense)
            this.createSchemaElement(element.path, schemaElement)
         }
         element.children.forEach(child => {
            if(!this.isMarkupType(child.path)){
               addElementAndChildren(child, schemaElement, level + 1)
            }
         })
         return schemaElement
      }
      return addElementAndChildren(window.store.schema.schema, null, 0)
   }

   changeLayoutSchema() {
      if (window.innerWidth < 768) {
         this.setClosestConfiguredLayout("mobile");
      } else if (window.innerWidth < 1024) {
         this.setClosestConfiguredLayout("tablet");
      } else {
         this.setClosestConfiguredLayout("desktop");
      }
   }

   setClosestConfiguredLayout(activeLayout) {
      if (this.data.activeLayout === activeLayout) {
         return
      }
      this.data.activeLayout = activeLayout;
      let mobileConfigured = !!this.layout.mobile.configured;
      let tabletConfigured = !!this.layout.tablet.configured;
      if (activeLayout === "mobile") {
         if (mobileConfigured) {
            this.currentLayout = this.layout.mobile;
         } else if (tabletConfigured) {
            this.currentLayout = this.layout.tablet;
         } else {
            this.currentLayout = this.layout.desktop;
         }
      } else if (activeLayout === "tablet") {
         if (tabletConfigured) {
            this.currentLayout = this.layout.tablet;
         } else {
            this.currentLayout = this.layout.desktop;
         }
      } else {
         this.currentLayout = this.layout.desktop;
      }
   }

   async createPDF() {
      return window.connection.post({
         url: `${window.API_URL}createPDF`,
         data: {},
         failMessage: "Could not create PDF"
      })
   }

   async clearHtmlFile() {
      return window.connection.post({
         url: `${window.API_URL}clearHtmlFile`,
         data: {},
         failMessage: "Could not clear HTML file"
      })
   }

   async appendToHtmlFile(html_string) {
      return window.connection.post({
         url: `${window.API_URL}appendToHtmlFile`,
         data: {
            html_string: html_string,
         },
         failMessage: "Could not append to HTML file"
      })
   }

   async loadEntries() {
      return window.connection.post({
         url: `${window.API_URL}${window.store.data.dictId}/entriesread.json`,
         failMessage: "Entries could not be loaded."
      })
   }

   async stringifyAllEntries(exportedEntries) {
      await this.clearHtmlFile();

      const transferSize = 700000;
      let entriesList = await this.loadEntries();
      exportedEntries.inProgress = true;
      exportedEntries.total = entriesList.entriesList.length;
      exportedEntries.exported = 0;

      let htmlWrapper = "<div>";

      for (let idx = 0; idx < entriesList.entriesList.length; idx++) {
         let entryJson = window.nvhStore.nvhToJson(entriesList.entriesList[idx].nvh);
         htmlWrapper += this.stringifyEntry(entryJson);
         htmlWrapper += `<div style="height: 1px; width: 980px; background-color: grey; margin: 2px 0"></div>`
         if (htmlWrapper.length > transferSize) { // Do not send all entries at once to backend, set some limit
            exportedEntries.exported = idx;
            this.trigger("updateToolbar");
            await this.appendToHtmlFile(htmlWrapper);
            htmlWrapper = ""
         }
      }
      exportedEntries.inProgress = false;
      exportedEntries.total = 0;
      exportedEntries.exported = 0;
      this.trigger("updateToolbar");

      htmlWrapper += "</div>"
      await this.appendToHtmlFile(htmlWrapper);
   }

   stringifyEntry(entry) {
      let schema = this.layout.pdf.configured ? this.layout.pdf.schema : this.layout.desktop.schema;
      let entryHTML = this.getEntryHTML(schema.children[0], entry);
      return entryHTML;
   }

   getEntryHTML(schema, element) {
      const item = document.createElement('entry-styled-element');
      riot.mount(item, { schema: schema, element: element, maxPossibleWidth: "980px" });
      return item.innerHTML;
   }

   getChildIndex(schema){
      if(schema.parent){
         return schema.parent.children.findIndex(child => child == schema)
      }
      return -1
   }

   resetSchema() {
      this.initializeSchema()
      this.trigger("updateEditor")
   }

   initializeSchema() {
      this.currentLayout.schema = this.createSchema()
      this.data.selectedLayoutContainer = null
   }

   initilaizeVisibleSections(){
      let cookie = window.getCookie("formattingEditorVisibleSections")
      if(cookie){
         let sections  = cookie.split(",")
         this.visibleSections = {
            elements: sections.includes("elements"),
            style: sections.includes("style"),
            editing: sections.includes("editing"),
            example: sections.includes("example")
         }
      } else {
         this.visibleSections = {
            elements: true,
            style: false,
            editing: true,
            example: true
         }
      }
   }

   initLayout(){
      let layout = window.store.data.config.formatting.layout ? structuredClone(window.store.data.config.formatting.layout) : {}
      layout.desktop ||= {}
      layout.desktop.schema ||= this.generateSchemaFromStructure()
      ;["desktop", "tablet", "mobile", "pdf"].forEach(device => {
         let deviceLayout = layout[device] || {schema: this.createSchema()}
         this.addParentReferenceToSchema(deviceLayout.schema)
         this.addStylesToSchema(deviceLayout.schema)
         this.layout[device] = {
            configured: deviceLayout.configured ?? false,
            schema: deviceLayout.schema,
            history: {
               index: 0,
               schema: [structuredClone(deviceLayout.schema)]
            }
         }
      })
      this.layout.desktop.configured = true
      this.currentLayout = this.layout.desktop
   }

   addParentReferenceToSchema(schema, parent=null){
      schema.parent = parent
      schema.children.forEach(child => {
         this.addParentReferenceToSchema(child, schema)
      })
   }

   removeParentReferenceFromSchema(schema){
      delete schema.parent
      schema.children.forEach(this.removeParentReferenceFromSchema.bind(this))
   }

   addStylesToSchema(schema){
      if(!schema.styles){
         schema.styles = {}
      }
      schema.children.forEach(child => {
         this.addStylesToSchema(child)
      })
   }

   createSchema() {
      return this.createSchemaElement(window.store.schema.getRoot().path)
   }

   createSchemaElement(elementPath, parent=null, index=null){
      let elementName = elementPath ? elementPath.split(".").pop() : ""
      let newElement = {
         orientation: "column",
         parent: null,
         content: {
            name: elementName,
            path: elementPath
         },
         styles: {},
         children: []
      }
      if(parent){
         newElement.parent = parent
         if(index != null){
            parent.children.splice(index, 0, newElement);
         } else {
            parent.children.push(newElement)
         }
      }
      return newElement
   }

   changeActiveLayout(layoutName){
      this.data.activeLayout = layoutName
      this.data.selectedLayoutContainer = null
      this.currentLayout = this.layout[layoutName]
      this.trigger("updateEditor")
   }

   undoSchema() {
      if (this.currentLayout.history.index > 0) {
         this.goToHistory(-1)
      }
   }

   redoSchema() {
      if (this.currentLayout.history.index < this.currentLayout.history.schema.length - 1) {
         this.goToHistory(1)
      }
   }

   resetSchemaStyles(schema, type, path){
      let styles = this.getStyles(schema, type, path)
      for (const key in styles) {
         delete styles[key]
      }
      this.trigger("updateEditor")
   }

   goToHistory(index) {
      let history = this.currentLayout.history
      history.index += index;
      this.currentLayout.schema = structuredClone(history.schema.at(history.index));
      this.data.selectedLayoutContainer = null;
      this.trigger("updateEditor")
   }

   selectLayoutContainer(selectedLayoutContainer) {
      if(this.data.selectedLayoutContainer != selectedLayoutContainer){
         this.data.selectedLayoutContainer = selectedLayoutContainer
         this.trigger("selectedLayoutContainerChange")
      }
   }

   isChildObjectOfParent(childObject, parent) {
      if (childObject.content.path === parent && childObject.children.length
         || !childObject.content.path.includes(parent) && childObject.content.path) {
         return false;
      }

      for (let child of childObject.children) {
         if (!this.isChildObjectOfParent(child, parent)) {
            return false;
         }
      }
      return true;
   }

   addElement(parent, elementPath, index) {
      let newElement = this.createSchemaElement(elementPath, parent, index)
      this.data.selectedLayoutContainer = newElement;
      this.trigger("updateEditor")
      return newElement
   }

   deleteElement(element) {
      if(element.parent){
         element.parent.children = element.parent.children.filter(child => child != element)
         if(this.data.draggedElement == element){
            this.stopElementDragging()
         }
         this.trigger("updateEditor")
      }
   }

   moveChildToAnotherParent(element, newParent, position=0){
      if(element.parent){ // if element was dragged from element list on the left, it has no parent
         let idx = element.parent.children.indexOf(element)
         element.parent.children.splice(idx, 1)
      }
      element.parent = newParent
      if(position === null){
         newParent.children.push(element)
      } else {
         newParent.children.splice(position, 0, element)
      }
      this.trigger("updateEditor")
      //this.addStateToHistory()
   }

   toggleSchemaOrientation(schema){
      schema.orientation === "column" ? schema.orientation = "row" : schema.orientation = "column"
      this.trigger("updateEditor")
   }

   duplicateSchema(schema){
      let copiedElement = structuredClone(schema);
      copiedElement.parent = schema.parent
      schema.parent.children.splice(this.getChildIndex(schema) + 1, 0, copiedElement);
      this.data.hoveredLayoutContainer = null;
      this.trigger("updateEditor")
   }

   startElementDragging(element){
      this.data.draggedElement = element
      this.trigger("onDndStart")
   }

   stopElementDragging(){
      this.data.draggedElement = null
      this.trigger("onDndStop")
   }

   setHoveredLayoutContainer(schema){
      if (this.data.hoveredLayoutContainer != schema) {
         this.data.hoveredLayoutContainer = schema
         this.trigger("updateEditor")
      }
   }

   forEachElement(callback, element){
      element = element || this.currentLayout?.schema
      if(element){
         callback(element)
         element.children.forEach(this.forEachElement.bind(this, callback))
      }
   }

   isMarkupType(path) {
      if (!path) {
         return false;
      }
      let config = window.nvhStore.getElementConfig(path);
      return config?.type === "markup";
   }

   isEveryChildDescendantOf(element, parent){
      let list = []
      this.forEachElement(element => {
         element.content.path && list.push(element.content.path)
      }, element)
      return !list.length || list.every(path => path.startsWith(parent.content.path))
   }

   isDescendantOf(child, parent){
      //return !childPath || (childPath != parentPath && childPath.startsWith(parentPath))
      let childPath = child.content.path
      let parentPath = parent.content.path
      return !childPath
            || (childPath != parentPath && childPath.startsWith(parentPath))
            || (childPath == parentPath && !child.children.length && parent.children.length)
   }

   findFirstNonContainerAncestor(schema){
      let currentSchema = schema
      while(!currentSchema.content.path && currentSchema.parent){
         currentSchema = currentSchema.parent
      }
      return currentSchema
   }

   canHaveChildren(schema, childPath){
      //return !schema.content.path || window.store.schema.getElementByPath(schema.content.path).children.length
            //TODO and maybe limit each child only one time?
      //      empty container
      if(schema.content.path){
         let children = window.store.schema.getElementByPath(schema.content.path)?.children
         if(!children?.length){
            return false
         }
         if(childPath){
            // can have specific child?
            return !!children.find(child => child.path == childPath)
         }
      }
      return true
   }

   areSchemasEquals(schema1, schema2){
      return (schema1 === schema2)
         || (schema1 instanceof Object
               && schema2 instanceof Object // if they are not strictly equal, they both need to be Objects
               && Object.keys(schema1).every(key => {
                  return key == "parent"
                        || (key == "children"
                                 && schema1.length == schema2.length
                                 && schema1.children.every((child, idx) => this.areSchemasEquals(schema1.children[idx], schema2.children[idx])))
                        || (key != "children"
                                 && window.objectEquals(schema1[key], schema2[key]))
                  })
            )
   }

   hasElementUrlChild(path) {
      return window.store.schema.getElementByPath(path)?.children.some(child => {
         return window.nvhStore.getElementConfig(child.path)?.type == "url"
      })
   }

   getElementMarkupUrl(markupElement){
      return markupElement?.children.find(child => window.nvhStore.getElementConfig(child.path)?.type === "url")?.value || null
   }

   getElementMarkupChildren(schema){
      let config = window.nvhStore.getElementConfig(schema.content.path)
      if(!config){
         return []
      }
      return config.children.filter(child => {
         return child.type == "markup"
      })
   }

   getDirectMarkupChildren(path) {
      let result = [];
      if (!path || !window.store.schema.getElementByPath(path)) {
         return result;
      }
      for (let child of window.store.schema.getElementByPath(path).children) {
         let config = window.nvhStore.getElementConfig(child.path);
         if (config?.type === "markup") {
            result.push({ name: child.name, path: child.path, color: window.nvhStore.getElementColor(child.path) });
         }
      }
      return result;
   }

   getStyles(schema, type="element", path=""){
      if(!schema.styles){
         schema.styles = {}
      }
      if(!schema.styles[type]){
         schema.styles[type] = {}
      }
      if(path && type == "markup"){
         if(!schema.styles[type][path]){
            schema.styles[type][path] = {}
         }
         return schema.styles[type][path]
      }
      return schema.styles[type]
   }

   createMarkupStyles(path) {
      let markupChildren = this.getDirectMarkupChildren(path);
      let result = [];
      for (let child of markupChildren) {
         result.push({ name: child.name, path: child.path, styles: {} });
      }
      return result;
   }

   getColorLightVersion(colorHex, coef=0.85) {
      if (!colorHex || ![4, 7, 9,].includes(colorHex.length)) { // #bbb, #bbbbbb, #bbbbbb10
         return "transparent";
      }
      colorHex = colorHex.replace(/^#/, "")
      let hasAlpha = colorHex.length == 8
      if(colorHex.length == 3) { //  3 digits hex to 6 digits
         colorHex = colorHex.split("")
               .map(c => c + c)
               .join("")
      }

      let red = parseInt(colorHex.slice(0, 2), 16)
      let green = parseInt(colorHex.slice(2, 4), 16)
      let blue = parseInt(colorHex.slice(4, 6), 16)
      let alpha = hasAlpha ? parseInt(colorHex.slice(6, 8), 16) : 255

      let lighten = c => Math.max(0,Math.min(255, Math.round(c + (255 - c) * coef)))
            .toString(16)
            .padStart(2, "0")

      let newRed = lighten(red)
      let newGreen = lighten(green)
      let newBlue = lighten(blue)
      let newAlpha = hasAlpha ? alpha.toString(16).padStart(2, "0") : "";

      return `#${newRed}${newGreen}${newBlue}${newAlpha}`;
   }

   getIcon(iconItem) {
      return {
         "link": "🔗", "speaker": "🔊", "load-speaker": "📢"
         , "music-note": "♫", "camera": "📹", "film-frames": "🎞"
         , "film-projector": "📽", "movie-camera": "🎥", "framed-picture": "🖼"
      }[iconItem];
   }

   getUnicodeIcon(unicodeIcon) {
      return unicodeIcon ? unicodeIcon : "";
   }

   isElementNonExisting(path) {
      return path && !window.nvhStore.getElementConfig(path);
   }

   getMaxPossibleWidth() {
      switch (this.data.activeLayout) {
         case "tablet":
            return 1024;
         case "pdf":
            return 980;
         case "mobile":
            return 768;
         default:
            // 2 * 5px padding + 2 * 3 px of margin = 16 px
            return window.innerWidth * 0.8 - 16
      }
   }

   getCssRules(schema, type, path) {
      let styles = this.getStyles(schema, type, path)
      let result_css = ""
      for (let [option, value] of Object.entries(styles)) {
         if (!value) {
            continue;
         }
         if (["leftPunc", "rightPunc",
            "border-color", "border-width", "container-width", "label-text-value",
            "show-label-before", "custom-css", "text-value", "applyURL", "allow-html"].includes(option)) {
            continue;
         }
         if (["border-radius", "padding-left", "padding-right", "padding-bottom",
              "padding-top", "margin-left", "margin-top", "margin-right",
              "margin-bottom", "max-height", "font-size"].includes(option)) {
            value = value + "px";
         } else if (option === "box-shadow") {
            value = value + "px " + value + "px " + value + "px " + "grey";
         } else if (option === "text-decoration") {
            if(!styles["text-decoration"]){
               continue
            }
            value = styles["text-decoration"].join(" ");
         } else if (option === "border") {
            let borderColor = styles?.["border-color"] || "black";
            let borderWidth = !styles["border-width"] ? "1px" : styles["border-width"] + "px";
            value = borderWidth + " " + value + " " + borderColor;
         } else if (option === "container-width-unit") {
            if (styles["container-width"]) {
               if (styles[option] === "px") {
                  option = "width";
                  value = Math.min(this.getElementMaxWidth(schema), parseInt(styles["container-width"])) + "px"
               } else if (styles[option] === "%") {
                  if (parseInt(styles["container-width"]) >= 100) {
                     styles["container-width"] = "100";
                  }
                  option = "width";
                  value = `${(parseInt(styles["container-width"]) / 100) * this.getElementMaxWidth(schema)}` + "px";
               } else {
                  continue;
               }
            } else {
               continue;
            }
         } else if (option === "max-width") {
            value = "min(" + styles["max-width"] + "px" + "," + "100%)";
         } else if (option == "direction" && value == "default"){
            continue
         }
         result_css += option + ":" + value + ";";
      }
      if(!schema.parent && type == "element" && (!styles.direction || styles.direction == "default")){
         // add dictionary direction to the root element
         result_css += "direction:" + (window.store.data.config.ident.direction || "ltr") + ";"
      }
      if (this.isStringCssValid(styles) && styles["custom-css"]) {
         result_css += styles["custom-css"] + ";";
      }

      return result_css;
   }

   getElementMaxWidth(schema){
      let maxWidth = this.getMaxPossibleWidth()
      let tmp = schema
      while (tmp){
         maxWidth -= 6  // Width needs to be reduced by 2 * 3px of margin at each nested level
         if(tmp.orientation == "row"){
            maxWidth -= 6 * tmp.children.length
         }
         tmp = tmp.parent
      }

      return maxWidth
   }

   isStringCssValid(styles) {
      let customStyles = styles?.["custom-css"]
      if (!customStyles) {
         return true
      }

      customStyles = customStyles.trimEnd().split(";").filter(e => e.length)
      let textContent = ""
      for (let i = 0; i < customStyles.length; i++) {
         textContent += `tmp${i}{${customStyles[i]};}`
      }
      const style = document.createElement('style')
      style.textContent = textContent

      document.head.appendChild(style)
      let cssRules = style.sheet.cssRules
      for (let i = 0; i < cssRules.length; i++) {
         if (!cssRules[i].style.length) {
            return false
         }
      }
      document.head.removeChild(style)
      return true
   }

   isLayoutContainerHovered(layoutContainer) {
      return this.data.hoveredLayoutContainer === layoutContainer;
   }

   isLayoutContainerActive(layoutContainer) {
      return this.data.selectedLayoutContainer === layoutContainer;
   }

   isLayoutContainerDragged(layoutContainer) {
      return this.data.draggedLayoutContainer === layoutContainer;
   }

   hasElementInAncestors(schema, path){
      let actualElement = schema.parent
      while (actualElement){
         if(actualElement.content.path == path){
            return true
         }
         actualElement = actualElement.parent
      }
      return false
   }
}

window.nvhFormattingEditor = new NVHFormattingEditorClass();
