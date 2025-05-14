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
    this.elementsSchema = null,
    this.data = this.getInitializedDataAttributes(),
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

  updateEditor() {
    this.trigger("updateEditor");
  }

  getInitializedDataAttributes() {
    return {
      canBeDropped: true,
      canBeDragged: true,
      canSelectLayoutContainer: true,
      dropInfo: {
        wasSuccessful: false,
        index: null,
      },
      mouseData: null,
      draggedLayoutContainer: null,
      hoveredLayoutContainer: null,
      selectedLayoutContainer: null,
      selectedLayoutContainerParentAreaFullName: "",
      activeLayout: "desktop", /*desktop, tablet, mobile, pdf*/
    }
  }

  resetDataAttributes() {
    this.data.canBeDropped = true;
    this.data.canBeDragged = true;
    this.data.canSelectLayoutContainer = true;
    this.data.dropInfo = {
      wasSuccessful: false,
      index: null,
    };
  }

  changeLayoutSchema() {
    if (window.innerWidth < 440) {
      this.setClosestConfiguredLayout("mobile");
    } else if (window.innerWidth < 1020) {
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

    let entriesList = await this.loadEntries();
    exportedEntries.inProgress = true;
    exportedEntries.total = entriesList.entriesList.length;
    exportedEntries.exported = 0;

    let htmlWrapper = "<div>";

    for (let idx = 0; idx < entriesList.entriesList.length; idx++) {
      let entryJson = window.nvhStore.nvhToJson(entriesList.entriesList[idx].nvh);
      htmlWrapper += this.stringifyEntry(entryJson);
      htmlWrapper += `<div style="height: 1px; width: 980px; background-color: grey; margin: 2px 0"></div>`
      if (htmlWrapper.length > 700000) { // Do not send all entries at once to backend, set some limit
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

  clearLayoutContainer(layoutContainer) {
    layoutContainer.content.name = "";
    layoutContainer.content.fullName = "";
    layoutContainer.content.area = "";
    layoutContainer.content.areaFullName = "";
    layoutContainer.content.canHaveChildren = true;
    layoutContainer.styles = {};
    layoutContainer.markupStyles = [];
    layoutContainer.labelStyles = {};
    layoutContainer.bulletStyles = {};
  }

  fillLayoutContainerWithData(layoutContainer, data) {
    layoutContainer.content.name = data.name;
    layoutContainer.content.fullName = data.fullName;
    layoutContainer.content.area = data.name;
    layoutContainer.content.areaFullName = data.fullName;
    layoutContainer.content.canHaveChildren = data.children.length !== 0;
    layoutContainer.styles = {};
    layoutContainer.labelStyles = {};
    layoutContainer.bulletStyles = {};

    let markupChildren = this.getDirectMarkupChildren(data.fullName);
    if (markupChildren.length !== 0) {
      layoutContainer.markupStyles = this.createMarkupStyles(data.fullName);
    }
  }

  resetSchema() {
    this.initializeSchema();
    this.updateEditor()
  }

  initializeSchema() {
    this.currentLayout.schema = this.createSchema();
    this.data.selectedLayoutContainer = null;
    this.data.selectedLayoutContainerParentAreaFullName = "";
  }

  initializeSchemas() {
    let initialSchema = this.createSchema();
    /* ASK: window.store.data.config.formatting.elements was used before
    the implementation of nvh-formatting-editor; but it is not used anymore;
    should it be removed?*/
    let defaultElements = window.store.data.config.formatting.elements;

    for (let layout of ["desktop", "tablet", "mobile", "pdf"]) {
      this.layout[layout] = {
        configured: false,
        schema: structuredClone(initialSchema),
        elements: structuredClone(defaultElements),
        history: {
          index: 0,
          schema: [structuredClone(initialSchema)],
          elements: [structuredClone(defaultElements)],
        }
      }
    }
    this.layout.desktop.configured = true;
    this.data.selectedLayoutContainer = null;
    this.data.selectedLayoutContainerParentAreaFullName = "";
  }

  createSchema() {
    let root = window.store.schema.getRoot();
    return {
      orientation: "column",
      children: [
        {
          orientation: "column",
          type: "layout-container", // NOTE
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

  goToHistory(index) {
    let history = this.currentLayout.history
    history.index += index;
    this.currentLayout.schema = structuredClone(history.schema.at(history.index));
    this.currentLayout.elements = structuredClone(history.elements.at(history.index));
    this.data.selectedLayoutContainer = null;
    this.data.selectedLayoutContainerParentAreaFullName = "";
    this.updateEditor();
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

  selectLayoutContainer(child, parent) {
    if (this.data.canSelectLayoutContainer) {
      if (!this.isLayoutContainerActive(child)) {
        if (parent) {
          this.data.selectedLayoutContainerParentAreaFullName = parent.content.areaFullName;
        }
        this.data.selectedLayoutContainer = child;
      } else {
        this.data.selectedLayoutContainerParentAreaFullName = "";
        this.data.selectedLayoutContainer = null;
      }
    }
    this.data.canSelectLayoutContainer = false;
  }

  isChildChoiceItemOfLayoutContainer(child) {
    return child.includes(this.data.selectedLayoutContainerParentAreaFullName);
  }

  isChildOfParent(parent) {
    let data = this.data.mouseData;
    if (data?.type === "layout-container") {
      return this.isChildObjectOfParent(data, parent);
    }
    if (data?.type === "choice-item") {
      return data?.fullName.includes(parent)
    }
    return true;
  }

  isChildObjectOfParent(childObject, parent) {
    if (childObject.content.fullName === parent && childObject.children.length
      || !childObject.content.fullName.includes(parent) && childObject.content.fullName) {
      return false;
    }

    for (let child of childObject.children) {
      if (!this.isChildObjectOfParent(child, parent)) {
        return false;
      }
    }
    return true;
  }

  addElement(index, state, label) {
    let newElement = {
      orientation: "row",
      type: "layout-container",
      content: {
        name: label?.name || "",
        fullName: label?.fullName || "",
        area: label?.area || state.content.area,
        areaFullName: label?.areaFullName || state.content.areaFullName,
        canHaveChildren: !label ? true : window.store.schema.getElementByPath(label.fullName).children.length
      },
      styles: {},
      markupStyles: [],
      labelStyles: {},
      bulletStyles: {},
      children: []
    };
    this.data.selectedLayoutContainer = newElement;
    this.data.selectedLayoutContainerParentAreaFullName = state.content.areaFullName;
    state.children.splice(index, 0, newElement);
    this.data.canSelectLayoutContainer = false;
  }

  deleteElement(indexToDelete, parentState) {
    parentState.children = Array.from(parentState.children).filter((_child, index) => index != indexToDelete);
    this.data.canSelectLayoutContainer = false;
    this.data.selectedLayoutContainerParentAreaFullName = "";
    this.data.selectedLayoutContainer = null;
  }

  isMarkupType(fullName) {
    if (!fullName) {
      return false;
    }
    let config = window.nvhStore.getElementConfig(fullName);
    return config?.type === "markup";
  }

  childWithInheritedArea(child, state) {
    if (!state) {
      return child;
    }
    child.content.area = !child.content.name ? state.content.area : child.content.name;
    child.content.areaFullName = !child.content.name ? state.content.areaFullName : child.content.fullName;
    return child;
  }

  canHaveAdders(parentFullName, layoutContainer) {
    return parentFullName !== layoutContainer.content.fullName && layoutContainer.content.canHaveChildren;
  }

  /*Validation of choice-element vs. layoutContainer relationship functions*/
  isElementWithoutChildrenToWrapper(element, layoutContainer) {
    return layoutContainer.children.length && !element.children.length;
  }
  isElementToRedundantNestedWrapper(element, layoutContainerWrapperAreaFullName, layoutContainer) {
    return layoutContainerWrapperAreaFullName.includes(element.fullName) && layoutContainer.children.length;
  }
  isLayoutContainerAsSameWrapper(elementName, layoutContainer) {
    if (layoutContainer.content.fullName && elementName !== layoutContainer.content.fullName && elementName.includes(layoutContainer.content.fullName)) {
      return false;
    }
    if (elementName === layoutContainer.content.fullName && layoutContainer.children.length) {
      return true;
    }

    for (let child of layoutContainer.children) {
      if (this.isLayoutContainerAsSameWrapper(elementName, child)) {
        return true;
      }
    }
    return false;
  }
  isParentLabelOfDropObject(parentLabel, dropObject) {
    let result = dropObject.content.fullName.includes(parentLabel);
    let alternative = !dropObject.content.fullName;
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
  isChoiceElementValidToLayoutContainer(choiceElement) {
    for (let child of this.data.selectedLayoutContainer.children) {
      if (!this.isParentLabelOfDropObject(choiceElement.fullName, child)
        || this.isLayoutContainerAsSameWrapper(choiceElement.fullName, child)) {
        return false;
      }
    }
    if (!this.isChildChoiceItemOfLayoutContainer(choiceElement.fullName)
      || this.isElementToRedundantNestedWrapper(choiceElement, this.data.selectedLayoutContainerParentAreaFullName, this.data.selectedLayoutContainer)
      || this.isElementWithoutChildrenToWrapper(choiceElement, this.data.selectedLayoutContainer)) {
      return false;
    }
    return true;
  }
  getDirectMarkupChildren(fullName) {
    let result = [];
    if (!fullName || !window.store.schema.getElementByPath(fullName)) {
      return result;
    }
    for (let child of window.store.schema.getElementByPath(fullName).children) {
      let config = window.nvhStore.getElementConfig(child.path);
      if (config?.type === "markup") {
        result.push({name: child.name, fullName: child.path, color: window.nvhStore.getElementColor(child.path)});
      }
    }
    return result;
  }
  createMarkupStyles(fullName) {
    let markupChildren = this.getDirectMarkupChildren(fullName);
    let result = [];
    for (let child of markupChildren) {
      result.push({name: child.name, fullName: child.fullName, styles: {}});
    }
    return result;
  }
  /*NOTE: Inspired by getFlagTextColor from store.js*/
  getColorLightVersion(colorHex) {
    if (!colorHex) {
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
    return {"link": "🔗", "speaker": "🔊", "load-speaker": "📢"
      , "music-note": "♫", "camera": "📹", "film-frames": "🎞"
      , "film-projector": "📽", "movie-camera": "🎥", "framed-picture": "🖼"}[iconItem];
  }
  getUnicodeIcon(unicodeIcon) {
    return unicodeIcon ? unicodeIcon : "";
  }
  isElementNonExisting(fullName) {
    return fullName && !window.nvhStore.getElementConfig(fullName);
  }
  getMaxPossibleWidth() {
    switch(this.data.activeLayout) {
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

  getCssStyles(state, styles) {
    if (!styles) {
      return;
    }
    let result_css = "";
    for (let i = 0; i < Object.keys(styles).length; i++) {
      let option = Object.keys(styles)[i];
      let value = styles[option];
      if (!value) {
        continue;
      }
      if (["thousandsDivider", "decimalPlaceDivider", "leftPunc", "rightPunc",
      "border-color", "border-width", "container-width", "label-text-value",
      "show-label-before"].includes(option)) {
        continue;
      }
      if (["border-radius", "padding", "margin", "max-height", "font-size"].includes(option)) {
        value = value + "px";
      } else if (option === "box-shadow") {
        value = value + "px " + value + "px " + value + "px " + "grey";
      } else if (option === "text-decoration") {
        let array = styles["text-decoration"];
        if (!array) {
          continue;
        }
        let values = "";
        for (let feature of array) {
          values = values + " " + feature;
        }
        value = values;
      } else if (option === "border") {
        let borderColor = styles?.["border-color"] || "black";
        let borderWidth = !styles["border-width"] ? "1px" : styles["border-width"] + "px";
        value = borderWidth + " " + value + " " + borderColor;
      } else if (option === "container-width-unit") {
        if (styles["container-width"] && styles["container-width"]) {
          if (styles[option] === "px") {
            option = "width";
            if (parseInt(styles["container-width"]) < parseInt(state.maxPossibleWidth)) {
              value = styles["container-width"] + "px";
            } else {
              value = state.maxPossibleWidth + "px";
            }
            state.maxPossibleWidth = value;
          } else if (styles[option] === "%") {
            if (parseInt(styles["container-width"]) >= 100) {
              styles["container-width"] = "100";
            }
            option = "width";
            value = `${(parseInt(styles["container-width"]) / 100) * parseInt(state.maxPossibleWidth)}` + "px";
            state.maxPossibleWidth = value;
          } else {
            continue;
          }
        } else {
          continue;
        }
      } else if (option === "max-width") {
        value = "min(" + styles["max-width"] + "px" + "," + "100%)";
      }
      result_css += option + ":" + value + ";";
    }

    return result_css;
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
}

window.nvhFormattingEditor = new NVHFormattingEditorClass();