class NVHFormattingEditorClass {
  constructor() {
    this.formattingEditorComponent = null,
    this.elementsSchema = null,
    this.global = this.initializeGlobalAttributes(),
    this.currentLayout = {
      schema: null,
      elements: null,
      history: null,
    }
    this.layout = {
      desktop: null,
      tablet: null,
      mobile: null,
      pdf: null,
    }
    observable(this);
  }

  initializeGlobalAttributes() {
    return {
      canBeRemovedIfHovered: true, /*remove only the deepest hovered "placeholder", the other ones should stay as they are*/
      canBeDropped: true, /*drop element only to deepest hovered "placeholder"*/
      canBeDragged: true, /*drag only the deepest hovered "placeholder"*/
      draggedElementFullName: "",
      draggedPlaceholder: null,
      dropInfo: {
        wasSuccessful: false,
        index: null,
      },
      canOpenActionPanel: true, /*open only action panel of the deepest hovered "placeholder"*/
      selectedPlaceholderAreaFullName: "",
      selectedPlaceholderFullName: "",
      selectedPlaceholder: null,
      selectedPlaceholderParentAreaFullName: "",
      parent: null,
      activeLayout: "desktop", /*desktop, tablet, mobile, pdf*/
    }
  }

  changeLayoutSchema() {
    if (window.innerWidth < 440) {
      if (window.nvhFormattingEditor.global.activeLayout !== "mobile") {
        window.nvhFormattingEditor.global.activeLayout = "mobile";
        window.nvhFormattingEditor.currentLayout = window.nvhFormattingEditor.layout.mobile;
      }
    } else if (window.innerWidth < 1020) {
      if (window.nvhFormattingEditor.global.activeLayout !== "tablet") {
        window.nvhFormattingEditor.global.activeLayout = "tablet";
        window.nvhFormattingEditor.currentLayout = window.nvhFormattingEditor.layout.tablet;
      }
    } else {
      if (window.nvhFormattingEditor.global.activeLayout !== "desktop") {
        window.nvhFormattingEditor.global.activeLayout = "desktop";
        window.nvhFormattingEditor.currentLayout = window.nvhFormattingEditor.layout.desktop;
      }
    }
  }

  async createPDF(html_string) {
    return window.connection.post({
       url: `${window.API_URL}createPDF`,
       data: {
          html_string: html_string,
       },
       failMessage: "Could not create PDF"
    })
  }

  async parseAllEntries() {
    let entriesList = await window.store.loadEntryList();
    let htmlWrapper = "<div>";
    for (let entry of entriesList.entries) {
      htmlWrapper += await this.parseEntry(entry.id);
      htmlWrapper += `<div style="height: 1px; width: 980px; background-color: grey; margin: 2px 0"></div>`
    }
    htmlWrapper += "</div>"
    return htmlWrapper;
  }

  async parseEntry(entryId) {
    window.store.changeEntryId(entryId);
    let entry = await window.store.loadEntry();
    let entryObject = Object.entries(JSON.parse(entry.json).entry[0]);

    let parsedEntry = this.getEntryStructure(entryObject, "entry");
    let schema = window.nvhFormattingEditor.layout.pdf.schema;
    
    let entryHTML = this.getEntryHTML(schema.children[0], parsedEntry);

    return entryHTML;
  }

  getEntryStructure(entry, fullName) {
    let objectHolder = {
      fullName: fullName,
      value: "",
      children: []
    };
    for (let element of entry) {
      if (element[0] === "_name") {
        continue;
      } else if (element[0] === "_value") {
        objectHolder.value = element[1];
      } else {
        for (let childHolder of element[1]) {
          let child = this.getEntryStructure(Object.entries(childHolder), element[0]);
          objectHolder.children.push(child);
        }
      }
    }
    return objectHolder;
  }

