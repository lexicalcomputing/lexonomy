window.nvhPlugins.ske = {
   isActive: function(element){
      return this.hasSkeConnectionSettings()
            && (this.hasSearchOptions(element)
               || this.hasExamples(element)
               || this.hasCollocations(element)
               || this.hasThesaurus(element)
               || this.hasDefinitions(element))
   },

   hasSearchOptions(element){
      let config = window.store.data.config
      return ((element.name == config.structure.root)
               || (config.kex.searchElements.includes(element.name)))
   },

   hasExamples: function(element) {
      let config = window.store.data.config
      return element.name == config.structure.root
            && config.structure.elements[config.xampl.container]
   },

   hasCollocations: function(element) {
      let config = window.store.data.config
      return element.name == config.structure.root
            && config.structure.elements[config.collx.container]
   },

   hasThesaurus: function(element) {
      let config = window.store.data.config
      return element.name == config.structure.root
            && config.structure.elements[config.thes.container]
   },

   hasDefinitions: function(element) {
      let config = window.store.data.config
      return element.name == config.structure.root
            && config.structure.elements[config.defo.container]
   },

   hasSkeConnectionSettings: function() {
      let config = window.store.data.config
      let authData = window.auth.data
      return window.store.data.siteconfig.api_url
            && config.kex
            && config.kex.corpus
            && authData.ske_username
            && authData.ske_apiKey
   },

   openSkeDialog(method, searchWord){
      window.modal.open({
         tag: "nvh-ske-dialog",
         fixedFooter: true,
         tall: true,
         props: {
            method: method,
            searchWord: searchWord
         }
      })
   },

   getConcordanceOperations(element, searchWord){
      let config = window.store.data.config
      let operations = []
      if (element.name == config.structure.root && config.kex.concquery.length > 0) {
         let cql = config.kex.concquery.replace(/%\([^)]+\)/g, function (match) {
            let elementName = match.substring(2, match.length - 1)
            let element = window.nvhStore.findElement(el => el == elementName)
            return element ? element.value : ""
         })
         operations.push({
            "name": "cql",
            "arg": cql,
            "query": {
               "queryselector": "cqlrow",
               "cql": cql
            }
         })
      } else {
         operations.push({
            "name": "iquery",
            "arg": searchWord,
            "query": {
               "queryselector": "iqueryrow",
               "iquery": searchWord
            }
         })
      }
      if(config.kex.concsampling > 0){
         operations.push({
            "name": "sample",
            "arg": config.kex.concsampling,
            "query": {"q": "r" + config.kex.concsampling}
         })
      }
     return operations
   },

   getHeadword(){
      return window.nvhStore.findElement(e => e.name == window.store.data.config.titling.headword).value
   },

   onPluginButtonClick(element, evt){
      let config = window.store.data.config
      let id = `dropdown${Math.round(Math.random()*100000)}`
      let dropdownContent = $(`<ul id="${id}" class="dropdown-content"></ul>`).click(window.stopEvtPropagation)
      dropdownContent.append($(`<li class="pointerEventsNone" tabindex="-1">
         <a class="grey-text" style="text-transform: uppercase;">
            <i class="left">
               <img src="img/logo_ske_round.png" style="width: 24px;">
            </i>
            Sketch Engine
         </a>
      </li>`))
      dropdownContent.append($('<li class="divider" tabindex="-1"></li>'))

      let searchWord = element.name == config.structure.root
            ? this.getHeadword()
            : element.value
      this.hasExamples(element) && dropdownContent.append($(`<li><a>Find examples<i class="material-icons left">search</i></a></li>`)
            .click(this.openSkeDialog.bind(this, "xampl", searchWord)))
      this.hasCollocations(element) && dropdownContent.append($(`<li><a>Find collocations<i class="material-icons left">search</i></a></li>`)
            .click(this.openSkeDialog.bind(this, "collx", searchWord)))
      this.hasThesaurus(element) && dropdownContent.append($(`<li><a>Find thesaurus items<i class="material-icons left">search</i></a></li>`)
            .click(this.openSkeDialog.bind(this, "thes", searchWord)))
      this.hasDefinitions(element) && dropdownContent.append($(`<li><a>Find definitions<i class="material-icons left">search</i></a></li>`)
            .click(this.openSkeDialog.bind(this, "defo", searchWord)))
      if(searchWord && this.hasSearchOptions(element)){
         let corpus = encodeURIComponent(config.kex.corpus)
         let concordanceOperations = encodeURIComponent(JSON.stringify(this.getConcordanceOperations(element, searchWord)))
         dropdownContent.append($(`<li><a href="${window.store.data.siteconfig.ske_url}/#wordsketch?corpname=${corpus}&lemma=${searchWord}&showresults=1" target="_blank">Show Word Sketch<i class="material-icons left">open_in_new</i></a></li>`))
         dropdownContent.append($(`<li><a href="${window.store.data.siteconfig.ske_url}/#concordance?corpname=${corpus}&operations=${concordanceOperations}&showresults=1" target="_blank">Show Concordance<i class="material-icons left">open_in_new</i></a></li>`))
         dropdownContent.append($(`<li><a href="${window.store.data.siteconfig.ske_url}/#thesaurus?corpname=${corpus}&lemma=${searchWord}&showresults=1" target="_blank">Show Thesaurus<i class="material-icons left">open_in_new</i></a></li>`))
      }

      $(evt.currentTarget).after(dropdownContent)
            .attr("data-target", id)
            .addClass("dropdown-trigger")
            .dropdown({
               coverTrigger: false,
               constrainWidth: false,
               onCloseEnd: function(target, dropdownContent){
                  M.Dropdown.getInstance(target).destroy()
                  dropdownContent.remove()
               }.bind(this, evt.currentTarget, dropdownContent)
            })
      M.Dropdown.getInstance(evt.currentTarget).open()
   }
}
