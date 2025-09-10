#!/usr/bin/python3

import os
import re
import ops
import json
import shlex
import shutil
import datetime
import subprocess
from refresh_project_state import refresh_selected_stages

currdir = os.path.dirname(os.path.abspath(__file__))
siteconfig = json.load(open(os.path.join(currdir, "siteconfig.json"), encoding="utf-8"))


def projectExists(projectID):
    return os.path.isdir(os.path.join(siteconfig["dataDir"], "projects", projectID))

def setProjectManager(email, is_manager):
    error = ''
    try:
        conn = ops.getMainDB()
        conn.execute("UPDATE users SET is_manager=? WHERE email=?",
                     (is_manager, email))
        conn.commit()
        conn.close()
    except:
        error = 'Main DB error'

    return email, is_manager, error

def suggestProjectId():
    projectid = ops.generateDictId()
    while projectid in ops.prohibitedDictIDs or projectExists(projectid):
        projectid = ops.generateDictId()
    return projectid


def getProjectsByUser(user):
    active_projects = []
    archived_projects = []
    conn = ops.getMainDB()
    c = conn.execute("SELECT DISTINCT project_id FROM user_projects WHERE user_email=?",
                     (user["email"],))

    for r in c.fetchall():
        project_info = getProject(r["project_id"])
        if project_info["active"] == 1:
            active_projects.append({"projectID": project_info["projectID"], "project_name": project_info["project_name"],
                                    "description": project_info["description"], "language": project_info["language"],
                                    "managers": project_info["managers"], "source_dict": project_info["source_dict"],
                                    "stages": [x['stage'] for x in project_info["workflow"]], 'ref_corpus': project_info['ref_corpus'],
                                    "active": 1})
        else:
            archived_projects.append({"projectID": project_info["projectID"], "project_name": project_info["project_name"],
                                      "description": project_info["description"], "language": project_info["language"],
                                      "managers": project_info["managers"], "source_dict": project_info["source_dict"],
                                      "stages": [x['stage'] for x in project_info["workflow"]], 'ref_corpus': project_info['ref_corpus'],
                                      "archived": 1})

    total = len(active_projects) + len(archived_projects)
    return {"projects_active": active_projects, "projects_archived": archived_projects, "total": total}


def add_project_staff(conn, project_id, project_name, project_staff, role, user):
    new_created_users = []
    c = conn.execute("SELECT email FROM users")
    all_users = set()
    for r in c.fetchall():
        all_users.add(r['email'])

    # Adding annotators
    for annotator in project_staff:
        if not annotator in all_users:
            if role == 'manager':
                ops.createUser(annotator, user, manager=1)
            else:
                ops.createUser(annotator, user)
            new_created_users.append(annotator)

        conn.execute("INSERT INTO user_projects (project_id, project_name, user_email, role)"\
                     " VALUES (?,?,?,?)", (project_id, project_name, annotator, role))
        conn.commit()
    return new_created_users