  getEntryHTML(schema, entry) {
    if (schema.children.length === 0 && schema.content.fullName === entry.fullName) {
      let entryStyle = entry.fullName === "entry" ? " color: red; font-weight: bold; font-size: 30px;" : ""
      return `<div style="padding: 3px;${entryStyle}">${entry.value}</div>`;
    }

    let stringHTML = `<div style="display: flex; flex-direction: ${schema.orientation}; flex-wrap: wrap;">`;
    for (let childSchema of schema.children) {
      if (childSchema.content.fullName === "") {
        stringHTML += this.getEntryHTML(childSchema, entry);
      } else if (childSchema.content.areaFullName === schema.content.areaFullName) {
        stringHTML += this.getEntryHTML(childSchema, entry);
      } else {
        stringHTML += `<div style="display: flex; flex-direction: ${childSchema.orientation}; flex-wrap: wrap;">`;
        for (let childEntry of this.getEntryChildren(entry, [])) {
          if (childSchema.content.fullName === childEntry.fullName) {
            stringHTML += this.getEntryHTML(childSchema, childEntry);
          }
        }
        stringHTML += `</div>`;
      }
    }
    stringHTML += `</div>`;
    return stringHTML;
  }

  /*This allows displaying non-direct children*/
  getEntryChildren(entry, resultChildren) {
    for (let child of entry.children) {
      this.getEntryChildren(child, resultChildren);
      resultChildren.push(child);
    }
    return resultChildren;
  }

  resetSchema() {
    window.nvhFormattingEditor.initializeSchema();
    window.nvhFormattingEditor.formattingEditorComponent.update();
  }

  initializeSchema() {
    window.nvhFormattingEditor.currentLayout.schema = window.nvhFormattingEditor.createSchema();
    window.nvhFormattingEditor.global.selectedPlaceholderAreaFullName = "";
    window.nvhFormattingEditor.global.selectedPlaceholderFullName = "";
    window.nvhFormattingEditor.global.selectedPlaceholder = null;
    window.nvhFormattingEditor.global.selectedPlaceholderParentAreaFullName = "";
  }

  initializeSchemas() {
    let initialSchema = window.nvhFormattingEditor.createSchema();
    let defaultElements = window.store.data.config.formatting.elements;

    window.nvhFormattingEditor.layout.desktop = {
      schema: JSON.parse(JSON.stringify(initialSchema)),
      elements: JSON.parse(JSON.stringify(defaultElements)),
      history: {
        index: 0,
        schema: [JSON.parse(JSON.stringify(initialSchema))],
        elements: [JSON.parse(JSON.stringify(defaultElements))],
      }
    }
    window.nvhFormattingEditor.layout.tablet = {
      schema: JSON.parse(JSON.stringify(initialSchema)),
      elements: JSON.parse(JSON.stringify(defaultElements)),
      history: {
        index: 0,
        schema: [JSON.parse(JSON.stringify(initialSchema))],
        elements: [JSON.parse(JSON.stringify(defaultElements))],
      }
    }
    window.nvhFormattingEditor.layout.mobile = {
      schema: JSON.parse(JSON.stringify(initialSchema)),
      elements: JSON.parse(JSON.stringify(defaultElements)),
      history: {
        index: 0,
        schema: [JSON.parse(JSON.stringify(initialSchema))],
        elements: [JSON.parse(JSON.stringify(defaultElements))],
      }
    }
    window.nvhFormattingEditor.layout.pdf = {
      schema: JSON.parse(JSON.stringify(initialSchema)),
      elements: JSON.parse(JSON.stringify(defaultElements)),
      history: {
        index: 0,
        schema: [JSON.parse(JSON.stringify(initialSchema))],
        elements: [JSON.parse(JSON.stringify(defaultElements))],
      }
    }
    window.nvhFormattingEditor.global.selectedPlaceholderAreaFullName = "";
    window.nvhFormattingEditor.global.selectedPlaceholderFullName = "";
    window.nvhFormattingEditor.global.selectedPlaceholder = null;
    window.nvhFormattingEditor.global.selectedPlaceholderParentAreaFullName = "";
  }

  createSchema() {
    let schema = {
      orientation: "column",
      children: [
        {
          status: {
            isActive: false,
            isDragged: false,
          },
          orientation: "column",
          type: "placeholder",
          content: {
            name: "entry",
            fullName: "entry",
            area: "entry",
            areaFullName: "entry",
            color: window.nvhStore.getElementColor("entry"),
            canHaveChildren: true,
          },
          children: [],
        }
      ]
    }
    return schema;
  }

  clearStatuses(state) {
    if (state === null) {
      return;
    }
    Array.from(state.children).map(child => this.clearStatuses(child));
    state.children.map(child => {
      child.status.isActive = false;
      child.status.isHovered = false;
      child.status.isDragged = false;
    });
  }

