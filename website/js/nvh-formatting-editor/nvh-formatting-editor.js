import example_audio_item from '../../riot/nvh-formatting-editor/example-section/example-audio-item.riot';
import example_basic_item from '../../riot/nvh-formatting-editor/example-section/example-basic-item.riot';
import example_bool_item from '../../riot/nvh-formatting-editor/example-section/example-bool-item.riot';
import example_image_item from '../../riot/nvh-formatting-editor/example-section/example-image-item.riot';
import example_markup_item from '../../riot/nvh-formatting-editor/example-section/example-markup-item.riot';
import example_section_item from '../../riot/nvh-formatting-editor/example-section/example-section-item.riot';
import example_url_item from '../../riot/nvh-formatting-editor/example-section/example-url-item.riot';
import example_video_item from '../../riot/nvh-formatting-editor/example-section/example-video-item.riot';

class NVHFormattingEditorClass {
  constructor() {
    this.timeout = null,
    this.dropdownTimeout = null,
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
    riot.register('example-basic-item', example_basic_item);
    riot.register('example-audio-item', example_audio_item);
    riot.register('example-bool-item', example_bool_item);
    riot.register('example-image-item', example_image_item);
    riot.register('example-markup-item', example_markup_item);
    riot.register('example-section-item', example_section_item);
    riot.register('example-url-item', example_url_item);
    riot.register('example-video-item', example_video_item);
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
      mouseData: null,
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
      if (this.global.activeLayout !== "mobile") {
        this.global.activeLayout = "mobile";
        this.setClosestConfiguredLayout("mobile");
      }
    } else if (window.innerWidth < 1020) {
      if (this.global.activeLayout !== "tablet") {
        this.global.activeLayout = "tablet";
        this.setClosestConfiguredLayout("tablet");
      }
    } else {
      if (this.global.activeLayout !== "desktop") {
        this.global.activeLayout = "desktop";
        this.setClosestConfiguredLayout("desktop");
      }
    }
  }

  setClosestConfiguredLayout(activeLayout) {
    let mobileConfigured = this.layout.mobile.configured === undefined ? false : this.layout.mobile.configured;
    let tabletConfigured = this.layout.tablet.configured === undefined ? false : this.layout.tablet.configured;
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

  async parseAllEntries(exportedEntries) {
    await this.clearHtmlFile();

    let entriesList = await this.loadEntries();
    exportedEntries.inProgress = true;
    exportedEntries.total = entriesList.entriesList.length;
    exportedEntries.exported = 0;

    let htmlWrapper = "<div>";

    for (let idx = 0; idx < entriesList.entriesList.length; idx++) {
      let entryJson = window.nvhStore.nvhToJson(entriesList.entriesList[idx].nvh);
      htmlWrapper += await this.parseEntry(entryJson);
      htmlWrapper += `<div style="height: 1px; width: 980px; background-color: grey; margin: 2px 0"></div>`
      if (htmlWrapper.length > 700000) { // Do not send all entries at once to backend, set some limit
        exportedEntries.exported = idx;
        this.formattingEditorComponent.update();
        await this.appendToHtmlFile(htmlWrapper);
        htmlWrapper = ""
      }
    }
    exportedEntries.inProgress = false;
    exportedEntries.total = 0;
    exportedEntries.exported = 0;
    this.formattingEditorComponent.update();

    htmlWrapper += "</div>"
    await this.appendToHtmlFile(htmlWrapper);
  }

  async parseEntry(entry) {
    let schema = this.layout.pdf.configured ? this.layout.pdf.schema : this.layout.desktop.schema;
    let entryHTML = this.getEntryHTML(schema.children[0], entry);
    return entryHTML;
  }

  getEntryHTML(schema, entry) {
    const item = document.createElement('example-section-item');
    riot.mount(item, { schema: schema, entry: entry, maxPossibleWidth: "980px"});
    return item.innerHTML;
  }

  getValidEntryChildren(entry, resultChildren, validPath) {
    for (let child of entry.children) {
      this.getValidEntryChildren(child, resultChildren, validPath);
      if (child.path === validPath) {
        resultChildren.push(child);
      }
    }
    return resultChildren;
  }

  resetSchema() {
    this.initializeSchema();
    this.formattingEditorComponent.update();
  }

  initializeSchema() {
    this.currentLayout.schema = this.createSchema();
    this.global.selectedPlaceholderAreaFullName = "";
    this.global.selectedPlaceholderFullName = "";
    this.global.selectedPlaceholder = null;
    this.global.selectedPlaceholderParentAreaFullName = "";
  }

  initializeSchemas() {
    let initialSchema = this.createSchema();
    let defaultElements = window.store.data.config.formatting.elements;

    this.layout.desktop = {
      configured: true,
      schema: JSON.parse(JSON.stringify(initialSchema)),
      elements: JSON.parse(JSON.stringify(defaultElements)),
      history: {
        index: 0,
        schema: [JSON.parse(JSON.stringify(initialSchema))],
        elements: [JSON.parse(JSON.stringify(defaultElements))],
      }
    }
    this.layout.tablet = {
      configured: false,
      schema: JSON.parse(JSON.stringify(initialSchema)),
      elements: JSON.parse(JSON.stringify(defaultElements)),
      history: {
        index: 0,
        schema: [JSON.parse(JSON.stringify(initialSchema))],
        elements: [JSON.parse(JSON.stringify(defaultElements))],
      }
    }
    this.layout.mobile = {
      configured: false,
      schema: JSON.parse(JSON.stringify(initialSchema)),
      elements: JSON.parse(JSON.stringify(defaultElements)),
      history: {
        index: 0,
        schema: [JSON.parse(JSON.stringify(initialSchema))],
        elements: [JSON.parse(JSON.stringify(defaultElements))],
      }
    }
    this.layout.pdf = {
      configured: false,
      schema: JSON.parse(JSON.stringify(initialSchema)),
      elements: JSON.parse(JSON.stringify(defaultElements)),
      history: {
        index: 0,
        schema: [JSON.parse(JSON.stringify(initialSchema))],
        elements: [JSON.parse(JSON.stringify(defaultElements))],
      }
    }
    this.global.selectedPlaceholderAreaFullName = "";
    this.global.selectedPlaceholderFullName = "";
    this.global.selectedPlaceholder = null;
    this.global.selectedPlaceholderParentAreaFullName = "";
  }

  createSchema() {
    let root = window.store.schema.getRoot();
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
            name: root.path,
            fullName: root.path,
            area: root.path,
            areaFullName: root.path,
            canHaveChildren: true,
          },
          styles: {},
          markupStyles: this.createMarkupStyles(root.path),
          labelStyles: {},
          bulletStyles: {},
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

  clearDraggedStatuses(state) {
    if (state === null) {
      return;
    }
    Array.from(state.children).map(child => this.clearDraggedStatuses(child));
    state.children.map(child => {
      child.status.isDragged = false;
    });
  }

  undoSchema() {
    if (this.currentLayout.history.index > 0) {
      this.currentLayout.history.index -= 1;
      this.currentLayout.schema = JSON.parse(JSON.stringify(this.currentLayout.history.schema.at(this.currentLayout.history.index)));
      this.currentLayout.elements = JSON.parse(JSON.stringify(this.currentLayout.history.elements.at(this.currentLayout.history.index)));
      this.clearStatuses(this.currentLayout.schema);
      this.global.selectedPlaceholderAreaFullName = "";
      this.global.selectedPlaceholderFullName = "";
      this.global.selectedPlaceholder = null;
      this.global.selectedPlaceholderParentAreaFullName = "";
      this.formattingEditorComponent.update();
    }
  }

  redoSchema() {
    if (this.currentLayout.history.index < this.currentLayout.history.schema.length - 1) {
      this.currentLayout.history.index += 1;
      this.currentLayout.schema = JSON.parse(JSON.stringify(this.currentLayout.history.schema.at(this.currentLayout.history.index)));
      this.currentLayout.elements = JSON.parse(JSON.stringify(this.currentLayout.history.elements.at(this.currentLayout.history.index)));
      this.clearStatuses(this.currentLayout.schema);
      this.global.selectedPlaceholderAreaFullName = "";
      this.global.selectedPlaceholderFullName = "";
      this.global.selectedPlaceholder = null;
      this.global.selectedPlaceholderParentAreaFullName = "";
      this.formattingEditorComponent.update();
    }
  }

  createElementsSchema() {
    return this.createElementsSchemaRec(window.store.schema.getRoot());
  }

  createElementsSchemaRec(element) {
    let objectStructure = {
      data: {
        type: "choice-item",
        name: element.name,
        fullName: element.path,
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
    this.clearIsHoveredStatusRec(this.currentLayout.schema);
  }

  clearIsHoveredStatusRec(state) {
    if (state === null) {
      return null;
    }
    Array.from(state.children).map(child => this.clearIsHoveredStatusRec(child));
    state.children.map(child => child.status.isHovered = false);
  }

  selectPlaceholder(child, parent) {
    if (this.global.canOpenActionPanel) {
      let currentIsActive = child.status.isActive;
      this.clearStatuses(this.currentLayout.schema);
      child.status.isActive = !currentIsActive; /*clicking on selected placeholder should unselect it*/
      child.status.isHovered = true;
      if (child.status.isActive && child.children.length === 0) {
        this.global.selectedPlaceholderFullName = child.content.fullName;
      } else {
        this.global.selectedPlaceholderFullName = "";
      }
      if (child.status.isActive) {
        this.global.selectedPlaceholderAreaFullName = child.content.areaFullName;
        if (parent !== null) {
          this.global.selectedPlaceholderParentAreaFullName = parent.content.areaFullName;
        }
        this.global.selectedPlaceholder = child;
      } else {
        this.global.selectedPlaceholderAreaFullName = "";
        this.global.selectedPlaceholderParentAreaFullName = "";
        this.global.selectedPlaceholder = null;
      }
    } else {
      child.status.isActive = false;
    }
    this.global.canOpenActionPanel = false;
  }

  isChildChoiceItemOfPlaceholder(child, parent) {
    return child.includes(parent);
  }

  isChildOfParent(child, parent) {
    if (this.global.draggedPlaceholder !== null) {
      return this.isChildObjectOfParent(this.global.draggedPlaceholder, parent);
    }
    let result = child.includes(parent);
    let alternative = this.global.draggedElementFullName === "";
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

  addElement(index, state, editingMode, label) {
    let newElement = {
      status: {
        isActive: true,
        isHovered: false,
        isDragged: false,
      },
      orientation: editingMode,
      type: "placeholder",
      content: {
        name: label === null ? "" : label.name,
        fullName: label === null ? "" : label.fullName,
        area: label === null ? "" : label.area,
        areaFullName: label === null ? "" : label.areaFullName,
        canHaveChildren: label === null ? true : window.store.schema.getElementByPath(label.fullName).children.length !== 0
      },
      styles: {},
      markupStyles: [],
      labelStyles: {},
      bulletStyles: {},
      children: []
    };
    this.clearStatuses(this.currentLayout.schema);
    this.global.selectedPlaceholderAreaFullName = state.content.areaFullName;
    this.global.selectedPlaceholderFullName = "";
    this.global.selectedPlaceholder = newElement;
    this.global.selectedPlaceholderParentAreaFullName = state.content.areaFullName;
    state.children.splice(index, 0, newElement);
    this.formattingEditorComponent.update();
    this.global.canOpenActionPanel = false;
  }

  deleteElement(indexToDelete, parentState, state) {
    if (this.isMarkupTypeChild(state.content.fullName)) {
      state.styles = false;
      if (state.markupValue !== undefined) {
        state.markupValue.value = null;
      }
    }
    this.clearStatuses(this.currentLayout.schema);
    parentState.children = Array.from(parentState.children).filter((_child, index) => index != indexToDelete);
    this.global.canOpenActionPanel = false;
    this.global.draggedElementFullName = "";
    this.global.selectedPlaceholderFullName = "";
    this.global.selectedPlaceholderAreaFullName = "";
    this.global.selectedPlaceholderParentAreaFullName = "";
    this.global.selectedPlaceholder = null;
  }

  isMarkupTypeChild(fullName) {
    if (fullName === "") {
      return false;
    }
    let pathArray = fullName.split('.');
    if (pathArray.length === 1) {
      return false;
    }
    pathArray.length -= 1;
    let parentPath = pathArray.join('.');
    let config = window.nvhStore.getElementConfig(parentPath);
    if (config === undefined) {
      return false;
    }
    return config.type === "markup";
  }

  isMarkupType(fullName) {
    if (fullName === "") {
      return false;
    }
    let config = window.nvhStore.getElementConfig(fullName);
    if (config === undefined) {
      return false;
    }
    return config.type === "markup";
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
    if (this.isElementWithoutChildrenToWrapper(choiceElement, placeholder)) {
      return false;
    }
    if (this.isElementToRedundantNestedWrapper(choiceElement, placeholderWrapperAreaFullName, placeholder)) {
      return false;
    }
    for (let child of placeholder.children) {
      if (!this.isParentLabelOfDropObject(choiceElement.fullName, child)) {
        return false;
      }
    }
    for (let child of placeholder.children) {
      if (this.isPlaceholderAsSameWrapper(choiceElement.fullName, child)) {
        return false;
      }
    }
    if (!this.isChildChoiceItemOfPlaceholder(choiceElement.fullName, placeholderWrapperAreaFullName)) {
      return false;
    }
    return true;
  }

  hasDirectMarkupChild(fullName) {
    let result = [];
    if (fullName === "" || window.store.schema.getElementByPath(fullName) === undefined) {
      return result;
    }
    for (let child of window.store.schema.getElementByPath(fullName).children) {
      let config = window.nvhStore.getElementConfig(child.path);
      if (config === undefined) {
        continue;
      }
      if (config.type === "markup") {
        result.push({name: child.name, fullName: child.path, color: window.nvhStore.getElementColor(child.path)});
      }
    }
    return result;
  }
  createMarkupStyles(fullName) {
    let markupChildren = this.hasDirectMarkupChild(fullName);
    let result = [];
    for (let child of markupChildren) {
      result.push({name: child.name, fullName: child.fullName, styles: {}});
    }
    return result;
  }
  /*NOTE: Inspired by getFlagTextColor from store.js*/
  getColorLightVersion(colorHex) {
    if (colorHex === null || colorHex === "") {
      return "transparent";
    }
    let tmp = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(colorHex);
    let red = parseInt(tmp[1], 16);
    let green = parseInt(tmp[2], 16);
    let blue = parseInt(tmp[3], 16);

    let newRed = Math.round(red + (255 - red) * 0.7).toString(16);
    let newGreen = Math.round(green + (255 - green) * 0.7).toString(16);
    let newBlue = Math.round(blue + (255 - blue) * 0.7).toString(16);
    return "#" + newRed + newGreen + newBlue;
  }

  getIcon(iconItem) {
    switch (iconItem) {
      case "link":
        return "🔗";
      case "speaker":
        return "🔊";
      case "load-speaker":
        return "📢";
      case "music-note":
        return "♫";
      case "camera":
        return "📹";
      case "film-frames":
        return "🎞";
      case "film-projector":
        return "📽";
      case "movie-camera":
        return "🎥";
      case "framed-picture":
        return "🖼";
      default:
        return ""
    }
  }
  getUnicodeIcon(unicodeIcon) {
    if (unicodeIcon) {
      return unicodeIcon;
    } else {
      return "";
    }
  }
  isElementNonExisting(fullName) {
    return fullName !== "" && window.nvhStore.getElementConfig(fullName) === undefined;
  }
  getMaxPossibleWidth() {
    switch(this.global.activeLayout) {
      case "tablet":
        return "1020px";
      case "pdf":
        return "980px";
      case "mobile":
        return "440px";
      default:
        // 2 * 5px padding + 2 * 3 px of margin = 16 px
        return (window.innerWidth * 0.8 - 16).toString() + "px";
    }
  }
}

window.nvhFormattingEditor = new NVHFormattingEditorClass();