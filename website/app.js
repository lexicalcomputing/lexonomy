import {register as riot_register, component} from 'riot'

import './js/dispatcher.js'
import './js/connection.js'
import './js/store.js'
import './js/auth.js'
import './js/extend-riot.js'
import './js/appupdater.js'
import './js/url.js'
import './js/misc.js'
import './js/configuration-checker.js'
import './libs/js.cookie.js'
import './libs/codejar/codejar.js'
import './libs/jsdiff/jsdiff.js'
import './libs/cssparser/cssparser.js'
import './js/nvh-store.js'
import './js/nvh-plugins/ske.js'
import './js/nvh-plugins/image-search.js'
import './js/nvh-plugins/voice-rss.js'
import './js/nvh-plugins/links.js'
import './js/extendmaterialize.js'
import './js/structure-editor-store.js'
import './js/formatter.js'
import './js/customstyles.js'
import './js/browser-update.js'

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
import dict_config_formatting from './riot/dict-config-formatting.riot'
import dict_download from './riot/dict-download.riot'
import dict_edit from './riot/dict-edit.riot'
import dictionaries from './riot/dictionaries.riot'
import new_dictionary from './riot/new-dictionary.riot'
import dict_public from './riot/dict-public.riot'
import dict_upload from './riot/dict-upload.riot'
import dict_links from './riot/dict-links.riot'
import dict_favorite_toggle from './riot/dict-favorite-toggle.riot'
import e404 from './riot/e404.riot'
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
import nvh_schema from './riot/nvh-schema.riot'
import structure_editor from './riot/structure-editor.riot'
import structure_editor_item from './riot/structure-editor-item.riot'
import structure_dnd_zone from './riot/structure-dnd-zone.riot'
import trim_text from './riot/trim-text.riot'
import entry_list from './riot/entry-list.riot'
import advanced_query_builder from './riot/advanced-query-builder.riot'
import advanced_query_group from './riot/advanced-query-group.riot'
import advanced_query_rule from './riot/advanced-query-rule.riot'
import element_select from './riot/element-select.riot'
import element_style_options from './riot/element-style-options.riot'
import lazy_dropdown from './riot/lazy-dropdown.riot'
import entry_dropdown from './riot/entry-dropdown.riot'
import user_dropdown from './riot/user-dropdown.riot'
import projects_dashboard from './riot/projects/projects-dashboard.riot'
import projects_new from './riot/projects/projects-new.riot'
import projects_view from './riot/projects/projects-view.riot'
import projects_edit from './riot/projects/projects-edit.riot'
import project_dict_name from './riot/projects/project-dict-name.riot'
import project_batches from './riot/projects/project-batches.riot'
import project_dictionary_status from './riot/projects/project-dictionary-status.riot'
import dict_config_styles from './riot/dict-config-styles.riot'
import nvh_schema_textarea from './riot/nvh-schema-textarea.riot'
import nvh_schema_syntax_help from './riot/nvh-schema-syntax-help.riot'
import site_notification from './riot/site-notification.riot'
import config_issues_icon from './riot/config-issues-icon.riot'
import config_issues_dialog from './riot/config-issues-dialog.riot'
import dict_configuration_issues from './riot/dict-configuration-issues.riot'
import project_export_to_batches_form from './riot/projects/project-export-to-batches-form.riot'

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
riot_register('dict-edit', dict_edit)
riot_register('dictionaries', dictionaries)
riot_register('new-dictionary', new_dictionary)
riot_register('dict-public', dict_public)
riot_register('dict-upload', dict_upload)
riot_register('dict-links', dict_links)
riot_register('dict-favorite-toggle', dict_favorite_toggle)
riot_register('e404', e404)
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
riot_register('nvh-schema', nvh_schema)
riot_register('structure-editor', structure_editor)
riot_register('structure-editor-item', structure_editor_item)
riot_register('structure-dnd-zone', structure_dnd_zone)
riot_register('trim-text', trim_text)
riot_register('entry-list', entry_list)
riot_register('advanced-query-builder', advanced_query_builder)
riot_register('advanced-query-group', advanced_query_group)
riot_register('advanced-query-rule', advanced_query_rule)
riot_register('element-select', element_select)
riot_register('dict-config-formatting', dict_config_formatting)
riot_register('element-style-options', element_style_options)
riot_register('lazy-dropdown', lazy_dropdown)
riot_register('entry-dropdown', entry_dropdown)
riot_register('user-dropdown', user_dropdown)
riot_register('projects-dashboard', projects_dashboard)
riot_register('projects-new', projects_new)
riot_register('projects-view', projects_view)
riot_register('projects-edit', projects_edit)
riot_register('project-dict-name', project_dict_name)
riot_register('project-batches', project_batches)
riot_register('project-dictionary-status', project_dictionary_status)
riot_register('dict-config-styles', dict_config_styles)
riot_register('nvh-schema-textarea', nvh_schema_textarea)
riot_register('nvh-schema-syntax-help', nvh_schema_syntax_help)
riot_register('site-notification', site_notification)
riot_register('config-issues-icon', config_issues_icon)
riot_register('config-issues-dialog', config_issues_dialog)
riot_register('dict-configuration-issues', dict_configuration_issues)
riot_register('project-export-to-batches-form', project_export_to_batches_form)


component(App)(document.getElementById('root'))