def project_init_git(path):
    # TODO log git ??
    subprocess.run(['git', 'init', '-q'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=path)
    subprocess.run(['git', 'lfs', 'install'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=path)
    subprocess.run(['git', 'lfs', 'track', '*.nvh', '*.in', '*.rejected', '*.nvh.patch'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=path)
    with open(os.path.join(path, '.gitignore'), 'w') as f:
        f.write('*.log')
    subprocess.run(['git', 'add', '-A'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=path)
    subprocess.run(['git', 'commit', '-m', 'init', '-q'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=path)
    subprocess.run(['git', 'config', 'advice.addIgnoredFile', 'false'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=path)
    subprocess.run(['git', 'config', 'user.email', 'apache'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=path)
    subprocess.run(['git', 'config', 'user.name', 'apache'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=path)


def project_git_commit(path, msg, stage=''):
    subprocess.run(['git', 'add', '-A', stage], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=path)
    subprocess.run(['git', 'commit', '-m', msg, '-q'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=path)


def createProject(project_id, project_name, project_description, project_annotators, project_managers, ref_corpus, src_dict_id, workflow_id, langauge, user):
    if projectExists(project_id):
        return {'success': False, "projectID": project_id, "error": "The project with the entered name already exists"}
    if not workflow_id:
        return {'success': False, "projectID": project_id, "error": "Workflow not specified."}
    if not os.path.isdir(os.path.join(currdir, 'workflows', workflow_id)):
        return {'success': False, "projectID": project_id, "error": "Can not find workflow template."}

    os.makedirs(os.path.join(siteconfig["dataDir"], "projects", project_id))

    # Copy workflow
    for file in os.listdir(os.path.join(currdir, 'workflows', workflow_id)):
        if file == 'Makefile':
            with open(os.path.join(siteconfig["dataDir"], "projects", project_id, 'Makefile'), 'w') as dest:
                with open(os.path.join(currdir, 'workflows', workflow_id, 'Makefile'), 'r') as source:
                    for line in source:
                        dest.write(re.sub('%dir%', currdir, line))
        else:
            shutil.copy2(os.path.join(currdir, 'workflows', workflow_id, file), os.path.join(siteconfig["dataDir"], "projects", project_id))

    # Dump source dict to NVH
    with open(os.path.join(siteconfig["dataDir"], "projects", project_id, src_dict_id+'.nvh'), 'w') as f:
        for nvh in ops.download(ops.getDB(src_dict_id), src_dict_id, 'nvh'):
            f.write(nvh)

    project_init_git(os.path.join(siteconfig["dataDir"], "projects", project_id))

    conn = ops.getMainDB()
    conn.execute("INSERT INTO projects (id, project_name, description, ref_corpus, src_dic_id, language, active, workflow_id)"\
                 " VALUES (?,?,?,?,?,?,?,?)", (project_id, project_name, project_description, ref_corpus, src_dict_id, langauge, 1, workflow_id))
    conn.execute("INSERT INTO project_dicts (project_id, dict_id, source_nvh, stage) VALUES (?,?,?,?)",
                 (project_id, src_dict_id, os.path.join(siteconfig["dataDir"], "projects", project_id, src_dict_id+'.nvh'), '__nvh_source__'))
    conn.commit()

    new_created_users = []
    for role, annotator_list in project_annotators.items():
        new_created_users += add_project_staff(conn, project_id, project_name, annotator_list, role, user)
    new_created_users += add_project_staff(conn, project_id, project_name, project_managers, 'manager', user)

    project_info = getProject(project_id)
    all_stages = [s['stage'] for s in project_info['workflow']]
    refresh_selected_stages(project_id, all_stages)

    return {'success': True , "projectID": project_id, 'new_reated_users': json.dumps(new_created_users)}


def editProject(project_id, project_name, project_description, project_annotators, project_managers, user):
    conn = ops.getMainDB()
    conn.execute("UPDATE projects SET description=?, project_name=? where id=?",
                 (project_description, project_name, project_id))
    conn.execute("DELETE FROM user_projects WHERE project_id=?", (project_id,))
    conn.commit()

    new_created_users = []
    for role, annotator_list in project_annotators.items():
        new_created_users += add_project_staff(conn, project_id, project_name, annotator_list, role, user)
    new_created_users += add_project_staff(conn, project_id, project_name, project_managers, 'manager', user)
    return {"success": True, "projectID": project_name, 'new_reated_users': json.dumps(new_created_users)}


def update_project_source_dict(project_id, src_dict_id):
    conn = ops.getMainDB()
    q =  conn.execute("SELECT src_dic_id FROM projects WHERE id=?", (project_id,))
    r = q.fetchone()
    # Make copy of old source
    if os.path.exists(os.path.join(siteconfig["dataDir"], "projects", project_id, r['src_dic_id']+'.nvh')):
        shutil.move(os.path.join(siteconfig["dataDir"], "projects", project_id, r['src_dic_id']+'.nvh'),
                    os.path.join(siteconfig["dataDir"], "projects", project_id, r['src_dic_id']+'.nvh_'+datetime.datetime.now().strftime("%Y-%m-%d_%H_%M_%S")))


    with open(os.path.join(siteconfig["dataDir"], "projects", project_id, src_dict_id+'.nvh'), 'w') as f:
        for nvh in ops.download(ops.getDB(src_dict_id), src_dict_id, 'nvh'):
            f.write(nvh)

    conn.execute("UPDATE projects SET src_dic_id=? WHERE id=?", (src_dict_id, project_id))
    conn.execute("UPDATE project_dicts SET source_nvh=?, dict_id=? WHERE project_id=? AND stage=?",
                 (os.path.join(siteconfig["dataDir"], "projects", project_id, src_dict_id+'.nvh'), src_dict_id, project_id, '__nvh_source__'))
    conn.commit()

    project_info = getProject(project_id)
    all_stages = [s['stage'] for s in project_info['workflow']]
    refresh_selected_stages(project_id, all_stages)

    return {'success': True , "projectID": project_id}

def getProjectStageState(projectID, stage):
    phase_stack = []
    log_filename = os.path.join(siteconfig["dataDir"], "projects", projectID, stage+'.log')
    if os.path.isfile(log_filename):
        with open(log_filename, 'r') as sf:
            for line in sf:
                if line.startswith('_LOCK_'):
                    phase_stack.append(line.strip()[6:])
                elif line.startswith('_UNLOCK_') and phase_stack[-1] == line.strip()[8:]:
                    phase_stack.pop()
    return phase_stack


def getMakeDeps(make_file):
    def add_data(data_dict, stage_name, data_name, data):
        if not data_dict.get(stage_name, False):
            data_dict[stage_name] = {data_name: data}
        else:
            data_dict[stage_name][data_name] = data

    stage_pretty_name_re = re.compile('^(.*)_TITLE="(.*)"$')
    stage_description_re = re.compile('^(.*)_DESCRIPTION="(.*)"$')
    stage_annot_name_re = re.compile('^(.*)_ANNOTATOR_NAME="(.*)"$')
    stage_query_re = re.compile('^(.*)_QUERY="(.*)"$')
    stage_type_re = re.compile('^(.*)_TYPE="(.*)"$')

    tl_node_re = re.compile('^TL_NODE="(.*)"$')
    target_line_re = re.compile('^(.*?).nvh:\s*(.*?)$')
    from collections import OrderedDict
    make_data = OrderedDict()

    tl_node = 'entry'

    with open(make_file, 'r') as f:
        for line in f:
            target_line = target_line_re.match(line)
            stage_pretty_name_line = stage_pretty_name_re.match(line)
            stage_description_line = stage_description_re.match(line)
            stage_annot_name_line = stage_annot_name_re.match(line)
            stage_query_line = stage_query_re.match(line)
            stage_type = stage_type_re.match(line)
            tl_node_line = tl_node_re.match(line)
            if target_line:
                sources = []
                stage = target_line.group(1)
                prerequisites = target_line.group(2).split()
                for s in prerequisites:
                    if s == '$(SOURCE_DICT)':
                        sources.append('__nvh_source__')
                    elif s.endswith('.nvh'):
                        sources.append(f'{s[:-4]}_stage')
                    else:
                        continue

                add_data(make_data, stage, 'sources', sources)
                # add_data(make_data, stage, 'id', stage)

            elif stage_pretty_name_line:
                add_data(make_data, stage_pretty_name_line.group(1).lower(), 'title', stage_pretty_name_line.group(2))

            elif stage_description_line:
                add_data(make_data, stage_description_line.group(1).lower(), 'description', stage_description_line.group(2))

            elif stage_annot_name_line:
                add_data(make_data, stage_annot_name_line.group(1).lower(), 'annotator_name', stage_annot_name_line.group(2))

            elif stage_query_line:
                add_data(make_data, stage_query_line.group(1).lower(), 'query', stage_query_line.group(2))
            
            elif stage_type:
                add_data(make_data, stage_type.group(1).lower(), 'type', stage_type.group(2))

            elif tl_node_line:
                tl_node = tl_node_line.group(1)

    return make_data, tl_node


def getProject(projectID):
    workflow_stages = []
    conn = ops.getMainDB()

    # ======================
    # Stage info in DB
    # ======================
    c1 = conn.execute("SELECT p.dict_id, p.stage, p.remaining, p.created, p.assignee, p.status, d.title "
                      "FROM project_dicts AS p INNER JOIN dicts AS d ON p.dict_id == d.id "
                      "WHERE p.project_id=?", (projectID,))
    r1 = c1.fetchall()

    stage_dicts_info = {}
    for i in r1: 
        if stage_dicts_info.get(i['stage']):
            stage_dicts_info[i['stage']].append({'dict_id': i['dict_id'], 'remaining': json.loads(i['remaining']), 
                                                 'title': i['title'], 'created': i['created'], 
                                                 'assignee': i['assignee'], 'status': i['status']})
        else:
            stage_dicts_info[i['stage']] = [{'dict_id': i['dict_id'], 'remaining': json.loads(i['remaining']), 
                                             'title': i['title'], 'created': i['created'], 
                                             'assignee': i['assignee'], 'status': i['status']}]

    # ======================
    # Stage dependencies
    # ======================
    make_data, tl_node = getMakeDeps(os.path.join(siteconfig["dataDir"], "projects", projectID, 'Makefile'))

    for stage in make_data.keys():
        # ======================
        # Check stage status
        # ======================
        phase_stack = getProjectStageState(projectID, stage)

        # ======================
        # Check stage log
        # ======================
        stage_log = []
        log_re = re.compile(r'^(INFO|WARNING|ERROR) \[(.*)\]:\s*(.*)$')
        if os.path.exists(os.path.join(siteconfig["dataDir"], "projects", projectID, stage+'.log')):
            with open(os.path.join(siteconfig["dataDir"], "projects", projectID, stage+'.log')) as lf:
                for line in lf:
                    l = log_re.match(line)
                    if l:
                        stage_log.append((l.group(1), l.group(2), l.group(3)))

        # ======================
        # INPUT DICTS
        # ======================
        input_dicts = []
        for dict_stage in make_data[stage]['sources']:
            if stage_dicts_info.get(dict_stage, False):
                if len(stage_dicts_info[dict_stage]) > 1:
                    raise Exception('Error: Stage dict should be only one!')
                dict_info = stage_dicts_info[dict_stage][0] # stages should have just one dict

                dictDB = ops.getDB(dict_info['dict_id'])
                q = dictDB.execute("SELECT value FROM stats WHERE id='entry_count'")
                r_q = q.fetchone()
                dictDB.close()

                if dict_info['remaining'].get(stage, -1) >= 0:
                    input_dicts.append({'dictID': dict_info['dict_id'],
                                        'title': dict_info['title'],
                                        'remaining': dict_info['remaining'][stage],
                                        'total': int(r_q['value'])})
                else:
                    input_dicts.append({'dictID': dict_info['dict_id'],
                                        'title': dict_info['title'],
                                        'total': int(r_q['value'])})

            else:
                input_dicts.append({'dictID': None, 'title': re.sub('_stage', ' output', dict_stage)})
        # ======================
        # OUTPUT DICTS
        # ======================
        if stage_dicts_info.get(f'{stage}_stage', False):

            if len(stage_dicts_info[f'{stage}_stage']) > 1:
                raise Exception('Error: Stage dict should be only one!')
            dict_info = stage_dicts_info[f'{stage}_stage'][0] # stages should have just one dict

            dictDB = ops.getDB(dict_info['dict_id'])
            q = dictDB.execute("SELECT value FROM stats WHERE id='entry_count'")
            r_q = q.fetchone()
            dictDB.close()

            output_dict = {'dictID': dict_info['dict_id'], 
                           'total': int(r_q['value']),
                           'title': dict_info['title'], 
                           'created': dict_info['created']}
        else:
            output_dict = {'dictID': None, 'total': 0, 'title': f'{stage} output', 'created': ''}

        # ======================
        # BATCH DICTS
        # ======================
        batches = []

        for b in stage_dicts_info.get(stage, []):
            dictDB = ops.getDB(b['dict_id'])
            q = dictDB.execute("SELECT id, value FROM stats WHERE id IN ('entry_count', 'completed_entries')")
            r_q = q.fetchall()
            dictDB.close()
            
            entry_count = int([x['value'] for x in r_q if x['id'] == 'entry_count'][0])
            completed_entries = int([x['value'] for x in r_q if x['id'] == 'completed_entries'][0])

            if entry_count > 0 and b['status'] != 'creating':
                batches.append({'dictID': b['dict_id'], 'title': b['title'],
                                'completed': completed_entries, 'total': entry_count,
                                'completed_per': (completed_entries / entry_count) * 100,
                                'assignee': b['assignee'], 'status': b['status'],
                                'created': b['created']
                                })
            else:
                batches.append({'dictID': b['dict_id'], 'title': b['title'],
                                'assignee': b['assignee'], 'status': b['status'],
                                })

        if len(input_dicts) > 1:
            stage_type = 'merge'
        else:
            stage_type = 'batches'

        workflow_stages.append({'stage': stage, 'inputDicts': input_dicts, 'outputDict': output_dict,
                                'batches': batches, 'type': stage_type, 'is_locked': phase_stack != [],
                                'query': make_data[stage].get('query', ''),
                                'title': make_data[stage].get('title', ''),
                                'description': make_data[stage].get('description', ''),
                                'annotator_name': make_data[stage].get('annotator_name', ''),
                                'type': make_data[stage].get('type', ''),
                                'log': stage_log})


    c3 = conn.execute("SELECT project_name, description, ref_corpus, language, src_dic_id, active, workflow_id FROM projects WHERE id=?",
                      (projectID,))
    r3 = c3.fetchone()

    # ======================
    # Annotators/Managers
    # ======================
    annotators = {}
    managers = set()
    all_stages = list(make_data.keys()) + ['__all__']
    c0 = conn.execute("SELECT user_email, role FROM user_projects WHERE project_id=? ORDER BY user_email;", (projectID,))
    for r0 in c0.fetchall():
        if r0['role'] in all_stages:
            if annotators.get(r0['role']):
                annotators[r0['role']].add(r0['user_email'])
            else:
                annotators[r0['role']] = set([r0['user_email']])
        elif r0['role'] == 'manager':
            managers.add(r0['user_email'])
        else:
            raise Exception('problem in user_projects database')

    for key, value in annotators.items():
        annotators[key] = list(value)
    # ======================

    conn.close()

    return {"projectID": projectID, 'project_name': r3['project_name'], 'description': r3['description'], 'ref_corpus': r3['ref_corpus'],
            'annotators': annotators, 'managers': list(managers), 'workflow_id': r3['workflow_id'] ,'workflow': workflow_stages,
            'language': r3['language'], 'source_dict': r3['src_dic_id'], 'active': r3['active'], 'tl_node': tl_node}


def archiveProject(project_id):
    conn = ops.getMainDB()
    conn.execute("UPDATE projects SET active=? WHERE id=?", (0, project_id))
    conn.commit()
    return {"success": True, "projectID": project_id}

def unarchiveProject(project_id):
    conn = ops.getMainDB()
    conn.execute("UPDATE projects SET active=? WHERE id=?", (1, project_id))
    conn.commit()
    return {"success": True, "projectID": project_id}

def deleteProject(project_id):
    conn = ops.getMainDB()
    conn.execute("DELETE FROM projects WHERE id=?", (project_id,))
    conn.execute("DELETE FROM user_projects WHERE project_id=?", (project_id, ))
    c = conn.execute("SELECT dict_id FROM project_dicts WHERE project_id=? AND stage!=?", (project_id,'__nvh_source__'))
    destroy_dicts = []
    for r in c.fetchall():
        destroy_dicts.append(r['dict_id'])
    conn.execute("DELETE FROM project_dicts WHERE project_id=?", (project_id,))
    conn.commit()

    for did in destroy_dicts:
        ops.destroyDict(did)

    shutil.rmtree(os.path.join(siteconfig["dataDir"], "projects/" + project_id))
    return {"success": True, "projectID": project_id}


def createBatch(projectID, stage, batch_size, max_batches, user_email):
    if getProjectStageState(projectID, stage) != []:
        return {"success": False, "projectID": projectID, "msg": 'Processing previous batch creating'}

    # Source dict ID for cases when its used for creating batches
    # e.g. images_new_batches: $(SOURCE_DICT)
    db = ops.getMainDB()
    c = db.execute("SELECT src_dic_id FROM projects WHERE id=?", (projectID,))
    r = c.fetchone()
    src_dict = r['src_dic_id']
    db.close()

    workflow_dir = os.path.join(siteconfig['dataDir'], 'projects', projectID)
    stage_path = os.path.join(siteconfig["dataDir"], 'projects', projectID , stage)
    filemask = os.path.join(stage_path, '*.in')
    logfile = stage_path + ".log"

    logfile_f = open(logfile, "a")

    cmds = ';'.join(['echo "_LOCK_BATCH_CREATE"',
                     'make %s_new_batches --silent SOURCE_DICT=%s.nvh BATCH_SIZE=%s MAX_BATCHES=%s USER="\\"%s\\"" GENERATED_BATCHES_FILEMASK="\\"%s\\""' % (shlex.quote(stage), src_dict, shlex.quote(batch_size),
                                                                                                                                                             shlex.quote(max_batches), user_email, filemask),
                     'git add -A %s' % stage,
                     'git commit -m "New batches %s"' % stage,
                     'echo "_UNLOCK_BATCH_CREATE"'])

    subprocess.Popen(cmds, stdout=logfile_f, stderr=logfile_f, start_new_session=True, close_fds=True, shell=True, cwd=workflow_dir)

    return {"success": True, "projectID": projectID, "msg": 'Creating batches'}


def makeStage(project_id, stage, user_email):
    project_info = getProject(project_id)
    main_db = ops.getMainDB()

    workflow_dir = os.path.join(siteconfig['dataDir'], 'projects', project_id)
    stage_path = os.path.join(siteconfig["dataDir"], 'projects', project_id , stage)
    filemask = os.path.join(stage_path, '*.nvh')
    
    # DELETE previous stage version
    dict_id = ops.suggestDictId()
    for s in project_info['workflow']:
        if s['stage'] == stage and s['outputDict']['dictID']:
            ops.destroyDict(s['outputDict']['dictID']) # will import into fresh dict
            main_db.execute("DELETE FROM project_dicts WHERE dict_id=?", (s['outputDict']['dictID'],))
            main_db.commit()
            dict_id = s['outputDict']['dictID'] # use old dictID if already existed

    dbpath = os.path.join(siteconfig["dataDir"], "dicts/"+dict_id+".sqlite")

    # ==================
    # Init new stage dict
    # ==================
    dictDB = ops.initDict(dict_id, f'{stage} output', project_info['language'], "", user_email)
    dict_config = {"limits": {"entries": 1000000000}} # TODO suggest size

    ops.registerDict(dictDB, dict_id, user_email, dict_config)
    ops.attachDict(dict_id, {})
    dictDB.close()

    # ==================
    # Add new dict to project
    # ==================
    main_db.execute("INSERT INTO project_dicts (project_id, dict_id, source_nvh, stage, created) VALUES (?,?,?,?,?)",
                    (project_id, dict_id, os.path.join(workflow_dir, stage + '.nvh'), f'{stage}_stage', datetime.datetime.utcnow()))
    main_db.commit()
    main_db.close()

    # ==================
    # Run workflow
    # ==================
    logfile = stage_path + ".log"
    logfile_f = open(logfile, "a")
    for p in project_info['workflow']:
        if p['stage'] == stage:
            stage_type = p['type']

    if os.path.exists(workflow_dir + '/' + shlex.quote(stage) + '.nvh'):
        os.remove(workflow_dir + '/' + shlex.quote(stage) + '.nvh')

    if stage_type == 'merge': # The ACCEPTED_BATCHES variable is not used and cause problem in dependencies
        cmds = ';'.join(['echo "_LOCK_STAGE"',
                         'echo "INFO merge stage"',
                         'make %s.nvh --silent SOURCE_DICT=%s.nvh DICT_DB=%s USER="\\"%s\\""' % (shlex.quote(stage), project_info["source_dict"],
                                                                                                 dbpath, user_email),
                         'git add -A %s*' % stage,
                         'git commit -m "Stage %s" -q' % stage,
                         '%s/refresh_project_state.py %s %s' % (currdir, project_id, dict_id),
                         'echo "_UNLOCK_STAGE"'])

        subprocess.Popen(cmds, stdout=logfile_f, stderr=logfile_f, start_new_session=True, close_fds=True, shell=True, cwd=workflow_dir)

    else:
        cmds = ';'.join(['echo "_LOCK_STAGE"',
                         'echo "INFO not merge stage"',
                         'make %s.nvh --silent SOURCE_DICT=%s.nvh ACCEPTED_BATCHES="%s" DICT_DB=%s USER="%s"' % (shlex.quote(stage), project_info["source_dict"],
                                                                                                                 filemask, dbpath, user_email),
                         'git add -A %s*' % stage,
                         'git commit -m "Stage %s" -q' % stage,
                         '%s/refresh_project_state.py %s %s' % (currdir, project_id, dict_id),
                         'echo "_UNLOCK_STAGE"'])

        subprocess.Popen(cmds, stdout=logfile_f, stderr=logfile_f, start_new_session=True, close_fds=True, shell=True, cwd=workflow_dir)

    return {"success": True, "projectID": project_id, "upload_file_path": logfile,
            "msg": 'Creating stage dict'}


def assignProjectDict(projectID, assignees): # TODO store channges to hystory?
    mainDB = ops.getMainDB()
    for dictID, user_email in assignees: # TODO can batch has more than one assignee?
        user_credentials = {user_email: {'canView': 1, 'canEdit': 1, 'canAdd': 0, 'canDelete': 0,
                                         'canEditSource': 0, 'canConfig': 0, 'canDownload': 0, 'canUpload': 0}}
        old_users = ops.updateDictAccess(dictID, user_credentials)
        ops.notifyUsers(old_users, user_credentials, {'title': dictID}, dictID)

        mainDB.execute("UPDATE project_dicts SET assignee=? WHERE project_id=? AND dict_id=?", (user_email, projectID, dictID))
        mainDB.commit()

    mainDB.close()
    return {"success": True, "projectID": projectID,}


def acceptBatch(project_id, dictID_list):
    accepted_dicts = []
    error_dicts = []
    all_stages = set()

    mainDB = ops.getMainDB()
    def can_accept_from_rejected(d_created, d_stage):
        conn = mainDB.execute('SELECT COUNT(DISTINCT dict_id) AS total FROM project_dicts WHERE project_id=? AND created>? AND stage=?', (project_id, d_created, d_stage))
        if int(conn.fetchone()['total']) > 0:
            return False
        return True

    for dictID in dictID_list:
        # remove batch form assignee
        ops.updateDictAccess(dictID, {})

        # get output filename
        c = mainDB.execute('SELECT source_nvh, stage, created FROM project_dicts WHERE project_id=? AND dict_id=?', (project_id, dictID))
        r = c.fetchone()
        if r['source_nvh'].endswith('.in'):
            out_nvh_file_name = r['source_nvh'].rstrip('.in') + '.nvh'
            mainDB.execute('UPDATE project_dicts SET status=? WHERE project_id=? AND dict_id=?', ('accepted', project_id, dictID))
            accepted_dicts.append(dictID)
        elif r['source_nvh'].endswith('.rejected'):
            if can_accept_from_rejected(r['created'], r['stage']):
                out_nvh_file_name = r['source_nvh'].rstrip('.rejected') + '.nvh'
                shutil.move(r['source_nvh'], r['source_nvh'].rstrip('.rejected') + '.in')
                mainDB.execute('UPDATE project_dicts SET status=?, source_nvh=? WHERE project_id=? AND dict_id=?',
                               ('accepted', r['source_nvh'].rstrip('.rejected') + '.in', project_id, dictID))
                accepted_dicts.append(dictID)
                all_stages.add(r['stage'])
            else:
                error_dicts.append(dictID)
                continue

        mainDB.commit()

        with open(out_nvh_file_name, 'w') as out_f:
            dictDB = ops.getDB(dictID)
            for line in ops.download(dictDB, dictID, 'nvh'):
                out_f.write(line)

        project_git_commit(os.path.join(siteconfig["dataDir"], "projects", project_id), f'Accepted batch {dictID}', r['stage'])

    mainDB.close()
    refresh_selected_stages(project_id, all_stages)

    if error_dicts:
        return {"success": False, "projectID": project_id, 'accepted_dicts': accepted_dicts, 'error_dicts': error_dicts, 'msg': "Rejected batches can't be re-accepted after new batches are created."}
    else:
        return {"success": True, "projectID": project_id, 'accepted_dicts': accepted_dicts}


def deleteBatch(project_id, dictID_list):
    all_stages = set()
    mainDB = ops.getMainDB()

    for dictID in dictID_list:
        # remove batch form assignee
        ops.updateDictAccess(dictID, {})

        # get output filename
        c = mainDB.execute('SELECT source_nvh, stage FROM project_dicts WHERE project_id=? AND dict_id=?', (project_id, dictID))
        r = c.fetchone()
        all_stages.add(r['stage'])

        if os.path.isfile(r['source_nvh'].rstrip('.in') + '.nvh'):
            os.remove(r['source_nvh'].rstrip('.in') + '.nvh')

        if os.path.isfile(r['source_nvh']):
            os.remove(r['source_nvh'])

        if os.path.isfile(r['source_nvh'] + '.schema'):
            os.remove(r['source_nvh'] + '.schema')

        # DELETE batch form project
        mainDB.execute('DELETE FROM project_dicts WHERE project_id=? AND dict_id=?', (project_id, dictID))
        mainDB.commit()

    mainDB.close()

    # DELETE batch dict from lexonomy
    for dictID in dictID_list:
        ops.destroyDict(dictID)

    refresh_selected_stages(project_id, all_stages)
    return {"success": True, "projectID": project_id}


def rejectBatch(project_id, dictID_list):
    all_stages = set()
    mainDB = ops.getMainDB()

    for dictID in dictID_list:
        # remove batch form assignee
        ops.updateDictAccess(dictID, {})

        # get output filename
        c = mainDB.execute('SELECT source_nvh, stage FROM project_dicts WHERE project_id=? AND dict_id=?', (project_id, dictID))
        r = c.fetchone()
        all_stages.add(r['stage'])

        # rm exported NVH if was created by accept
        if os.path.isfile(r['source_nvh'].rstrip('.in') + '.nvh'):
            os.remove(r['source_nvh'].rstrip('.in') + '.nvh')

        # move batch to rejected
        if r['source_nvh'].endswith('.in'):
            rejected_file = r['source_nvh'].rstrip('.in') + '.rejected'
            shutil.move(r['source_nvh'], rejected_file)
            mainDB.execute('UPDATE project_dicts SET status=?, source_nvh=? WHERE project_id=? AND dict_id=?', ('rejected', rejected_file, project_id, dictID))

        mainDB.commit()
        project_git_commit(os.path.join(siteconfig["dataDir"], "projects", project_id), f'Rejected batch {dictID}', r['stage'])

    mainDB.close()
    refresh_selected_stages(project_id, all_stages)
    return {"success": True, "projectID": project_id}


def getWokflows():
    workflows = {}
    conn = ops.getMainDB()
    c = conn.execute("SELECT id, name, description FROM workflows ORDER BY name")

    for r in c.fetchall():
        make_data, tl_node = getMakeDeps(os.path.join(currdir, "workflows", r["id"], "Makefile"))
        workflows[r["id"]] = {"workflow_id": r["id"], "name": r["name"], "description": r["description"], 'stages': make_data, 'tl_node': tl_node}

    total = len(workflows)
    return {"workflows": workflows, "total": total, "success": True}