  undoSchema() {
    if (window.nvhFormattingEditor.currentLayout.history.index > 0) {
      window.nvhFormattingEditor.currentLayout.history.index -= 1;
      window.nvhFormattingEditor.currentLayout.schema = JSON.parse(JSON.stringify(window.nvhFormattingEditor.currentLayout.history.schema.at(window.nvhFormattingEditor.currentLayout.history.index)));
      window.nvhFormattingEditor.currentLayout.elements = JSON.parse(JSON.stringify(window.nvhFormattingEditor.currentLayout.history.elements.at(window.nvhFormattingEditor.currentLayout.history.index)));
      window.nvhFormattingEditor.clearStatuses(window.nvhFormattingEditor.currentLayout.schema);
      window.nvhFormattingEditor.global.selectedPlaceholderAreaFullName = "";
      window.nvhFormattingEditor.global.selectedPlaceholderFullName = "";
      window.nvhFormattingEditor.global.selectedPlaceholder = null;
      window.nvhFormattingEditor.global.selectedPlaceholderParentAreaFullName = "";
      window.nvhFormattingEditor.formattingEditorComponent.update();
    }
  }

  redoSchema() {
    if (window.nvhFormattingEditor.currentLayout.history.index < window.nvhFormattingEditor.currentLayout.history.schema.length - 1) {
      window.nvhFormattingEditor.currentLayout.history.index += 1;
      window.nvhFormattingEditor.currentLayout.schema = JSON.parse(JSON.stringify(window.nvhFormattingEditor.currentLayout.history.schema.at(window.nvhFormattingEditor.currentLayout.history.index)));
      window.nvhFormattingEditor.currentLayout.elements = JSON.parse(JSON.stringify(window.nvhFormattingEditor.currentLayout.history.elements.at(window.nvhFormattingEditor.currentLayout.history.index)));
      window.nvhFormattingEditor.clearStatuses(window.nvhFormattingEditor.currentLayout.schema);
      window.nvhFormattingEditor.global.selectedPlaceholderAreaFullName = "";
      window.nvhFormattingEditor.global.selectedPlaceholderFullName = "";
      window.nvhFormattingEditor.global.selectedPlaceholder = null;
      window.nvhFormattingEditor.global.selectedPlaceholderParentAreaFullName = "";
      window.nvhFormattingEditor.formattingEditorComponent.update();
    }
  }

  createElementsSchema() {
    return window.nvhFormattingEditor.createElementsSchemaRec(window.store.schema.getRoot());
  }

  createElementsSchemaRec(element) {
    let objectStructure = {
      data: {
        type: "choice-item",
        name: element.name,
        fullName: element.path,
        color: window.nvhStore.getElementColor(element.path),
        children: [],
      },
    };
    for (let child of element.children) {
      let newElement = this.createElementsSchemaRec(child);
      objectStructure.data.children.push(newElement)
    }
    return objectStructure;
  }

  clearIsHoveredStatus() {
    window.nvhFormattingEditor.clearIsHoveredStatusRec(window.nvhFormattingEditor.currentLayout.schema);
  }

  clearIsHoveredStatusRec(state) {
    if (state === null) {
      return null;
    }
    Array.from(state.children).map(child => this.clearIsHoveredStatusRec(child));
    state.children.map(child => child.status.isHovered = false);
  }

  // RENAME ?
  closeActionPanel() {
    this.closeActionPanelRec(window.nvhFormattingEditor.currentLayout.schema);
  }

  // RENAME ?
  closeActionPanelRec(state) {
    if (state === null) {
      return null;
    }
    Array.from(state.children).map(child => this.closeActionPanelRec(child));
    state.children.map(child => child.status.isActive = false);
  }

