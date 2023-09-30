import {register as riot_register, component} from 'riot'

import './js/store.js'
import './js/auth.js'
import './js/extend-riot.js'
import './js/appupdater.js'
import './js/url.js'
import './js/misc.js'
import './libs/js.cookie.js'
import './libs/codejar/codejar.js'
import './widgets/xema-designer.js'
import './libs/jsdiff/jsdiff.js'
import './js/nvh-store.js'
import './js/nvh-plugins/ske.js'
import './js/nvh-plugins/image-search.js'
import './js/nvh-plugins/voice-rss.js'
import './js/nvh-plugins/links.js'
import './js/extendmaterialize.js'

import App from './riot/main.riot'
import api from './riot/api.riot'
import admin_dicts from './riot/admin-dicts.riot'
import admin_users from './riot/admin-users.riot'
import admin_users_add from './riot/admin-users-add.riot'
import dict_config_autonumber from './riot/dict-config-autonumber.riot'
import dict_config_editing from './riot/dict-config-editing.riot'
import dict_config_flagging from './riot/dict-config-flagging.riot'
import dict_config_gapi from './riot/dict-config-gapi.riot'
import dict_config_ident from './riot/dict-config-ident.riot'
import dict_config_kontext from './riot/dict-config-kontext.riot'
import dict_config_links from './riot/dict-config-links.riot'
import dict_nav from './riot/dict-nav.riot'
import dict_entry_filter from './riot/dict-entry-filter.riot'
import dict_config_buttons from './riot/dict-config-buttons.riot'
import dict_config_publico from './riot/dict-config-publico.riot'
import dict_config_searchability from './riot/dict-config-searchability.riot'
import dict_config_ske from './riot/dict-config-ske.riot'
import dict_config from './riot/dict-config.riot'
import dict_config_titling from './riot/dict-config-titling.riot'
import dict_config_url from './riot/dict-config-url.riot'
import dict_config_users from './riot/dict-config-users.riot'
import dict_config_structure from './riot/dict-config-structure.riot'
import dict_config_limits from './riot/dict-config-limits.riot'
import dict_download from './riot/dict-download.riot'
import dict_edit_entry from './riot/dict-edit-entry.riot'
import dict_edit from './riot/dict-edit.riot'
import dictionaries from './riot/dictionaries.riot'
import new_dictionary from './riot/new-dictionary.riot'
import dict_public_entry from './riot/dict-public-entry.riot'
import dict_public from './riot/dict-public.riot'
import dict_upload from './riot/dict-upload.riot'
import dict_links from './riot/dict-links.riot'
import dict_favorite_toggle from './riot/dict-favorite-toggle.riot'
import e404 from './riot/e404.riot'
import entry_view from './riot/entry-view.riot'
import app_footer from './riot/app-footer.riot'
import feedback_dialog from './riot/feedback-dialog.riot'
import forgot_password from './riot/forgot-password.riot'
import forgot from './riot/forgot.riot'
import app_header from './riot/app-header.riot'
import login from './riot/login.riot'
import main from './riot/main.riot'
import open_dictionaries from './riot/open-dictionaries.riot'
import register_password from './riot/register-password.riot'
import register from './riot/register.riot'
import user_profile from './riot/user-profile.riot'
import welcome from './riot/welcome.riot'
import user_consent from './riot/user-consent.riot'
import raw_html from './riot/raw-html.riot'
import loading_overlay from './riot/loading-overlay.riot'
import docs_intro from './riot/docs-intro.riot'
import modal_dialog from './riot/modal-dialog.riot'
import help_dialog from './riot/help-dialog.riot'
import dict_description_dialog from './riot/dict-description-dialog.riot'
import unauthorized from './riot/unauthorized.riot'
import nvh_editor from './riot/nvh-editor/nvh-editor.riot'
import nvh_editor_edit_item from './riot/nvh-editor/nvh-editor-edit-item.riot'
import nvh_editor_view_item from './riot/nvh-editor/nvh-editor-view-item.riot'
import nvh_editor_toolbar from './riot/nvh-editor/nvh-editor-toolbar.riot'
import nvh_editor_context_menu from './riot/nvh-editor/nvh-editor-context-menu.riot'
import nvh_dnd_zone from './riot/nvh-editor/nvh-dnd-zone.riot'
import nvh_source_code from './riot/nvh-editor/nvh-source-code.riot'
import nvh_item_media from './riot/nvh-editor/nvh-item-media.riot'
import nvh_element_style_editor from './riot/nvh-editor/nvh-element-style-editor.riot'
import nvh_editor_item_toolbar from './riot/nvh-editor/nvh-editor-item-toolbar.riot'
import nvh_item_value_editor from './riot/nvh-editor/nvh-item-value-editor.riot'
import nvh_side_dnd_panel from './riot/nvh-editor/nvh-side-dnd-panel.riot'
import nvh_revisions from './riot/nvh-editor/nvh-revisions.riot'
import nvh_custom_editor from './riot/nvh-editor/nvh-custom-editor.riot'
import nvh_widget_panel from './riot/nvh-editor/nvh-widget-panel.riot'
import nvh_plugin_buttons from './riot/nvh-editor/nvh-plugin-buttons.riot'
import nvh_ske_dialog from './riot/nvh-editor/plugins/nvh-ske-dialog.riot'
import nvh_links_dialog from './riot/nvh-editor/plugins/nvh-links-dialog.riot'

