class AuthClass {
   constructor(){
      observable(this);

      this.data = {
         authorized: false
      }
      this.resetUser()
      window.dispatcher.on("userCameBack", this.onUserCameBack.bind(this))
   }

   resetUser(){
      Object.assign(this.data, {
         apiKey: null,
         consent: null,
         email: null,
         sessionkey: null,
         ske_apiKey: null,
         ske_username: null
      })
   }

   onUserCameBack(){
      if (this.data.authorized) {
         window.connection.post({
            url: `${window.API_URL}login.json`,
            failMessage: "Could not check authorization cookie."
         })
               .always(response => {
                  if (response.success && !response.loggedin) {
                     this.invalidateSession()
                  }
               })
      }
   }

   checkAuthCookie(){
      if (!this.data.email) {
         this.data.isCheckingAuth = true
         this.trigger("checkingAuthChanged")
         return window.connection.post({
            url: `${window.API_URL}login.json`,
            failMessage: "Could not check authorization cookie."
         })
               .done(response => {
                  if (response.success && response.loggedin) {
                     Object.assign(this.data, response)
                     this.data.authorized = true;
                     this.trigger("authChanged")
                  }
               })
               .always(() => {
                  this.data.isCheckingAuth = false
                  this.trigger("checkingAuthChanged")
               })
      }
   }

   login(email, password){
      this.data.isCheckingAuth = true
      this.trigger("checkingAuthChanged")
      return window.connection.post({
            url: `${window.API_URL}login.json`,
            data: {
               email: email,
               password: password
            }
         })
               .done(response => {
                  if (response.success && response.loggedin) {
                     Object.assign(this.data, response)
                     this.data.authorized = true;
                     this.trigger("authChanged")
                  }
               })
               .always((response) => {
                  this.data.isCheckingAuth = false
                  this.trigger("checkingAuthChanged")
                  if(!response || !response.success){
                     window.showToast("Login failed.")
                  } else if(!response.loggedin){
                     window.showToast("You have entered an invalid email or password.")
                  }
               })
   }

   register(email){
      return window.connection.post({
            url: `${window.API_URL}signup.json`,
            data: {
               email: email
            },
            failMessage: "Registration failed."
         })
   }

   registerPassword(token, password){
      return window.connection.post({
            url: `${window.API_URL}createaccount.json`,
            data: {
               token: token,
               password: password
            },
            failMessage: "Could not create the account",
            successMessage: "The account was created."
         })
   }

   requestResetPassword(email){
      return window.connection.post({
            url: `${window.API_URL}forgotpwd.json`,
            data: {
               email: email
            },
            failMessage: "Could not request password reset.",
            successMessage: "Link to reset password was sent to your email."
         })
   }

   setUserPassword(email, password){
      return window.connection.post({
         url: `${window.API_URL}users/userupdate.json`,
         data: {
            email: email,
            password: password
         },
         failMessage: "User password could not be set.",
         successMessage: "User password was set."
      })
   }

   resetPassword(token, password){
      return window.connection.post({
            url: `${window.API_URL}recoverpwd.json`,
            data: {
               token: token,
               password: password
            },
            failMessage: "Could not set the password."
         })
   }

   verifyToken(token, type){
      return window.connection.post({
            url: `${window.API_URL}verifytoken.json`,
            data: {
               token: token,
               type: type
            }
         })
   }

   consent(){
      return window.connection.post({
         url: `${window.API_URL}consent.json`,
         data: {
            consent: 1
         },
         failMessage: "Could not save the consent."
      })
            .done(response => {
               this.data.consent = true
               this.trigger("authChanged")
            })
   }

   logout(){
      this.data.isCheckingAuth = true
      this.trigger("checkingAuthChanged")
      return window.connection.post({
         url: `${window.API_URL}logout.json`,
         failMessage: "Could not log out.",
         ignoreUnauthorized: true
      })
            .done(() => {
               this.data.authorized = false;
               this.resetUser()
               route("/")
               this.trigger("authChanged")
            })
            .always(() => {
               this.data.isCheckingAuth = false
               this.trigger("checkingAuthChanged")
            })
   }

   invalidateSession(){
      if(this.data.authorized){
         this.data.authorized = false;
         this.resetUser()
         this.trigger("authChanged")
         window.showToast("Your session has expired.")
      }
   }

   _getCookie(val) {
      if (document.cookie != undefined) {
         if (document.cookie.split('; ').find(row => row.startsWith(val+'=')) != undefined) {
            return document.cookie.split('; ').find(row => row.startsWith(val+'=')).split('=')[1].slice(1,-1)
         }
      }
      return ""
   }
}

window.auth = new AuthClass()
