window.CustomStyles = {
   add: (styleId, css, prefix) => {
      let id = `customStyle_${styleId}`
      let styleNode = document.getElementById(id)
      if(!styleNode){
         styleNode = document.createElement("style")
         styleNode.id = id
         styleNode.type = "text/css"
         let head = document.head || document.getElementsByTagName("head")[0]
         head.appendChild(styleNode)
      }
      styleNode.innerHTML = ""
      try{
         if(prefix){
            // add prefix to the each selector to limit style scope
            css = window.CSSParser.parseCSS(css)
                  .map(rule => {
                     if(rule.type == "keyframes"){
                        return `${rule.selector}{${rule.styles}}`
                     } else {
                        let selectors = rule.selector.split("\n")
                              .map(s => {
                                 return `${prefix} ${s}`
                              }).join(",")
                        let rules = rule.rules.map(r => `${r.directive}:${r.value}`)
                              .join(";\n")
                        return `${selectors}{${rules}}`
                     }
                  }).join('\n')
         }
         styleNode.appendChild(document.createTextNode(css))
      } catch (e){}
   },

   remove: (styleId) => {
      let styleNode = document.getElementById(`customStyle_${styleId}`)
      styleNode && styleNode.remove()
   }
}