  // RENAME ?
  openActionPanel(child, parent) {
    if (window.nvhFormattingEditor.global.canOpenActionPanel) {
      let currentIsActive = child.status.isActive
      window.nvhFormattingEditor.closeActionPanel(); /*close actionPanel if any was opened*/
      child.status.isActive = !currentIsActive; /*clicking on selected placeholder should unselect it*/
      if (child.status.isActive && child.children.length === 0) {
        window.nvhFormattingEditor.global.selectedPlaceholderFullName = child.content.fullName;
      } else {
        window.nvhFormattingEditor.global.selectedPlaceholderFullName = "";
      }
      if (child.status.isActive) {
        window.nvhFormattingEditor.global.selectedPlaceholderAreaFullName = child.content.areaFullName;
        window.nvhFormattingEditor.global.selectedPlaceholderParentAreaFullName = parent.content.areaFullName;
        window.nvhFormattingEditor.global.selectedPlaceholder = child;
      } else {
        window.nvhFormattingEditor.global.selectedPlaceholderAreaFullName = "";
        window.nvhFormattingEditor.global.selectedPlaceholderParentAreaFullName = "";
        window.nvhFormattingEditor.global.selectedPlaceholder = null;
      }
    } else {
      child.status.isActive = false;
    }
    window.nvhFormattingEditor.global.canOpenActionPanel = false;
  }

  isChildChoiceItemOfPlaceholder(child, parent) {
    return child.includes(parent);
  }

  isChildOfParent(child, parent) { // NOTE
    if (window.nvhFormattingEditor.global.draggedPlaceholder !== null) {
      return window.nvhFormattingEditor.isChildObjectOfParent(window.nvhFormattingEditor.global.draggedPlaceholder, parent);
    }
    let result = child.includes(parent);
    let alternative = window.nvhFormattingEditor.global.draggedElementFullName === "";
    return result || alternative;
  }

  isChildObjectOfParent(childObject, parent) {
    if (childObject.content.fullName === parent && childObject.children.length !== 0) {
      /*This avoids placing a wrapper with label "parent" into another wrapper with label "parent"*/
      return false;
    }
    let result = childObject.content.fullName.includes(parent);
    let alternative = childObject.content.fullName === "";
    if (!result && !alternative) {
      return false;
    }

    for (let child of childObject.children) {
      if (!this.isChildObjectOfParent(child, parent)) {
        return false;
      }
    }
    return true;
  }

  /*TODO: it seems like label is here always null, figure out why*/
  addElement(index, component, state, editingMode, label) {
    let newElement = {
      status: {
        isActive: true,
        isHovered: true,
        isDragged: false,
      },
      orientation: editingMode,
      type: "placeholder",
      content: {
        name: label == null ? "" : label.name,
        fullName: label == null ? "" : label.fullName,
        area: label == null ? "" : label.area,
        areaFullName: label == null ? "" : label.areaFullName,
        color: label == null ? "": label.color,
        canHaveChildren: true, /*NOTE: really always true ?*/
      },
      children: []
    };
    window.nvhFormattingEditor.closeActionPanel();
    window.nvhFormattingEditor.clearIsHoveredStatus();
    window.nvhFormattingEditor.global.selectedPlaceholderAreaFullName = state.content.areaFullName;
    window.nvhFormattingEditor.global.selectedPlaceholderFullName = "";
    window.nvhFormattingEditor.global.selectedPlaceholder = newElement;
    window.nvhFormattingEditor.global.selectedPlaceholderParentAreaFullName = state.content.areaFullName;
    state.children.splice(index, 0, newElement);
    window.nvhFormattingEditor.formattingEditorComponent.update();
    window.nvhFormattingEditor.global.canOpenActionPanel = false;
  }

  addElementWithChildren(index, component, state, element, label) {
    /*label can not be null or undefined*/
    if (label == null || label == undefined) {
      return;
    }
    let newElement = {
      status: {
        isActive: false,
        isHovered: false,
        isDragged: false,
      },
      orientation: "column",
      type: "placeholder",
      content: {
        name: label.name,
        fullName: label.fullName,
        area: label.name,
        areaFullName: label.fullName,
        color: label.color,
        canHaveChildren: label.canHaveChildren !== undefined ? label.canHaveChildren : label.children.length !== 0,
      },
      children: []
    };

    if (state != null) {
      state.children.splice(index, 0, newElement);
    }
    if (label.children !== undefined && label.children !== null && element.content.areaFullName != label.areaFullName) {
      /*
      Children are present.
      When I drop to an plus icon e.g. pronunciation and the parent
      is also of type pronunciation, so that it will not render all the children.
      */
      /*
      If element has children, append also this element,
      so that it is displayed together with its children.
      */
      if (label.children.length !== 0) {
        let selfDisplayElement = {
          status: {
            isActive: false,
            isHovered: false,
            isDragged: false,
          },
          orientation: "column",
          type: "placeholder",
          content: {
            name: label.name,
            fullName: label.fullName,
            area: label.name,
            areaFullName: label.fullName,
            color: label.color,
            canHaveChildren: false,
          },
          children: []
        };
        newElement.children.push(selfDisplayElement);
      }
      for(let child of label.children) {
        let childElement = this.addElementWithChildren(null, null, null, newElement, child.data);
        newElement.children.push(childElement);
      }
    }
    if (component != null) {
      window.nvhFormattingEditor.formattingEditorComponent.update();
    }
    return newElement;
  }