riot_register('api', api)
riot_register('admin-dicts', admin_dicts)
riot_register('admin-users', admin_users)
riot_register('admin-users-add', admin_users_add)
riot_register('dict-config-autonumber', dict_config_autonumber)
riot_register('dict-config-editing', dict_config_editing)
riot_register('dict-config-flagging', dict_config_flagging)
riot_register('dict-config-gapi', dict_config_gapi)
riot_register('dict-config-ident', dict_config_ident)
riot_register('dict-config-kontext', dict_config_kontext)
riot_register('dict-config-links', dict_config_links)
riot_register('dict-nav', dict_nav)
riot_register('dict-entry-filter', dict_entry_filter)
riot_register('dict-config-buttons', dict_config_buttons)
riot_register('dict-config-publico', dict_config_publico)
riot_register('dict-config-searchability', dict_config_searchability)
riot_register('dict-config-ske', dict_config_ske)
riot_register('dict-config', dict_config)
riot_register('dict-config-titling', dict_config_titling)
riot_register('dict-config-url', dict_config_url)
riot_register('dict-config-users', dict_config_users)
riot_register('dict-config-structure', dict_config_structure)
riot_register('dict-config-limits', dict_config_limits)
riot_register('dict-download', dict_download)
riot_register('dict-edit-entry', dict_edit_entry)
riot_register('dict-edit', dict_edit)
riot_register('dictionaries', dictionaries)
riot_register('new-dictionary', new_dictionary)
riot_register('dict-public-entry', dict_public_entry)
riot_register('dict-public', dict_public)
riot_register('dict-upload', dict_upload)
riot_register('dict-links', dict_links)
riot_register('dict-favorite-toggle', dict_favorite_toggle)
riot_register('e404', e404)
riot_register('entry-view', entry_view)
riot_register('app-footer', app_footer)
riot_register('feedback-dialog', feedback_dialog)
riot_register('forgot-password', forgot_password)
riot_register('forgot', forgot)
riot_register('app-header', app_header)
riot_register('login', login)
riot_register('main', main)
riot_register('open-dictionaries', open_dictionaries);
riot_register('register-password', register_password)
riot_register('register', register)
riot_register('user-profile', user_profile)
riot_register('welcome', welcome)
riot_register('user-consent', user_consent)
riot_register('raw-html', raw_html)
riot_register('loading-overlay', loading_overlay)
riot_register('docs-intro', docs_intro)
riot_register('modal-dialog', modal_dialog)
riot_register('help-dialog', help_dialog)
riot_register('dict-description-dialog', dict_description_dialog)
riot_register('unauthorized', unauthorized)
riot_register('nvh-editor', nvh_editor)
riot_register('nvh-editor-edit-item', nvh_editor_edit_item)
riot_register('nvh-editor-view-item', nvh_editor_view_item)
riot_register('nvh-editor-toolbar', nvh_editor_toolbar)
riot_register('nvh-editor-context-menu', nvh_editor_context_menu)
riot_register('nvh-dnd-zone', nvh_dnd_zone)
riot_register('nvh-source-code', nvh_source_code)
riot_register('nvh-item-media', nvh_item_media)
riot_register('nvh-element-style-editor', nvh_element_style_editor)
riot_register('nvh-editor-item-toolbar', nvh_editor_item_toolbar)
riot_register('nvh-item-value-editor', nvh_item_value_editor)
riot_register('nvh-side-dnd-panel', nvh_side_dnd_panel)
riot_register('nvh-revisions', nvh_revisions)
riot_register('nvh-custom-editor', nvh_custom_editor)
riot_register('nvh-widget-panel', nvh_widget_panel)
riot_register('nvh-plugin-buttons', nvh_plugin_buttons)
riot_register('nvh-ske-dialog', nvh_ske_dialog)
riot_register('nvh-links-dialog', nvh_links_dialog)

component(App)(document.getElementById('root'))
