import nodeResolve from '@rollup/plugin-node-resolve'
import {terser} from "rollup-plugin-terser"


export default [{
  input: "codemirror.js",
  output: {
    file: "bundle.codemirror.js",
    format: "iife"
  },
  plugins: [nodeResolve(), terser()]
}]
