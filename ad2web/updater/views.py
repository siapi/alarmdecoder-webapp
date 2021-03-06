# -*- coding: utf-8 -*-

import os
import json

from flask import Blueprint, render_template, abort, g, request, flash, Response, redirect, url_for
from flask import current_app as APP
from flask.ext.login import login_required, current_user

from werkzeug import secure_filename

from ..extensions import db
from ..decorators import admin_required

from .forms import UpdateFirmwareForm
from .models import FirmwareUpdater

updater = Blueprint('update', __name__, url_prefix='/update')

@updater.context_processor
def keypad_context_processor():
    return { }

@updater.route('/')
@login_required
@admin_required
def index():
    return render_template('updater/index.html', updates=APP.decoder.updates)

@updater.route('/update', methods=['POST'])
@login_required
@admin_required
def update():
    ret = { 'status': 'FAIL' }

    component = request.json.get('component', None)
    if component is not None:
        ret = APP.decoder.updater.update(component)

    return json.dumps(ret);

@updater.route('/restart', methods=['POST'])
@login_required
@admin_required
def restart():
    APP.decoder.trigger_restart = True

    return json.dumps({ 'status': 'PASS' })

@updater.route('/checkavailable', methods=['GET'])
def checkavailable():
    return json.dumps({ 'status': 'PASS' })

@updater.route('/check_for_updates', methods=['GET'])
@login_required
@admin_required
def check_for_updates():
    APP.decoder.updates = APP.decoder.updater.check_updates()
    update_available = not all(not needs_update for component, (needs_update, branch, revision, new_revision, status, project_url) in APP.decoder.updates.iteritems())
    APP.jinja_env.globals['update_available'] = update_available

    return redirect(url_for('update.index'))

@updater.route('/firmware', methods=['GET', 'POST'])
@login_required
@admin_required
def firmware():
    form = UpdateFirmwareForm()
    form.multipart = True
    if form.validate_on_submit():
        uploaded_file = request.files[form.firmware_file.name]
        data = uploaded_file.read()
        file_path = os.path.join('/tmp', secure_filename(uploaded_file.filename))
        open(file_path, 'w').write(data)

        APP.decoder.firmware_file = file_path
        APP.decoder.firmware_length = len(filter(lambda x: x[0] == ':', data))

        return render_template('updater/firmware_upload.html')

    return render_template('updater/firmware.html', form=form)