  deleteElement(indexToDelete, parentState) {
    parentState.children = Array.from(parentState.children).filter((child, index) => index != indexToDelete);
    window.nvhFormattingEditor.global.canOpenActionPanel = false;
    window.nvhFormattingEditor.global.draggedElementFullName = "";
    window.nvhFormattingEditor.global.selectedPlaceholderFullName = "";
    window.nvhFormattingEditor.global.selectedPlaceholderAreaFullName = "";
    window.nvhFormattingEditor.global.selectedPlaceholderParentAreaFullName = "";
    window.nvhFormattingEditor.global.selectedPlaceholder = null;
    window.nvhFormattingEditor.formattingEditorComponent.update(); // NOTE: here was updated only edit-layout, but maybe does not matter
  }

  childWithInheritedArea(child, state) {
    if (state === null) {
      return child;
    }
    child.content.area = child.content.name === "" ? state.content.area : child.content.name;
    child.content.areaFullName = child.content.name === "" ? state.content.areaFullName : child.content.fullName;
    return child;
  }

  canHaveAdders(parentFullName, placeholder) {
    if (parentFullName === placeholder.content.fullName) {
      return false;
    }
    if (!placeholder.content.canHaveChildren) {
      return false;
    }
    return true;
  }

  getChoiceElementsFullNamesList() {
    return window.store.schema.getElementList().map(e => e.path);
  }

  /*Validation of choice-element vs. placeholder relationship functions*/
  isElementWithoutChildrenToWrapper(element, placeholder) {
    return placeholder.children.length !== 0 && element.children.length === 0;
  }
  isElementToRedundantNestedWrapper(element, placeholderWrapperAreaFullName, placeholder) {
    return placeholderWrapperAreaFullName.includes(element.fullName) && placeholder.children.length !== 0;
  }
  isPlaceholderAsSameWrapper(elementName, placeholder) {
    if (placeholder.content.fullName !== "" && elementName !== placeholder.content.fullName && elementName.includes(placeholder.content.fullName)) {
      /*Optimization: None of next children can be same wrapper*/
      return false;
    }
    if (elementName === placeholder.content.fullName && placeholder.children.length !== 0) {
      return true;
    }

    for (let child of placeholder.children) {
      if (this.isPlaceholderAsSameWrapper(elementName, child)) {
        return true;
      }
    }
    return false;
  }
  isParentLabelOfDropObject(parentLabel, dropObject) {
    let result = dropObject.content.fullName.includes(parentLabel);
    let alternative = dropObject.content.fullName === "";
    if (!result && !alternative) {
      return false;
    }

    for (let child of dropObject.children) {
      if (!this.isParentLabelOfDropObject(parentLabel, child)) {
        return false;
      }
    }
    return true;
  }
  isChoiceElementValidToPlaceholder(choiceElement, placeholder, placeholderWrapperAreaFullName) {
    if (window.nvhFormattingEditor.isElementWithoutChildrenToWrapper(choiceElement, placeholder)) {
      return false;
    }
    if (window.nvhFormattingEditor.isElementToRedundantNestedWrapper(choiceElement, placeholderWrapperAreaFullName, placeholder)) {
      return false;
    }
    for (let child of placeholder.children) {
      if (!window.nvhFormattingEditor.isParentLabelOfDropObject(choiceElement.fullName, child)) {
        return false;
      }
    }
    for (let child of placeholder.children) {
      if (window.nvhFormattingEditor.isPlaceholderAsSameWrapper(choiceElement.fullName, child)) {
        return false;
      }
    }
    if (!window.nvhFormattingEditor.isChildChoiceItemOfPlaceholder(choiceElement.fullName, placeholderWrapperAreaFullName)) {
      return false;
    }
    return true;
  }
}

window.nvhFormattingEditor = new NVHFormattingEditorClass();