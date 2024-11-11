import riot from 'rollup-plugin-riot'
import nodeResolve from '@rollup/plugin-node-resolve'
import { registerPreprocessor } from '@riotjs/compiler'
import sass from 'sass'
import fs from  "fs"
import path from "path"
import css from "rollup-plugin-import-css"
import { terser } from "rollup-plugin-terser"



let walk = function(dir) {
   // find all files in directory and its subdirectories
   let results = []
   let list = fs.readdirSync(dir)
   list.forEach(file => {
      file = path.join(dir, file)
      let stat = fs.statSync(file)
      if (stat && stat.isDirectory()) {
            results = results.concat(walk(file))
      } else {
            results.push(file.split(path.sep).join("/"))
      }
   })
   return results
}

function createAppJs(){
   // create app.js file to import and register all .riot components
   let lines = []

   walk("./riot").forEach(f => {
      let fileName = path.basename(f, ".riot")
      let normalizedName = fileName.replaceAll("-", "_")
      lines.push(`import ${normalizedName} from "./${f}"`)
      lines.push(`riot_register("${fileName}", ${normalizedName})`)
   })
   let riotRegisterComponents = lines.sort().join("\n")

   let appTemplate = fs.readFileSync("./app.js.template", {encoding:"utf8", flag:"r"})
   let appFile = appTemplate.replace("@RIOT_REGISTER_COMPONENTS@", riotRegisterComponents)

   fs.writeFileSync("app.js", appFile)
}
createAppJs()

registerPreprocessor('css', 'scss', function(code, { options }) {
  const {css} = sass.renderSync({
    data: code
  })
  return {
    code: css.toString(),
    map: null
  }
})

export default [{
  input: 'app.js',
  output: {
    file: 'bundle.js',
    format: 'iife',
    strict: false
  },
  plugins: [
    {
      buildStart() {
        console.log('building Lexonomy...');
      },
    },
    riot(),
    terser(),
    nodeResolve()
  ]
}, {
  input: 'app.static.js',
  context: "window",
  output: {
    file: 'bundle.static.js',
    format: 'iife',
    strict: false
  },
  plugins: [terser(), nodeResolve()]
}, {
  input: "app.css.js",
  output: {
    file: "bundle.css"
  },
  plugins: [
    css(),
    nodeResolve()
  ]
}]
