// build bundle using npx rollup -c rollup.config.codemirror.js

import {EditorView, basicSetup} from "codemirror"
import {javascript} from "@codemirror/lang-javascript"
import {css} from "@codemirror/lang-css"

window.CodeMirror = {
  EditorView,
  basicSetup,
  javascript,
  css
}

