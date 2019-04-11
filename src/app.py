#!/usr/bin/env python
#-*- coding: utf-8 -*-

import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import yaml
import hashlib
import smtplib

app = Flask(__name__)
application = app

# Load configuration from YAML file
__dir__ = os.path.dirname(__file__)
app.config.update(
	yaml.safe_load(open(os.path.join(__dir__, os.environ.get(
		'FLASK_CONFIG_FILE', 'config.yaml')))))

db = SQLAlchemy(app)

class Request(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(80), nullable=False)
	reason = db.Column(db.Text, nullable=False)
	contact = db.Column(db.String(80), nullable=False)

class Consent(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	request_id = db.Column(db.Integer, db.ForeignKey('request.id'), nullable=False)
	request = db.relationship(Request, backref='consents')
	email = db.Column(db.String(80))

	def verification_string(self):
		return hashlib.md5((self.email + str(self.request_id)).encode('utf-8')).hexdigest()
	
	def grant_link(self):
		return '/consent/%s/%s/%s' % (self.verification_string(), self.request_id, self.email)
	
	def revoke_link(self):
		return '/revoke/%s/%d/%s' % (self.verification_string(), self.request_id, self.email)

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/consent/<verification>/<request_id>/<email>')
def consent(verification, request_id, email):
	c = Consent.query.filter_by(email=email, request_id=request_id).first()
	if not c:
		c = Consent(email=email, request_id=request_id)
		if c.verification_string() == verification:
			db.session.add(c)
			db.session.commit()
			s = smtplib.SMTPS(app.config('SMTP_HOST'))
			s.ehlo()
			mailtext = render_template('consent_granted_email.html', consent=c)
			msg = """From: Wikimedia Ceska republika <info@wikimedia.cz>
To: %s
MIME-Version: 1.0
Content-type: text/html
Subject: [WMČR] Udělení souhlasu se zpracováním osobních údajů bylo úspěšné

%s
			""" % (email, mailtext)
			s.sendmail("info@wikimedia.cz", email, msg)
			return render_template('consent_granted.html', consent=c)
		else:
			return render_template('unsuccessful_verification.html', consent=c)
	else:
		return render_template('already_granted.html', consent=c)

@app.route('/revoke/<verification>/<request_id>/<email>')
def revoke(verification, request_id, email):
	c = Consent.query.filter_by(email=email, request_id=request_id).first()
	if c:
		if c.verification_string() == verification:
			db.session.delete(c)
			db.session.commit()
			return render_template('consent_revoked.html', consent=Consent(email=email, request_id=request_id))
		else:
			return render_template('unsuccessful_verification.html', consent=c)
	else:
		return render_template('already_revoked.html', consent=Consent(email=email, request_id=request_id))

if __name__ == "__main__":
	app.run(debug=True, port=2000)
