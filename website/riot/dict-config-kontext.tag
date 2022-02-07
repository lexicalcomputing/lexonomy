<dict-config-kontext>
	<dict-config-nav dictId={ this.dictId } dictTitle={ this.props.dictDetails.title } configId={ this.configId } configTitle={ this.configTitle }/>
	<div>
		<div class="row">
			<h4>KonText connection</h4>
		</div>
			<div class="row">
        <div class="input-field col s10">
          <input value={ this.configData.url } placeholder="" id="kontext_url" type="text" class=""/>
					<label for="kontext_url">KonText URL</label>
					<span class="helper-text">The URL of the KonText installation where external links should point. Defaults to <tt>https://www.clarin.si/kontext/</tt>. Do not change this unless you are using a local installation of KonText.</span>
				</div>
			</div>
				<div class="row">
					<div class="input-field col s10">
						<input data-selected-corpus={ this.configData.corpus } type="text" id="corpus" class="autocomplete" placeholder="Retrieving available corpora from KonText, please wait...">
						<label for="corpus">Corpus name</label>
						<span class="helper-text">Select a Sketch Engine corpus from the list of corpora available to you.</span>
						<span class="helper-text" id="corpusInfo" hide={ true }></span>
					</div>
				</div>
				<div class="row">
					<div class="input-field col s10">
						<input value={ this.configData.concquery} placeholder="" id="concquery" type="text" class=""/>
						<label for="concquery">Concordance query</label>
						<span class="helper-text">The CQL query that will be used to obtain concordance from KonText. You can use placeholders for elements in the form of '%(element)', e.g. '[lemma="%(headword)"]'. If left empty the 'simple' query type will be used as configured for the respective corpus. Please note that you cannot use CQL syntax with default attribute because it is not specified.</span>
					</div>
				</div>
				<div class="row">
					<div class="input-field col s10">
						<select id="searchElements" multiple>
						</select>
						<label for="searchElements">Additional search elements</label>
						<span class="helper-text">You can select any textual elements here whose content you would like to search for in KonText. A menu will be displayed next to all these elements like for the root entry element.</span>
					</div>
				</div>
			<div class="row">
				<h4>Examples</h4>
			</div>
			<div class="row">
				<div class="input-field col s10">
					<select id="container">
						<option value="">(not set)</option>
					</select>
					<label for="container">Example container</label>
					<span class="helper-text">Select the element which should wrap each individual example. When you pull example sentences automatically from a corpus, Lexonomy will insert one of these elements for each example sentence.</span>
				</div>
			</div>
			<div class="row">
				<div class="input-field col s10">
					<textarea id="template" class="materialize-textarea" placeholder="XML template">{ this.configData.template }</textarea>
					<label for="template">XML template</label>
					<span class="helper-text">This is the XML that will be inserted into your entries with each corpus example. The actual text will be where the placeholder <tt>$text</tt> is.</span>
				</div>
			</div>
			<div class="row">
				<div class="input-field col s10">
					<select id="markup">
						<option value="">(not set)</option>
					</select>
					<label for="markup">Headword mark-up</label>
					<span class="helper-text">Select the element which should mark up the headword in inserted corpus examples. This setting is optional: if you make no selection, corpus examples will be inserted without mark-up.</span>
				</div>
			</div>
			<button class="btn waves-effect waves-light" onclick={ saveData } id="submit_button">Save <i class="material-icons right">save</i>
			</button>
	</div>
	<style>
		#searchElements {
			width: 10em;
		}
	</style>
	<script>
		export default {
			dictId: '',
			configId: '',
			configTitle: 'KonText connection', 
			configData: {
				url: 'https://www.clarin.si/kontext/', searchElements: [],
				container: '', template: '', markup: ''
			},
		
			onMounted() {
				this.dictId = this.props.dictId;
				this.configId = this.props.configId;
				console.log('config dict '+ this.dictId + '-' + this.configId)
				this.props.loadDictDetail();
				this.fillConfigForm();
				M.updateTextFields();
			},

			onUpdated() {
				if (this.props.dictConfigs.xema && this.props.dictConfigs.xema.elements) {
					if ($('#searchElements option').length == 0) {
						Object.entries(this.props.dictConfigs.xema.elements).forEach(([key, info]) => {
							if (info.filling == 'txt' || info.filling == 'lst') {
								var checked = this.configData.searchElements.includes(key)? 'checked':'';
								$('#searchElements').append('<option value="' + key + '" ' + checked + '>' + key + '</option>');
							}
						});
					}
					if ($('#container option').length == 1) {
						Object.entries(this.props.dictConfigs.xema.elements).forEach(([key, info]) => {
								var checked = (this.configData.container == key)? 'checked':'';
								$('#container').append('<option value="' + key + '" ' + checked + '>' + key + '</option>');
						});
					}
					if ($('#markup option').length == 1) {
						Object.entries(this.props.dictConfigs.xema.elements).forEach(([key, info]) => {
								var checked = (this.configData.markup == key)? 'checked':'';
								$('#markup').append('<option value="' + key + '" ' + checked + '>' + key + '</option>');
						});
					}
					$('select').formSelect();
				}
			},

			async fillConfigForm() {
				this.props.loadConfigData(this.configId).then((response)=>{
					this.configData = response;
					if (!response.url || response.url == '') {
						this.configData.url = 'https://www.clarin.si/kontext/';
					}
					if (!response.searchElements) {
						this.configData.searchElements = [];
					}
					M.updateTextFields();
					M.textareaAutoResize($('#template'));
					$('#corpus').autocomplete({data: {}});
					$('#corpus').data('corpora', {});
					if (this.configData.corpus != '') {
						$('#corpus').data('selected-corpora', this.configData.corpus);
					}
					$.get({
						url: '/' + this.dictId + '/kontext/corpora'
					}).done(function(res) {
						var corporaList = {};
						var corporaData = {};
						var selected = '';
						res.corpus_list.forEach(e => {
							var eInfo = e.name + " (" + e.desc + "; " + e.size_info + ")";
							corporaData[eInfo] = e.corpus_id;
							corporaList[eInfo] = null;
							if ($('#corpus').data('selected-corpus') == e.corpus_id) {
								selected = eInfo;
								$('#corpusInfo').html('Currently selected corpus: ' + e.name + ".");
								$('#corpusInfo').show();
							}
						});
						$('#corpus').autocomplete({data: corporaList});
						$('#corpus').data('corpora', corporaData);
						$('#corpus').attr('placeholder', 'Type to search in the list of corpora');
						if (selected != '') {
							$('#corpus').val(selected);
						}
					});
					$('#corpus').on('change', function() {
						var corporaData = $(this).data('corpora')
						$(this).data('selected-corpus', corporaData[$(this).val()]);
						$('#corpusInfo').html('Currently selected corpus: ' + $(this).val() + ".");
						$('#corpusInfo').show();
					});

					this.configData.searchElements.forEach(el => {
						$('#searchElements option[value='+el+']').attr('selected','selected');
					});
					if (this.configData.container != '') {
						$('#container option[value='+this.configData.container+']').attr('selected','selected');
					}
					if (this.configData.markup != '') {
						$('#markup option[value='+this.configData.markup+']').attr('selected','selected');
					}
					$('select').formSelect();
					this.update();
				});
			},

			getConfigData() {
				var newData = {
					url: $('#kontext_url').val(),
					corpus: $('#corpus').data('selected-corpus'),
					concquery: $('#concquery').val(),
					searchElements: $('#searchElements').val(),
					container: $('#container').val(),
					template: $('#template').val(),
					markup: $('#markup').val(),
				};
				return newData;
			},

			saveData() {
				console.log(this.getConfigData())
				$('#submit_button').html('Saving...');
				this.props.saveConfigData(this.configId, this.getConfigData());
			}
		}
	</script>
	
</dict-config-kontext>