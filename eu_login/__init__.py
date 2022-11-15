# ===================================================================================
# Copyright (C) 2019 Fraunhofer Gesellschaft. All rights reserved.
# ===================================================================================
# This Graphene software file is distributed by Fraunhofer Gesellschaft
# under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# This file is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============LICENSE_END==========================================================
from flask import session, request, render_template, redirect, url_for
from cas import CASClient
from app import app
import logging
from binascii import hexlify

logger = logging.getLogger(__name__)

cas_client = CASClient(
    version=3,
    service_url='https://playground.ki-lab.nrw/oauth/login',
    server_url='https://ecas.ec.europa.eu/cas/path' # the last segment is a dummy and will be replaced by urljoin
)


def render_login():
    return render_template("eu-login.html")


@app.route('/oauth/login')
def login():
    if 'username' in session:
        # Already logged in
        return redirect(url_for("home"))

    next = request.args.get('next')
    ticket = request.args.get('ticket')
    if not ticket:
        # No ticket, the request come from end user, send to CAS login
        cas_login_url = cas_client.get_login_url()
        logger.debug('CAS login URL: %s', cas_login_url)
        return redirect(cas_login_url)

    # There is a ticket, the request come from CAS as callback.
    # need call `verify_ticket()` to validate ticket and get user profile.
    logger.debug('ticket: %s', ticket)
    logger.debug('next: %s', next)

    user, attributes, pgtiou = cas_client.verify_ticket(ticket)

    logger.info(
        'CAS verify ticket response: user: %s, attributes: %s, pgtiou: %s', user, attributes, pgtiou)

    if not user:
        return 'Failed to verify ticket. <a href="/login">Login</a>'
    else:  # Login successfully, redirect according `next` query parameter.
        session['username'] = hexlify(attributes['email'].lower().strip().encode()).decode('utf-8')
        session['userfirstname'] = attributes['firstName']

        return redirect(url_for("home"))



# User logout
@app.route('/logout', methods=["GET"])  # URL for logout
def logout():  # logout function
    session.clear()
    return redirect(url_for("home"))  # redirect to home page with message


