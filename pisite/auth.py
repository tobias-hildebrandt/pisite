#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 15 16:26:37 2020

@author: tobias
"""

import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from passlib.hash import bcrypt

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        error = None
        user = "" # TODO get user from backend