from werkzeug.wrappers import request
from flask import Flask, render_template, jsonify
from flask_restful import Resource, Api, reqparse
from datetime import datetime, timedelta
import mysql.connector

app = Flask(__name__)
api = Api(app)