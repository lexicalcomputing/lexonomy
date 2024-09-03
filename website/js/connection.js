class ConnectionClass {
   constructor(){
      observable(this)
      $.ajaxSetup({
         xhrFields: {
            withCredentials: true
         }
      })
   }

   get(params){
      return this.sendRequest(Object.assign({
         method: "GET"
      }, params))
   }

   post(params){
      return this.sendRequest(Object.assign({
         method: "POST"
      }, params))
   }

   sendRequest(params){
      let failMessage = params.failMessage || ""
      let successMessage = params.successMessage || ""
      delete params.failMessage
      delete params.successMessage
      return $.ajax(params)
            .done(response => {
               if(response.loggedin === false){
                  window.auth.invalidateSession()
               }
            })
            .always(this.notifyAboutRequestResult(failMessage, successMessage))
   }

   notifyAboutRequestResult(failMessage, successMessage){
      return function(failMessage, successMessage, response) {
         if(failMessage){
            if(response){
               if(response.error){
                  window.showToast(`${failMessage}\n${response.error}`)
               } else if(typeof response.statusText != "undefined" && response.statusText != "abort"){
                  window.showToast(`${failMessage}\n${response.statusText || ""}`)
               }
            } else {
               window.showToast(failMessage)
            }
         }
         if(successMessage && response && !response.error && response.statusText == "undefined"){
            M.toast({html: successMessage})
         }
      }.bind(this, failMessage, successMessage)
   }
}

window.connection = new ConnectionClass()
